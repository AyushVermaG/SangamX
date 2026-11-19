from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.engine.state import (
    ModelConfig,
    QueryRequest,
    TaskStatusResponse,
    StreamEvent,
    AgentState,
)
from app.engine.graph import run_graph

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["engine"])

# In-memory task store: task_id -> task dict
tasks: dict[str, dict] = {}


async def run_engine_task(task_id: str, query_request: QueryRequest) -> None:
    """Background coroutine that drives the agent graph and feeds events into the queue."""
    task = tasks[task_id]
    task["status"] = "running"
    queue: asyncio.Queue = task["events"]

    config = query_request.config or ModelConfig()
    initial_state: AgentState = {
        "query": query_request.query,
        "session_id": query_request.session_id,
        "plan": None,
        "research_out": None,
        "analyst_out": None,
        "critic_verdict": None,
        "revision_count": 0,
        "final_answer": None,
        "streaming_log": [],
        "error": None,
    }

    try:
        final_state = await run_graph(initial_state, queue, config)
        task["status"] = "done"
        task["final_answer"] = final_state.get("final_answer")
        task["error"] = final_state.get("error")
    except Exception as exc:
        logger.exception("Engine task %s failed: %s", task_id, exc)
        task["status"] = "error"
        task["error"] = str(exc)
        await queue.put({"event": "error", "data": {"message": str(exc)}})
    finally:
        # Signal SSE stream to close
        await queue.put({"event": "done", "data": {}})


@router.post("/engine/run", response_model=dict, status_code=202)
async def engine_run(
    query_request: QueryRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "task_id": task_id,
        "status": "queued",
        "final_answer": None,
        "error": None,
        "events": asyncio.Queue(),
    }
    background_tasks.add_task(run_engine_task, task_id, query_request)
    return {"task_id": task_id, "status": "queued"}


@router.get("/engine/status/{task_id}", response_model=TaskStatusResponse)
async def engine_status(task_id: str) -> TaskStatusResponse:
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id!r} not found")
    queue: asyncio.Queue = task["events"]
    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        final_answer=task.get("final_answer"),
        error=task.get("error"),
        events_count=queue.qsize(),
    )


@router.get("/engine/stream/{task_id}")
async def engine_stream(task_id: str) -> EventSourceResponse:
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id!r} not found")

    queue: asyncio.Queue = task["events"]

    async def event_generator() -> AsyncGenerator[dict, None]:
        while True:
            event_dict = await queue.get()
            event_name = event_dict.get("event", "message")
            data_payload = event_dict.get("data", {})
            yield {
                "event": event_name,
                "data": json.dumps(data_payload),
            }
            if event_name in ("done", "error"):
                break

    return EventSourceResponse(event_generator())
