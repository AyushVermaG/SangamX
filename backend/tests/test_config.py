
"""
Tests for app.config.Settings.

Covers environment loading, provider defaults, Ollama fallback,
CORS parsing, and settings caching.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-123")
    monkeypatch.setenv("GROQ_API_KEY", "groq-test-456")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    from app import config as cfg
    cfg.get_settings.cache_clear()

    settings = cfg.Settings.from_env()
    assert settings.gemini_api_key == "gemini-test-123"
    assert settings.groq_api_key == "groq-test-456"
    assert settings.log_level == "DEBUG"
    assert not hasattr(settings, "openai_api_key")

    cfg.get_settings.cache_clear()


def test_settings_defaults(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    for key in (
        "PLANNER_MODEL", "RESEARCHER_MODEL", "ANALYST_MODEL",
        "CRITIC_MODEL", "SYNTHESIZER_MODEL",
        "PLANNER_PROVIDER", "CRITIC_PROVIDER",
    ):
        monkeypatch.delenv(key, raising=False)

    from app import config as cfg
    cfg.get_settings.cache_clear()

    settings = cfg.Settings.from_env()
    gemini_default = "gemini-2.0-flash-exp"

    assert settings.planner_model == gemini_default
    assert settings.researcher_model == gemini_default
    assert settings.analyst_model == gemini_default
    assert settings.synthesizer_model == gemini_default
    assert settings.critic_provider == "groq"
    assert settings.critic_model == "llama-3.1-8b-instant"

    cfg.get_settings.cache_clear()


def test_ollama_defaults(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)

    from app import config as cfg
    cfg.get_settings.cache_clear()

    settings = cfg.Settings.from_env()
    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.ollama_model == "qwen3:4b"
    assert settings.ollama_max_concurrency == 2

    cfg.get_settings.cache_clear()


def test_settings_cors_origins_list(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000",
    )

    from app import config as cfg
    cfg.get_settings.cache_clear()

    settings = cfg.Settings.from_env()
    assert "http://localhost:5173" in settings.cors_origins_list
    assert "http://localhost:3000" in settings.cors_origins_list
    assert len(settings.cors_origins_list) == 2

    cfg.get_settings.cache_clear()


def test_get_settings_cached(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    from app import config as cfg
    cfg.get_settings.cache_clear()

    s1 = cfg.get_settings()
    s2 = cfg.get_settings()
    assert s1 is s2


@pytest.mark.asyncio
async def test_config_precedence_resolution(monkeypatch):
    """
    Verify actual production configuration-resolution behavior:
    1. Explicit request config overrides take priority.
    2. Missing request config fields inherit from Settings (.env).
    3. Application defaults apply when neither provides a value.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("PLANNER_PROVIDER", "groq")
    monkeypatch.setenv("PLANNER_MODEL", "llama-3.1-8b-instant")
    monkeypatch.setenv("CRITIC_PROVIDER", "groq")
    monkeypatch.setenv("CRITIC_MODEL", "llama-3.1-8b-instant")

    from app import config as cfg
    from app.engine.state import ModelConfig
    from app.engine.graph import run_graph

    cfg.get_settings.cache_clear()
    settings = cfg.get_settings()
    assert settings.planner_provider == "groq"
    assert settings.planner_model == "llama-3.1-8b-instant"

    queue = asyncio.Queue()
    dummy_state = {
        "query": "test query",
        "session_id": None,
        "plan": None,
        "research_out": None,
        "analyst_out": None,
        "critic_verdict": None,
        "revision_count": 0,
        "final_answer": None,
        "streaming_log": [],
        "error": None,
    }

    # Case 1 & 2: Explicit request override takes priority, missing fields inherit from Settings
    req_config = ModelConfig(planner_provider="ollama", planner_model="custom-ollama")

    with patch("app.engine.graph._build_graph") as mock_build:
        mock_compiled = AsyncMock()
        mock_compiled.ainvoke.return_value = {**dummy_state, "final_answer": "Done"}
        mock_build.return_value = mock_compiled

        await run_graph(dummy_state, queue, config=req_config)

        assert mock_build.called
        _, resolved_config, _ = mock_build.call_args[0]

        # Explicit request overrides must take priority over Settings
        assert resolved_config.planner_provider == "ollama"
        assert resolved_config.planner_model == "custom-ollama"

        # Missing request fields must inherit from Settings (.env)
        assert resolved_config.researcher_provider == settings.researcher_provider
        assert resolved_config.researcher_model == settings.researcher_model
        assert resolved_config.critic_provider == "groq"
        assert resolved_config.critic_model == "llama-3.1-8b-instant"

    # Case 3: config=None inherits Settings (.env)
    with patch("app.engine.graph._build_graph") as mock_build:
        mock_compiled = AsyncMock()
        mock_compiled.ainvoke.return_value = {**dummy_state, "final_answer": "Done"}
        mock_build.return_value = mock_compiled

        await run_graph(dummy_state, queue, config=None)

        assert mock_build.called
        _, resolved_none_config, _ = mock_build.call_args[0]

        assert resolved_none_config.planner_provider == "groq"
        assert resolved_none_config.planner_model == "llama-3.1-8b-instant"
        assert resolved_none_config.researcher_provider == settings.researcher_provider
        assert resolved_none_config.researcher_model == settings.researcher_model

    # Case 4: When both request config fields and Settings values are None, application defaults apply
    mock_settings_none = MagicMock()
    mock_settings_none.gemini_api_key = "test-key"
    mock_settings_none.groq_api_key = "test-key"
    mock_settings_none.planner_provider = None
    mock_settings_none.planner_model = None
    mock_settings_none.researcher_provider = None
    mock_settings_none.researcher_model = None
    mock_settings_none.analyst_provider = None
    mock_settings_none.analyst_model = None
    mock_settings_none.critic_provider = None
    mock_settings_none.critic_model = None
    mock_settings_none.synthesizer_provider = None
    mock_settings_none.synthesizer_model = None

    with (
        patch("app.engine.graph.get_settings", return_value=mock_settings_none),
        patch("app.engine.graph._build_graph") as mock_build,
    ):
        mock_compiled = AsyncMock()
        mock_compiled.ainvoke.return_value = {**dummy_state, "final_answer": "Done"}
        mock_build.return_value = mock_compiled

        # Sub-case 4a: config=None and Settings=None -> all application defaults applied
        await run_graph(dummy_state, queue, config=None)
        assert mock_build.called
        _, resolved_defaults, _ = mock_build.call_args[0]

        assert resolved_defaults.planner_provider == "gemini"
        assert resolved_defaults.planner_model == "gemini-2.0-flash-exp"
        assert resolved_defaults.researcher_provider == "gemini"
        assert resolved_defaults.researcher_model == "gemini-2.0-flash-exp"
        assert resolved_defaults.analyst_provider == "gemini"
        assert resolved_defaults.analyst_model == "gemini-2.0-flash-exp"
        assert resolved_defaults.critic_provider == "groq"
        assert resolved_defaults.critic_model == "llama-3.1-8b-instant"
        assert resolved_defaults.synthesizer_provider == "gemini"
        assert resolved_defaults.synthesizer_model == "gemini-2.0-flash-exp"

        # Sub-case 4b: Partial request config with None fields and Settings=None
        partial_none_req = ModelConfig(planner_provider="ollama")
        await run_graph(dummy_state, queue, config=partial_none_req)
        _, resolved_partial_defaults, _ = mock_build.call_args[0]

        assert resolved_partial_defaults.planner_provider == "ollama"
        assert resolved_partial_defaults.planner_model == "gemini-2.0-flash-exp"
        assert resolved_partial_defaults.critic_provider == "groq"
        assert resolved_partial_defaults.critic_model == "llama-3.1-8b-instant"

    cfg.get_settings.cache_clear()
