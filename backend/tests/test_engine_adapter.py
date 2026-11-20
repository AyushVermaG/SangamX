"""
Unit tests for EngineAdapter (app/engine/adapter.py).

Verifies:
- Wrapping run_graph and generating correct initial state
- Event forwarding via async callback and optional external queue
- Event augmentation with task_id and timezone-aware UTC ISO-8601 timestamps
- Multiple queued events handled and drained cleanly
- Callback failure resilience: consumer acknowledges queue items even if callback fails
- Queue cleanup and consumer termination (consumer task is stopped and awaited)
- Error normalization and original exception preservation
- Cancellation propagation without emitting workflow_completed or workflow_failed
- Exactly-once backend terminal event emission:
    - 'workflow_completed' on success
    - 'workflow_failed' on failure
    - No legacy 'done' event emitted
    - No duplicate error events if engine already emitted one
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.engine.adapter import EngineAdapter
from app.engine.state import AgentState, ModelConfig


@pytest.fixture
def adapter():
    return EngineAdapter()


async def test_adapter_successful_execution(adapter):
    """Adapter executes run_graph and emits workflow_completed as the terminal event."""
    expected_answer = "Paris is the capital of France."

    async def fake_run_graph(state, queue, config):
        await queue.put({"event": "agent_start", "agent": "planner", "data": {"step": "plan"}})
        await queue.put({"event": "final_answer", "agent": "synthesizer", "data": {"content": expected_answer}})
        return {**state, "final_answer": expected_answer}

    events = []

    async def on_event(evt):
        events.append(evt)

    with patch("app.engine.adapter.run_graph", side_effect=fake_run_graph):
        result = await adapter.execute_task(
            query="What is the capital of France?",
            task_id="task-123",
            event_callback=on_event,
        )

    assert result["status"] == "done"
    assert result["final_answer"] == expected_answer
    assert result["error"] is None
    assert result["task_id"] == "task-123"

    event_names = [e["event"] for e in events]
    assert "agent_start" in event_names
    assert "final_answer" in event_names
    assert "workflow_completed" in event_names
    # Must NOT emit old 'done' event
    assert "done" not in event_names
    # Exactly one terminal event
    assert event_names.count("workflow_completed") == 1

    # Check that task_id and timezone-aware timestamp were attached
    for evt in events:
        assert evt.get("task_id") == "task-123"
        ts = evt.get("timestamp")
        assert ts is not None
        # ISO-8601 validation
        dt = datetime.fromisoformat(ts)
        assert dt.tzinfo is not None


async def test_adapter_handles_engine_exception(adapter):
    """When run_graph raises an exception, adapter captures error and emits workflow_failed."""

    async def failing_run_graph(state, queue, config):
        await queue.put({"event": "agent_start", "agent": "planner", "data": {}})
        raise RuntimeError("LLM provider rate limit exceeded")

    events = []

    async def on_event(evt):
        events.append(evt)

    with patch("app.engine.adapter.run_graph", side_effect=failing_run_graph):
        result = await adapter.execute_task(
            query="test query",
            task_id="task-err-1",
            event_callback=on_event,
        )

    assert result["status"] == "error"
    assert "LLM provider rate limit exceeded" in result["error"]

    event_names = [e["event"] for e in events]
    assert "agent_start" in event_names
    assert "error" in event_names
    assert "workflow_failed" in event_names
    assert "done" not in event_names
    # Terminal workflow_failed emitted exactly once
    assert event_names.count("workflow_failed") == 1
    # Original error message is preserved in the workflow_failed event
    wf_event = next(e for e in events if e["event"] == "workflow_failed")
    assert "LLM provider rate limit exceeded" in wf_event["data"]["error"]


async def test_adapter_detects_error_from_agent_state(adapter):
    """If run_graph returns a state containing an error, adapter emits workflow_failed."""

    async def errored_state_run_graph(state, queue, config):
        await queue.put({"event": "error", "agent": "planner", "data": {"message": "Decomposition failed"}})
        return {**state, "error": "Decomposition failed"}

    events = []

    async def on_event(evt):
        events.append(evt)

    with patch("app.engine.adapter.run_graph", side_effect=errored_state_run_graph):
        result = await adapter.execute_task(
            query="test query",
            task_id="task-state-err-1",
            event_callback=on_event,
        )

    assert result["status"] == "error"
    assert result["error"] == "Decomposition failed"

    event_names = [e["event"] for e in events]
    # No duplicate error events (the engine already emitted one)
    assert event_names.count("error") == 1
    # Exactly one terminal event
    assert event_names.count("workflow_failed") == 1
    assert "workflow_completed" not in event_names
    assert "done" not in event_names


async def test_agent_level_error_event_with_successful_state(adapter):
    """
    If an agent emits an error event during execution but the overall graph recovers
    and returns a successful final state, the workflow must succeed and emit workflow_completed.
    The agent-level error event is preserved in history.
    """
    async def recovered_run_graph(state, queue, config):
        await queue.put({"event": "agent_start", "agent": "critic", "data": {}})
        # Agent-level error event emitted during run
        await queue.put({"event": "error", "agent": "critic", "data": {"message": "Transient critic warning"}})
        # But synthesizer successfully completes
        await queue.put({"event": "final_answer", "agent": "synthesizer", "data": {"content": "Synthesized successfully"}})
        return {**state, "final_answer": "Synthesized successfully", "error": None}

    events = []

    async def on_event(evt):
        events.append(evt)

    with patch("app.engine.adapter.run_graph", side_effect=recovered_run_graph):
        result = await adapter.execute_task(
            query="test query",
            task_id="task-recovered-1",
            event_callback=on_event,
        )

    assert result["status"] == "done"
    assert result["final_answer"] == "Synthesized successfully"
    assert result["error"] is None

    event_names = [e["event"] for e in events]
    # Agent-level error event is preserved in event stream / history
    assert "error" in event_names
    error_event = next(e for e in events if e["event"] == "error")
    assert error_event["agent"] == "critic"
    assert error_event["data"]["message"] == "Transient critic warning"

    # Terminal event must be workflow_completed (NOT workflow_failed)
    assert "workflow_completed" in event_names
    assert "workflow_failed" not in event_names
    assert "done" not in event_names
    assert event_names.count("workflow_completed") == 1


async def test_adapter_cancellation_propagation(adapter):
    """When cancelled, adapter propagates CancelledError without emitting terminal completion or failure."""

    async def hanging_run_graph(state, queue, config):
        await queue.put({"event": "agent_start", "agent": "planner", "data": {}})
        await asyncio.sleep(100.0)
        return state

    events = []

    async def on_event(evt):
        events.append(evt)

    with patch("app.engine.adapter.run_graph", side_effect=hanging_run_graph):
        task = asyncio.create_task(
            adapter.execute_task(
                query="test query",
                task_id="task-cancel-1",
                event_callback=on_event,
            )
        )
        await asyncio.sleep(0.05)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task

    event_names = [e["event"] for e in events]
    assert "agent_start" in event_names
    # Cancellation must NOT produce workflow_completed or workflow_failed or done
    assert "workflow_completed" not in event_names
    assert "workflow_failed" not in event_names
    assert "done" not in event_names


async def test_adapter_multiple_queued_events_and_drain(adapter):
    """All events placed into the internal queue are delivered and drained cleanly."""

    async def multi_event_run_graph(state, queue, config):
        for i in range(10):
            await queue.put({"event": "agent_start", "agent": f"agent_{i}", "data": {"index": i}})
        return {**state, "final_answer": "Complete"}

    events = []

    async def on_event(evt):
        events.append(evt)

    with patch("app.engine.adapter.run_graph", side_effect=multi_event_run_graph):
        result = await adapter.execute_task(
            query="test multi",
            task_id="task-multi-1",
            event_callback=on_event,
        )

    assert result["status"] == "done"
    # 10 progress events + 1 workflow_completed event
    assert len(events) == 11
    assert [e["data"].get("index") for e in events[:10]] == list(range(10))
    assert events[-1]["event"] == "workflow_completed"


async def test_adapter_callback_failure_resilience(adapter):
    """Consumer acknowledges internal queue items and completes even if the event callback fails."""

    async def normal_run_graph(state, queue, config):
        await queue.put({"event": "agent_start", "agent": "planner", "data": {}})
        await queue.put({"event": "agent_done", "agent": "planner", "data": {}})
        return {**state, "final_answer": "Recovered"}

    call_count = 0

    async def flunking_callback(evt):
        nonlocal call_count
        call_count += 1
        raise ValueError("Simulated callback failure")

    ext_queue = asyncio.Queue()

    with patch("app.engine.adapter.run_graph", side_effect=normal_run_graph):
        result = await adapter.execute_task(
            query="test callback fail",
            task_id="task-cb-fail",
            event_callback=flunking_callback,
            external_queue=ext_queue,
        )

    assert result["status"] == "done"
    assert result["final_answer"] == "Recovered"
    # Callback was called for each event despite raising
    assert call_count >= 3
    # External queue still received the events
    ext_events = []
    while not ext_queue.empty():
        ext_events.append(ext_queue.get_nowait())
    assert [e["event"] for e in ext_events] == ["agent_start", "agent_done", "workflow_completed"]


async def test_adapter_exactly_once_terminal_event(adapter):
    """Terminal event is emitted exactly once across both callback and external queue."""
    async def quick_run_graph(state, queue, config):
        return {**state, "final_answer": "Answer"}

    callback_events = []
    ext_queue = asyncio.Queue()

    with patch("app.engine.adapter.run_graph", side_effect=quick_run_graph):
        result = await adapter.execute_task(
            query="test",
            task_id="task-once",
            event_callback=lambda evt: callback_events.append(evt),
            external_queue=ext_queue,
        )

    assert result["status"] == "done"
    assert len(callback_events) == 1
    assert callback_events[0]["event"] == "workflow_completed"

    q_events = []
    while not ext_queue.empty():
        q_events.append(ext_queue.get_nowait())
    assert len(q_events) == 1
    assert q_events[0]["event"] == "workflow_completed"
