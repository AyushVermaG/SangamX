"""
Unit tests for TaskStore (app/task_store.py).

Verifies:
- Task registration, lookup, and listing
- Concurrency-safe status transitions
- Event history recording and real-time distribution
- Subscriber lifecycle (live pub/sub + historical replay on reconnect)
- Reconnection to already-terminal tasks without hanging
- Task cancellation mechanics and worker cancellation
- Terminal events: workflow_completed, workflow_failed, cancelled
- TTL-based expiration and cleanup
"""
from __future__ import annotations

import asyncio
import json
import time

import pytest

from app.task_store import TaskStore


@pytest.fixture
def store():
    return TaskStore(default_ttl_seconds=3600.0)


async def test_create_and_get_task(store):
    """Creating a task registers it with 'queued' status."""
    task = await store.create_task(query="Sample query", session_id="sess-1")
    assert task.task_id is not None
    assert task.status == "queued"
    assert task.query == "Sample query"
    assert task.session_id == "sess-1"

    retrieved = await store.get_task(task.task_id)
    assert retrieved is not None
    assert retrieved.task_id == task.task_id


async def test_list_tasks(store):
    """Listing tasks returns recent task summaries sorted newest first."""
    t1 = await store.create_task(query="Query 1", task_id="t1")
    await asyncio.sleep(0.02)
    t2 = await store.create_task(query="Query 2", task_id="t2")

    tasks = await store.list_tasks(limit=10)
    assert len(tasks) >= 2
    task_ids = [t["task_id"] for t in tasks]
    assert "t1" in task_ids
    assert "t2" in task_ids
    assert task_ids.index("t2") < task_ids.index("t1")  # t2 created after t1


async def test_update_status(store):
    """Status updates update timestamp and result attributes."""
    task = await store.create_task(query="Test")
    updated = await store.update_status(
        task.task_id,
        status="done",
        final_answer="Answer text",
    )
    assert updated.status == "done"
    assert updated.final_answer == "Answer text"


async def test_event_history_and_live_subscription(store):
    """Subscribers receive historical events followed by live events concluding on workflow_completed."""
    task = await store.create_task(query="Streaming test", task_id="stream-1")

    # Add historical event before subscriber joins
    await store.add_event(task.task_id, {"event": "agent_start", "agent": "planner", "data": {}})

    received = []

    async def consume():
        async for frame in store.subscribe(task.task_id):
            received.append(frame)

    consumer = asyncio.create_task(consume())

    # Give consumer a moment to start
    await asyncio.sleep(0.01)

    # Add live events
    await store.add_event(task.task_id, {"event": "final_answer", "agent": "synthesizer", "data": {"content": "42"}})
    await store.add_event(task.task_id, {"event": "workflow_completed", "agent": None, "data": {"final_answer": "42"}})

    await asyncio.wait_for(consumer, timeout=2.0)

    events_received = [json.loads(f["data"]) for f in received]
    event_names = [f["event"] for f in received]

    assert event_names == ["agent_start", "final_answer", "workflow_completed"]
    assert events_received[1]["content"] == "42"
    assert events_received[2]["final_answer"] == "42"


async def test_reconnection_to_completed_task(store):
    """Connecting to an already completed task immediately replays history and exits cleanly."""
    task = await store.create_task(query="Reconnection test", task_id="reconnect-1")
    await store.add_event(task.task_id, {"event": "agent_start", "agent": "planner", "data": {}})
    await store.add_event(task.task_id, {"event": "final_answer", "agent": "synthesizer", "data": {"content": "Final"}})
    await store.add_event(task.task_id, {"event": "workflow_completed", "agent": None, "data": {"final_answer": "Final"}})
    await store.update_status(task.task_id, "done", final_answer="Final")

    # Client connects AFTER task is already done
    frames = []
    async for frame in store.subscribe(task.task_id):
        frames.append(frame)

    assert len(frames) == 3
    assert [f["event"] for f in frames] == ["agent_start", "final_answer", "workflow_completed"]


async def test_cancel_task(store):
    """Cancelling a running task marks it cancelled and emits a cancelled event."""
    task = await store.create_task(query="Cancel test", task_id="cancel-1")
    await store.update_status(task.task_id, "running")

    # Attach a dummy background asyncio task
    async def dummy_work():
        await asyncio.sleep(10)

    bg_task = asyncio.create_task(dummy_work())
    await store.set_asyncio_task(task.task_id, bg_task)

    cancelled = await store.cancel_task(task.task_id)
    assert cancelled is True

    updated = await store.get_task(task.task_id)
    assert updated.status == "cancelled"
    assert bg_task.cancelled() or bg_task.cancelling()

    # Verify cancel event was recorded in history, and neither workflow_completed nor done was emitted
    event_names = [e["event"] for e in updated.history]
    assert "cancelled" in event_names
    assert "workflow_completed" not in event_names
    assert "done" not in event_names


async def test_cancel_task_exactly_once(store):
    """Calling cancel_task repeatedly only cancels once and emits a single cancelled event."""
    task = await store.create_task(query="Cancel duplicate test", task_id="cancel-dup-1")
    await store.update_status(task.task_id, "running")

    first_cancel = await store.cancel_task(task.task_id)
    assert first_cancel is True

    second_cancel = await store.cancel_task(task.task_id)
    assert second_cancel is False

    updated = await store.get_task(task.task_id)
    assert updated.status == "cancelled"

    cancel_events = [e for e in updated.history if e.get("event") == "cancelled"]
    assert len(cancel_events) == 1


async def test_ttl_cleanup(store):
    """Terminal tasks older than TTL are purged; active or recent tasks are retained."""
    t_old = await store.create_task(query="Old task", task_id="old-1")
    await store.update_status(t_old.task_id, "done")
    # Manually backdate updated_at
    t_old.updated_at = time.time() - 4000.0

    t_recent = await store.create_task(query="Recent task", task_id="recent-1")
    await store.update_status(t_recent.task_id, "done")

    t_running = await store.create_task(query="Running task", task_id="running-1")
    await store.update_status(t_running.task_id, "running")
    t_running.updated_at = time.time() - 4000.0  # Even if old, running task is NOT purged

    purged = await store.cleanup_expired_tasks(ttl_seconds=3600.0)
    assert purged == 1

    assert await store.get_task("old-1") is None
    assert await store.get_task("recent-1") is not None
    assert await store.get_task("running-1") is not None
