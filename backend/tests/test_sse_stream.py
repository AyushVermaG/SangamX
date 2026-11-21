"""
Tests for Server-Sent Events (SSE) streaming compatibility and formatting.

Verifies:
- Compliance with frontend EventSource contract (event names, JSON payloads)
- Content extraction and field availability (both top-level and in 'data' object)
- Clean termination on 'workflow_completed', 'workflow_failed', and 'cancelled'
- History replay upon reconnection
- Multiple concurrent listeners receiving identical frames
"""
from __future__ import annotations

import asyncio
import json

import pytest

from app.task_store import TaskStore


@pytest.fixture
def store():
    return TaskStore()


async def test_sse_event_names_and_payload_structure(store):
    """
    SSE frames must preserve the required event names and format payload
    so that frontend engineApi.js and AgentTrace.jsx can parse them cleanly.
    """
    task = await store.create_task(query="SSE format test", task_id="sse-fmt-1")

    test_events = [
        {"event": "agent_start", "agent": "planner", "data": {"message": "Decomposing query"}},
        {"event": "agent_done", "agent": "planner", "data": {"approach": "stepwise"}},
        {"event": "revision_start", "agent": None, "data": {"reason": "Contradiction detected", "round": 1}},
        {"event": "disagreement", "agent": "critic", "data": {"confidence": 0.85, "reason": "Conflict"}},
        {"event": "final_answer", "agent": "synthesizer", "data": {"content": "Final synthesized result", "preview": "Final"}},
        {"event": "workflow_completed", "agent": None, "data": {"final_answer": "Final synthesized result"}},
    ]

    for evt in test_events:
        await store.add_event(task.task_id, evt)

    await store.update_status(task.task_id, "done", final_answer="Final synthesized result")

    frames = []
    async for frame in store.subscribe(task.task_id):
        frames.append(frame)

    assert len(frames) == len(test_events)

    for i, frame in enumerate(frames):
        assert frame["event"] == test_events[i]["event"]
        parsed_data = json.loads(frame["data"])

        # Top level attributes expected by frontend
        assert "task_id" in parsed_data
        assert "timestamp" in parsed_data
        assert parsed_data["agent"] == test_events[i]["agent"]

        # Inner data object preserved
        assert isinstance(parsed_data["data"], dict)

        # For final_answer, content must be accessible
        if frame["event"] == "final_answer":
            assert parsed_data["content"] == "Final synthesized result"
            assert parsed_data["data"]["content"] == "Final synthesized result"
        elif frame["event"] == "workflow_completed":
            assert parsed_data["final_answer"] == "Final synthesized result"


async def test_sse_failure_event_delivery(store):
    """Failure terminal event workflow_failed is delivered and terminates the stream."""
    task = await store.create_task(query="SSE failure test", task_id="sse-fail-1")
    await store.add_event(task.task_id, {"event": "agent_start", "agent": "planner", "data": {}})
    await store.add_event(task.task_id, {"event": "error", "agent": "planner", "data": {"message": "Model timeout"}})
    await store.add_event(task.task_id, {"event": "workflow_failed", "agent": None, "data": {"error": "Model timeout"}})
    await store.update_status(task.task_id, "error", error="Model timeout")

    frames = []
    async for frame in store.subscribe(task.task_id):
        frames.append(frame)

    assert len(frames) == 3
    assert [f["event"] for f in frames] == ["agent_start", "error", "workflow_failed"]
    parsed_last = json.loads(frames[-1]["data"])
    assert parsed_last["error"] == "Model timeout"


async def test_sse_concurrent_listeners(store):
    """Multiple concurrent SSE listeners to the same task receive the identical sequence."""
    task = await store.create_task(query="Multi-listener test", task_id="multi-1")

    client1_frames = []
    client2_frames = []

    async def client1():
        async for f in store.subscribe(task.task_id):
            client1_frames.append(f["event"])

    async def client2():
        async for f in store.subscribe(task.task_id):
            client2_frames.append(f["event"])

    t1 = asyncio.create_task(client1())
    t2 = asyncio.create_task(client2())
    await asyncio.sleep(0.01)

    await store.add_event(task.task_id, {"event": "agent_start", "agent": "researcher", "data": {}})
    await store.add_event(task.task_id, {"event": "agent_done", "agent": "researcher", "data": {}})
    await store.add_event(task.task_id, {"event": "workflow_completed", "agent": None, "data": {}})

    await asyncio.gather(t1, t2)

    assert client1_frames == ["agent_start", "agent_done", "workflow_completed"]
    assert client2_frames == ["agent_start", "agent_done", "workflow_completed"]


async def test_sse_cancelled_event_delivery(store):
    """Cancelled task delivers 'cancelled' event over SSE and terminates stream cleanly."""
    task = await store.create_task(query="SSE cancel test", task_id="sse-cancel-1")
    await store.add_event(task.task_id, {"event": "agent_start", "agent": "planner", "data": {}})

    received = []

    async def consume():
        async for frame in store.subscribe(task.task_id):
            received.append(frame)

    consumer = asyncio.create_task(consume())
    await asyncio.sleep(0.01)

    # Trigger cancellation via store
    await store.cancel_task(task.task_id)

    await asyncio.wait_for(consumer, timeout=2.0)

    event_names = [f["event"] for f in received]
    assert event_names == ["agent_start", "cancelled"]
    assert "workflow_completed" not in event_names
    assert "workflow_failed" not in event_names
    assert "done" not in event_names

    parsed_cancel = json.loads(received[-1]["data"])
    assert parsed_cancel["event"] == "cancelled"
    assert parsed_cancel["task_id"] == "sse-cancel-1"
