"""
Shared pytest fixtures for SangamX backend tests.

Sets fake API keys and stubs heavy AI dependencies (langgraph, langchain)
so tests run without real credentials or optional packages being installed.

Provider chain: Gemini (primary) → Groq (secondary) → Ollama (local fallback).
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Stub out AI-stack packages that may not be installed in the test environment.
# This must happen BEFORE any app import that triggers these transitive imports.
#
# Packages stubbed here:
#   langgraph / langgraph.graph     — LangGraph StateGraph (AI-engine owned)
#   langchain_core / .messages      — LangChain message types
#   langchain_google_genai          — Gemini provider (optional in test env)
#   langchain_groq                  — Groq provider (optional in test env)
#   langchain_ollama                — Ollama provider (optional in test env)
#
# Real packages (pydantic, fastapi, httpx, sse-starlette) are always present.
# ---------------------------------------------------------------------------

_STUB_MODULES = [
    "langgraph",
    "langgraph.graph",
    "langchain_core",
    "langchain_core.messages",
    "langchain_google_genai",
    "langchain_groq",
    "langchain_ollama",
]

for _mod in _STUB_MODULES:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

# langgraph.graph needs sentinel constants that graph.py uses at import time.
_lg_graph = sys.modules["langgraph.graph"]
_lg_graph.END = "END"
_lg_graph.START = "START"
_lg_graph.StateGraph = MagicMock()

# ---------------------------------------------------------------------------
# Ensure fake API keys are set before any import that calls get_settings()
# NOTE: Project uses GROQ_API_KEY — OPENAI_API_KEY is a stale legacy reference.
# ---------------------------------------------------------------------------
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")


@pytest.fixture(autouse=True)
def _patch_api_keys(monkeypatch):
    """Force fake API keys for every test — no real credentials consumed."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")


@pytest.fixture()
def mock_settings(monkeypatch):
    """Return a Settings instance built from fake env vars."""
    from app import config as cfg

    # Clear the lru_cache so the new env vars are picked up.
    cfg.get_settings.cache_clear()
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")

    settings = cfg.Settings(
        gemini_api_key="test-gemini-key",
        groq_api_key="test-groq-key",
        # Keep per-agent defaults consistent with config.py defaults
        planner_provider="gemini",
        planner_model="gemini-2.0-flash-exp",
        researcher_provider="gemini",
        researcher_model="gemini-2.0-flash-exp",
        analyst_provider="gemini",
        analyst_model="gemini-2.0-flash-exp",
        critic_provider="groq",
        critic_model="llama-3.1-8b-instant",
        synthesizer_provider="gemini",
        synthesizer_model="gemini-2.0-flash-exp",
        cors_origins="http://localhost:5173",
        log_level="INFO",
    )

    yield settings

    cfg.get_settings.cache_clear()


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
