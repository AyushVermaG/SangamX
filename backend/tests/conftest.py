"""
Shared pytest fixtures for SangamX backend tests.
Sets fake API keys so no real credentials are needed.
"""
from __future__ import annotations

import os
from datetime import datetime

import pytest

# ---------------------------------------------------------------------------
# Ensure fake API keys are set before any import that might call get_settings()
# ---------------------------------------------------------------------------
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("GROQ_API_KEY", "test-key")


@pytest.fixture(autouse=True)
def _patch_api_keys(monkeypatch):
    """Force fake API keys for every test."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")


@pytest.fixture()
def mock_settings(monkeypatch):
    """Return a Settings instance built from fake env vars."""
    # Clear the lru_cache so the new env vars are picked up.
    from app import config as cfg

    cfg.get_settings.cache_clear()
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    settings = cfg.Settings(
        gemini_api_key="test-key",
        groq_api_key="test-key",
        planner_model="gemini-2.0-flash-exp",
        researcher_model="gemini-2.0-flash-exp",
        analyst_model="gemini-2.0-flash-exp",
        critic_model="llama-3.1-8b-instant",
        synthesizer_model="gemini-2.0-flash-exp",
        cors_origins="http://localhost:5173",
        log_level="INFO",
    )
    return settings


@pytest.fixture()
def sample_query_request():
    from app.engine.state import QueryRequest

    return QueryRequest(query="What is the capital of France?")


@pytest.fixture()
def sample_agent_output():
    from app.engine.state import AgentOutput

    return AgentOutput(
        agent="researcher",
        content="Paris is the capital of France.",
        metadata={"source": "wikipedia"},
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
    )


@pytest.fixture()
def sample_critic_verdict():
    from app.engine.state import CriticVerdict

    return CriticVerdict(agree=True, reason="Both outputs align.", confidence=0.95)
