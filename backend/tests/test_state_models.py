"""
Tests for Pydantic models defined in app.engine.state.
"""
from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.engine.state import (
    AgentOutput,
    CriticVerdict,
    ModelConfig,
    QueryRequest,
    StreamEvent,
    TaskStatusResponse,
)


# ---------------------------------------------------------------------------
# QueryRequest
# ---------------------------------------------------------------------------


def test_query_request_valid():
    req = QueryRequest(query="What is the capital of France?")
    assert req.query == "What is the capital of France?"
    assert req.session_id is None
    assert req.config is None


def test_query_request_too_long():
    with pytest.raises(ValidationError):
        QueryRequest(query="x" * 4001)


def test_query_request_empty():
    with pytest.raises(ValidationError):
        QueryRequest(query="")


def test_query_request_with_session_id():
    req = QueryRequest(query="Hello", session_id="abc-123")
    assert req.session_id == "abc-123"


# ---------------------------------------------------------------------------
# ModelConfig
# ---------------------------------------------------------------------------


def test_model_config_defaults_are_none():
    cfg = ModelConfig()
    assert cfg.planner_provider is None
    assert cfg.planner_model is None
    assert cfg.researcher_provider is None
    assert cfg.researcher_model is None
    assert cfg.analyst_provider is None
    assert cfg.analyst_model is None
    assert cfg.critic_provider is None
    assert cfg.critic_model is None
    assert cfg.synthesizer_provider is None
    assert cfg.synthesizer_model is None


def test_model_config_explicit_overrides():
    cfg = ModelConfig(
        planner_provider="ollama",
        planner_model="qwen3:4b",
        critic_provider="gemini",
    )
    assert cfg.planner_provider == "ollama"
    assert cfg.planner_model == "qwen3:4b"
    assert cfg.critic_provider == "gemini"
    assert cfg.critic_model is None
    assert cfg.researcher_provider is None
    assert cfg.synthesizer_model is None


# ---------------------------------------------------------------------------
# AgentOutput
# ---------------------------------------------------------------------------


def test_agent_output_model():
    ts = datetime(2024, 6, 1, 10, 0, 0)
    out = AgentOutput(
        agent="researcher",
        content="Some research content.",
        metadata={"confidence": 0.9},
        timestamp=ts,
    )
    assert out.agent == "researcher"
    assert out.content == "Some research content."
    assert out.metadata == {"confidence": 0.9}
    assert out.timestamp == ts


def test_agent_output_default_timestamp():
    out = AgentOutput(agent="analyst", content="Analysis done.")
    assert isinstance(out.timestamp, datetime)
    assert out.metadata == {}


# ---------------------------------------------------------------------------
# CriticVerdict
# ---------------------------------------------------------------------------


def test_critic_verdict_model():
    verdict = CriticVerdict(agree=True, reason="Both agree.", confidence=0.85)
    assert verdict.agree is True
    assert verdict.reason == "Both agree."
    assert verdict.confidence == 0.85


def test_critic_verdict_confidence_bounds():
    # confidence must be 0-1
    with pytest.raises(ValidationError):
        CriticVerdict(agree=True, reason="x", confidence=1.5)
    with pytest.raises(ValidationError):
        CriticVerdict(agree=False, reason="x", confidence=-0.1)


# ---------------------------------------------------------------------------
# StreamEvent
# ---------------------------------------------------------------------------


def test_stream_event_model():
    ts = datetime(2024, 6, 1, 10, 0, 0)
    evt = StreamEvent(event="agent_start", agent="researcher", data={"step": 1}, timestamp=ts)
    assert evt.event == "agent_start"
    assert evt.agent == "researcher"
    assert evt.data == {"step": 1}
    assert evt.timestamp == ts


def test_stream_event_defaults():
    evt = StreamEvent(event="done")
    assert evt.agent is None
    assert evt.data == {}
    assert isinstance(evt.timestamp, datetime)


# ---------------------------------------------------------------------------
# TaskStatusResponse
# ---------------------------------------------------------------------------


def test_task_status_response():
    resp = TaskStatusResponse(
        task_id="abc-123",
        status="done",
        final_answer="Paris",
        error=None,
        events_count=5,
    )
    assert resp.task_id == "abc-123"
    assert resp.status == "done"
    assert resp.final_answer == "Paris"
    assert resp.events_count == 5


def test_task_status_response_defaults():
    resp = TaskStatusResponse(task_id="xyz", status="queued")
    assert resp.final_answer is None
    assert resp.error is None
    assert resp.events_count == 0
