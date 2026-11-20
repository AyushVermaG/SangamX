"""
Task Store for SangamX
=======================

Concurrency-safe in-memory task management, event pub/sub, and lifecycle storage.

Features:
- Thread/async-safe mutations protected by an asyncio.Lock.
- Full task lifecycle states: "queued" -> "running" -> "done" | "error" | "cancelled".
- Event history recording for deterministic SSE replay upon client reconnection.
- Per-task listener subscriptions supporting multiple concurrent SSE clients.
- Cancellation support with proper background asyncio.Task cleanup.
- Safe TTL-based task cleanup to prevent unbounded memory growth.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Optional

from app.engine.state import ModelConfig

logger = logging.getLogger(__name__)

# Events that conclude a workflow stream
_TERMINAL_EVENTS = frozenset({"workflow_completed", "workflow_failed", "cancelled", "done"})


@dataclass
class TaskInfo:
    """Internal representation of a task."""
    task_id: str
    query: str
    status: str  # "queued" | "running" | "done" | "error" | "cancelled"
    session_id: Optional[str] = None
    config: Optional[ModelConfig] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    final_answer: Optional[str] = None
    error: Optional[str] = None
    history: list[dict[str, Any]] = field(default_factory=list)
    listeners: set[asyncio.Queue] = field(default_factory=set)
    asyncio_task: Optional[asyncio.Task] = None

    def is_terminal(self) -> bool:
        """Return True if the task has concluded execution."""
        return self.status in ("done", "error", "cancelled")


class TaskStore:
    """
    Central in-memory store for SangamX tasks and SSE event distribution.
    """

    def __init__(self, default_ttl_seconds: float = 3600.0):
        self._tasks: dict[str, TaskInfo] = {}
        self._lock = asyncio.Lock()
        self.default_ttl_seconds = default_ttl_seconds

    async def create_task(
        self,
        query: str,
        session_id: Optional[str] = None,
        config: Optional[ModelConfig] = None,
        task_id: Optional[str] = None,
    ) -> TaskInfo:
        """Create and register a new task with status 'queued'."""
        tid = task_id or str(uuid.uuid4())
        task = TaskInfo(
            task_id=tid,
            query=query,
            status="queued",
            session_id=session_id,
            config=config,
            created_at=time.time(),
            updated_at=time.time(),
        )
        async with self._lock:
            self._tasks[tid] = task
        logger.info("Task %s created with status 'queued'", tid)
        return task

    async def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Retrieve task by id, or None if not found."""
        async with self._lock:
            return self._tasks.get(task_id)

    async def list_tasks(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return a summary of recent tasks sorted by creation time (most recent first)."""
        async with self._lock:
            safe_limit = max(0, limit)
            tasks_list = sorted(
                self._tasks.values(),
                key=lambda t: t.created_at,
                reverse=True,
            )[:safe_limit]

            return [
                {
                    "task_id": t.task_id,
                    "query": t.query,
                    "status": t.status,
                    "created_at": t.created_at,
                    "updated_at": t.updated_at,
                    "final_answer": t.final_answer,
                    "error": t.error,
                    "events_count": len(t.history),
                }
                for t in tasks_list
            ]

    async def update_status(
        self,
        task_id: str,
        status: str,
        final_answer: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Optional[TaskInfo]:
        """Update a task's state in a thread-safe manner."""
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            task.status = status
            task.updated_at = time.time()
            if final_answer is not None:
                task.final_answer = final_answer
            if error is not None:
                task.error = error
            return task

    async def set_asyncio_task(self, task_id: str, a_task: asyncio.Task) -> None:
        """Associate the running asyncio.Task with the task record."""
        async with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.asyncio_task = a_task

    async def add_event(self, task_id: str, event_dict: dict[str, Any]) -> None:
        """
        Record an event into the task's history and dispatch it to all active listeners.
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return

            task.history.append(event_dict)
            task.updated_at = time.time()

            # Push to all active listener queues
            for listener_queue in list(task.listeners):
                try:
                    listener_queue.put_nowait(event_dict)
                except Exception as ex:
                    logger.warning("Failed to deliver event to listener for %s: %s", task_id, ex)

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task if it is queued or running.
        Terminates the running asyncio.Task and emits cancellation event.
        Does not emit workflow_completed or workflow_failed.
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return False

            if task.is_terminal():
                return False

            task.status = "cancelled"
            task.error = "Task was cancelled by user"
            task.updated_at = time.time()

            if task.asyncio_task and not task.asyncio_task.done():
                task.asyncio_task.cancel()

        # Emit cancellation event to any connected listeners
        now_iso = datetime.now(timezone.utc).isoformat()
        cancel_event = {
            "event": "cancelled",
            "agent": None,
            "data": {"message": "Task was cancelled by user"},
            "timestamp": now_iso,
            "task_id": task_id,
        }
        await self.add_event(task_id, cancel_event)
        logger.info("Task %s successfully cancelled.", task_id)
        return True

    async def subscribe(
        self,
        task_id: str,
    ) -> AsyncGenerator[dict[str, str], None]:
        """
        Asynchronously subscribe to SSE events for a task.

        Guarantees:
        - Replays existing event history first (safe client reconnect).
        - If task is already completed, delivers history and closes cleanly.
        - Streams new live events as they occur.
        - Closes cleanly when a terminal event ('workflow_completed', 'workflow_failed', 'cancelled') is encountered.
        - Removes listener queue on client disconnection.
        """
        listener_queue: asyncio.Queue = asyncio.Queue()

        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return

            # Snapshot current history under lock
            history_snapshot = list(task.history)
            is_already_terminal = task.is_terminal()

            if not is_already_terminal:
                task.listeners.add(listener_queue)

        def _format_sse_frame(event_dict: dict[str, Any]) -> dict[str, str]:
            event_name = event_dict.get("event", "message")
            data_payload = event_dict.get("data", {})
            if not isinstance(data_payload, dict):
                data_payload = {"value": data_payload}

            merged = {
                "event": event_name,
                "agent": event_dict.get("agent"),
                "timestamp": event_dict.get("timestamp"),
                "task_id": event_dict.get("task_id", task_id),
                "data": data_payload,
                **data_payload,
            }
            return {
                "event": event_name,
                "data": json.dumps(merged),
            }

        try:
            # 1. Replay historical events
            for event_dict in history_snapshot:
                yield _format_sse_frame(event_dict)
                if event_dict.get("event") in _TERMINAL_EVENTS:
                    return

            # If task was already concluded and all historical events were replayed, finish
            if is_already_terminal:
                return

            # 2. Stream live events
            while True:
                event_dict = await listener_queue.get()
                yield _format_sse_frame(event_dict)
                listener_queue.task_done()
                if event_dict.get("event") in _TERMINAL_EVENTS:
                    break

        finally:
            async with self._lock:
                task = self._tasks.get(task_id)
                if task and listener_queue in task.listeners:
                    task.listeners.remove(listener_queue)

    async def cleanup_expired_tasks(self, ttl_seconds: Optional[float] = None) -> int:
        """
        Purge terminal tasks that are older than the specified TTL.
        Returns the number of removed tasks.
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        cutoff = time.time() - ttl
        removed_count = 0

        async with self._lock:
            expired_ids = [
                tid for tid, task in self._tasks.items()
                if task.is_terminal() and task.updated_at < cutoff
            ]
            for tid in expired_ids:
                del self._tasks[tid]
                removed_count += 1

        if removed_count > 0:
            logger.info("Evicted %d expired tasks (TTL: %0.1fs)", removed_count, ttl)
        return removed_count

    async def cancel_all_running(self) -> int:
        """Cancel all running tasks during application shutdown."""
        cancelled = 0
        async with self._lock:
            running_tasks = [t for t in self._tasks.values() if not t.is_terminal()]
        for t in running_tasks:
            await self.cancel_task(t.task_id)
            cancelled += 1
        return cancelled


# Global task store singleton
task_store = TaskStore()
