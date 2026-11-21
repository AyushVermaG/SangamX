from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field, field_validator
from typing_extensions import TypedDict


# ---------------------------------------------------------------------------
# Pydantic models (request / response / shared)
# ---------------------------------------------------------------------------


class ModelConfig(BaseModel):
    """
    Per-request model and provider overrides.

    Provider choices: "gemini" | "groq" | "ollama"
    Model names must match the chosen provider's available models.
    """

    # Planner
    planner_provider: Optional[str] = None
    planner_model: Optional[str] = None
    # Researcher
    researcher_provider: Optional[str] = None
    researcher_model: Optional[str] = None
    # Analyst
    analyst_provider: Optional[str] = None
    analyst_model: Optional[str] = None
    # Critic  — Groq by default (fast, free-tier)
    critic_provider: Optional[str] = None
    critic_model: Optional[str] = None
    # Synthesizer
    synthesizer_provider: Optional[str] = None
    synthesizer_model: Optional[str] = None


class QueryRequest(BaseModel):
    """Incoming request to start an engine run."""

    query: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None
    config: Optional[ModelConfig] = None


class AgentOutput(BaseModel):
    """Structured output from a single agent."""

    agent: str
    content: str
    metadata: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CriticVerdict(BaseModel):
    """Critic's verdict on whether researcher and analyst agree."""

    agree: bool
    reason: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class StreamEvent(BaseModel):
    """An SSE event emitted during the engine run."""

    event: str = Field(
        ...,
        description=(
            "One of: agent_start | agent_done | disagreement | "
            "revision_start | final_answer | error | done"
        ),
    )
    agent: Optional[str] = None
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EngineResponse(BaseModel):
    """Immediate response returned when a run is queued."""

    task_id: str
    status: str
    final_answer: Optional[str] = None


class TaskStatusResponse(BaseModel):
    """Polling response for a task's current state."""

    task_id: str
    status: str = Field(
        ...,
        description="One of: queued | running | done | error",
    )
    final_answer: Optional[str] = None
    error: Optional[str] = None
    events_count: int = 0


# ---------------------------------------------------------------------------
# LangGraph state
# ---------------------------------------------------------------------------


def _replace_last(existing: Any, new: Any) -> Any:
    """Reducer that simply replaces the previous value (last-write-wins)."""
    return new


def _append_events(existing: list, new: list) -> list:
    """Reducer that appends new StreamEvents to the existing list."""
    return existing + new


class AgentState(TypedDict):
    """LangGraph state shared across all nodes."""

    query: str
    session_id: Optional[str]
    plan: Optional[dict]
    # Annotated tells LangGraph which reducer to use for each field
    research_out: Annotated[Optional[AgentOutput], _replace_last]
    analyst_out: Annotated[Optional[AgentOutput], _replace_last]
    critic_verdict: Annotated[Optional[CriticVerdict], _replace_last]
    revision_count: int
    final_answer: Optional[str]
    streaming_log: Annotated[list, _append_events]
    error: Optional[str]
