from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.engine.adapter import EngineAdapter, run_graph
from app.engine.state import (
    AgentState,
    ModelConfig,
    QueryRequest,
    StreamEvent,
    TaskStatusResponse,
)
from app.task_store import TaskInfo, task_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["engine"])

# Backward compatibility alias for in-memory task dictionary access
tasks = task_store._tasks

# Shared adapter instance
_engine_adapter = EngineAdapter()


async def run_engine_task(task_id: str, query_request: QueryRequest) -> None:
    """
    Background worker that executes the multi-agent workflow via EngineAdapter
    and streams events into the central TaskStore.
    """
    await task_store.update_status(task_id, "running")
    config = query_request.config

    async def _on_event(event_dict: dict[str, Any]) -> None:
        await task_store.add_event(task_id, event_dict)

    try:
        result = await _engine_adapter.execute_task(
            query=query_request.query,
            config=config,
            task_id=task_id,
            session_id=query_request.session_id,
            event_callback=_on_event,
        )
        await task_store.update_status(
            task_id=task_id,
            status=result["status"],
            final_answer=result["final_answer"],
            error=result["error"],
        )
    except asyncio.CancelledError:
        logger.info("Task %s worker received cancellation signal.", task_id)
        # Ensure status reflects cancelled
        await task_store.update_status(
            task_id=task_id,
            status="cancelled",
            error="Task was cancelled by user",
        )
        raise
    except Exception as exc:
        logger.exception("Task %s worker encountered an unhandled error: %s", task_id, exc)
        await task_store.update_status(
            task_id=task_id,
            status="error",
            error=str(exc),
        )
        task = await task_store.get_task(task_id)
        if task and not any(e.get("event") == "workflow_failed" for e in task.history):
            from datetime import datetime, timezone
            now_iso = datetime.now(timezone.utc).isoformat()
            await task_store.add_event(task_id, {
                "event": "workflow_failed",
                "agent": None,
                "data": {"error": str(exc), "message": str(exc)},
                "timestamp": now_iso,
                "task_id": task_id,
            })


@router.post("/engine/run", response_model=dict, status_code=200)
async def engine_run(
    query_request: QueryRequest,
) -> dict[str, str]:
    """
    Submit a user query to begin an asynchronous multi-agent engine execution.
    Spawns background asyncio.Task and returns task_id with queued status immediately.
    """
    task = await task_store.create_task(
        query=query_request.query,
        session_id=query_request.session_id,
        config=query_request.config,
    )
    bg_task = asyncio.create_task(run_engine_task(task.task_id, query_request))
    await task_store.set_asyncio_task(task.task_id, bg_task)
    return {"task_id": task.task_id, "status": "queued"}


@router.get("/engine/status/{task_id}", response_model=TaskStatusResponse)
async def engine_status(task_id: str) -> TaskStatusResponse:
    """
    Poll the current lifecycle state, final answer, error, and event count of a task.
    """
    task = await task_store.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id!r} not found")

    return TaskStatusResponse(
        task_id=task.task_id,
        status=task.status,
        final_answer=task.final_answer,
        error=task.error,
        events_count=len(task.history),
    )


@router.get("/engine/stream/{task_id}")
async def engine_stream(task_id: str) -> EventSourceResponse:
    """
    Server-Sent Events (SSE) streaming endpoint for real-time agent workflow events.
    Guarantees event replay on reconnection and clean termination on terminal events
    ('workflow_completed', 'workflow_failed', 'cancelled').
    """
    task = await task_store.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id!r} not found")

    return EventSourceResponse(task_store.subscribe(task_id))


@router.get("/engine/tasks", response_model=list[dict])
async def list_engine_tasks(limit: int = 50) -> list[dict[str, Any]]:
    """
    List all tracked engine tasks with their status and metadata.
    """
    return await task_store.list_tasks(limit=limit)


@router.delete("/engine/cancel/{task_id}", response_model=dict)
async def cancel_engine_task(task_id: str) -> dict[str, str]:
    """
    Cancel an active or queued engine task.
    """
    task = await task_store.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id!r} not found")

    cancelled = await task_store.cancel_task(task_id)
    return {
        "task_id": task_id,
        "status": "cancelled" if cancelled else task.status,
    }
