"""
End-to-end integration tests for FastAPI backend API endpoints.

Tests the full lifecycle:
1. POST /api/v1/engine/run -> 200 {task_id, status: "queued"}
2. GET /api/v1/engine/status/{task_id} -> 200 TaskStatusResponse
3. GET /api/v1/engine/tasks -> 200 list with task included
4. GET /api/v1/engine/stream/{task_id} -> SSE event streaming
5. DELETE /api/v1/engine/cancel/{task_id} -> 200 {task_id, status: "cancelled"}
6. 404s for invalid task IDs
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def test_full_api_workflow(client):
    """Test full cycle: submit query -> check status -> list tasks -> cancel."""
    async def fake_execute_task(**kwargs):
        return {
            "task_id": kwargs.get("task_id"),
            "status": "done",
            "final_answer": "Integration test answer.",
            "error": None,
            "state": None,
        }

    with patch("app.api.v1.engine._engine_adapter.execute_task", side_effect=fake_execute_task):
        res = await client.post(
            "/api/v1/engine/run",
            json={"query": "Explain quantum computing in simple terms."},
        )
        assert res.status_code == 200
        data = res.json()
        assert "task_id" in data
        assert data["status"] == "queued"
        task_id = data["task_id"]

        # Allow background task a brief moment to run
        await asyncio.sleep(0.05)

        # 2. Check status
        res_status = await client.get(f"/api/v1/engine/status/{task_id}")
        assert res_status.status_code == 200
        st_data = res_status.json()
        assert st_data["task_id"] == task_id
        assert st_data["status"] in ("queued", "running", "done")

        # 3. List tasks
        res_list = await client.get("/api/v1/engine/tasks")
        assert res_list.status_code == 200
        tasks = res_list.json()
        assert any(t["task_id"] == task_id for t in tasks)


async def test_cancel_endpoint(client):
    """DELETE /api/v1/engine/cancel/{task_id} cancels an existing running task."""
    async def slow_execute_task(**kwargs):
        await asyncio.sleep(2.0)
        return {"status": "done", "final_answer": "done", "error": None, "state": None}

    with patch("app.api.v1.engine._engine_adapter.execute_task", side_effect=slow_execute_task):
        # Create task
        res = await client.post("/api/v1/engine/run", json={"query": "Cancel me"})
        assert res.status_code == 200
        task_id = res.json()["task_id"]

        # Cancel task while it is still running
        cancel_res = await client.delete(f"/api/v1/engine/cancel/{task_id}")
        assert cancel_res.status_code == 200
        assert cancel_res.json()["status"] == "cancelled"

        # Verify status endpoint reflects cancellation
        st_res = await client.get(f"/api/v1/engine/status/{task_id}")
        assert st_res.status_code == 200
        assert st_res.json()["status"] == "cancelled"


async def test_unknown_task_id_returns_404(client):
    """Non-existent task IDs return 404 across all task endpoints."""
    bad_id = "non-existent-uuid-9999"

    res_status = await client.get(f"/api/v1/engine/status/{bad_id}")
    assert res_status.status_code == 404

    res_cancel = await client.delete(f"/api/v1/engine/cancel/{bad_id}")
    assert res_cancel.status_code == 404

    res_stream = await client.get(f"/api/v1/engine/stream/{bad_id}")
    assert res_stream.status_code == 404


async def test_sse_streaming_integration(client):
    """GET /api/v1/engine/stream/{task_id} streams progress and workflow_completed frames."""
    from app.task_store import task_store
    task = await task_store.create_task(query="SSE integration test")
    await task_store.add_event(task.task_id, {"event": "agent_start", "agent": "planner", "data": {"step": "init"}})
    await task_store.add_event(task.task_id, {"event": "workflow_completed", "agent": None, "data": {"final_answer": "Complete"}})
    await task_store.update_status(task.task_id, "done", final_answer="Complete")

    res = await client.get(f"/api/v1/engine/stream/{task.task_id}")
    assert res.status_code == 200
    assert "text/event-stream" in res.headers.get("content-type", "")
    content = res.text
    assert "event: agent_start" in content
    assert "event: workflow_completed" in content
