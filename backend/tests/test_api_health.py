"""
Tests for FastAPI health and engine API endpoints.
Uses httpx.AsyncClient with ASGITransport.
"""
from __future__ import annotations

import os

import pytest
import pytest_asyncio

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("OPENAI_API_KEY", "test-key")


@pytest.mark.asyncio
async def test_health_endpoint():
    """GET /health should return {"status": "healthy"}."""
    from httpx import ASGITransport, AsyncClient

    from main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_engine_run_validation():
    """POST /api/v1/engine/run with empty query should return 422."""
    from httpx import ASGITransport, AsyncClient

    from main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/engine/run", json={"query": ""})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_engine_run_queued():
    """POST /api/v1/engine/run with valid query should return 200 with task_id."""
    from unittest.mock import AsyncMock, patch

    from httpx import ASGITransport, AsyncClient

    from main import app

    # Patch run_graph so no real LLM calls happen
    with patch("app.api.v1.engine.run_graph", new_callable=AsyncMock) as mock_rg:
        mock_rg.return_value = {"final_answer": "mocked", "streaming_log": [], "error": None}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/engine/run",
                json={"query": "What is the capital of France?"},
            )
    assert resp.status_code == 200
    body = resp.json()
    assert "task_id" in body
    assert body["status"] == "queued"


@pytest.mark.asyncio
async def test_engine_status_not_found():
    """GET /api/v1/engine/status/<nonexistent> should return 404."""
    from httpx import ASGITransport, AsyncClient

    from main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/engine/status/nonexistent-task-id-xyz")
    assert resp.status_code == 404
