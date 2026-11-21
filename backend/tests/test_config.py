"""
Tests for app.config.Settings.

Verifies that Settings correctly reads from environment variables,
applies defaults, and exposes derived properties.
Stale references to openai_api_key (removed) and wrong critic_model
default have been corrected to match the current implementation.
"""
from __future__ import annotations

import os


def test_settings_from_env(monkeypatch):
    """Settings reads API keys from environment variables."""
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-123")
    monkeypatch.setenv("GROQ_API_KEY", "groq-test-456")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    from app import config as cfg

    cfg.get_settings.cache_clear()

    settings = cfg.Settings.from_env()
    assert settings.gemini_api_key == "gemini-test-123"
    assert settings.groq_api_key == "groq-test-456"
    assert settings.log_level == "DEBUG"
    # Confirm openai_api_key is NOT a field (it was removed when stack moved to Groq)
    assert not hasattr(settings, "openai_api_key")

    cfg.get_settings.cache_clear()


def test_settings_defaults(monkeypatch):
    """Model name defaults should match the current provider assignments."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    # Remove any overriding model env vars
    for k in ("PLANNER_MODEL", "RESEARCHER_MODEL", "ANALYST_MODEL", "CRITIC_MODEL", "SYNTHESIZER_MODEL"):
        monkeypatch.delenv(k, raising=False)

    from app import config as cfg

    cfg.get_settings.cache_clear()

    settings = cfg.Settings.from_env()
    gemini_model = "gemini-2.0-flash-exp"
    # Planner, researcher, analyst, synthesizer all default to Gemini
    assert settings.planner_model == gemini_model
    assert settings.researcher_model == gemini_model
    assert settings.analyst_model == gemini_model
    assert settings.synthesizer_model == gemini_model
    # Critic defaults to Groq (fast free-tier model)
    assert settings.critic_model == "llama-3.1-8b-instant"
    assert settings.critic_provider == "groq"

    cfg.get_settings.cache_clear()


def test_settings_ollama_defaults(monkeypatch):
    """Ollama defaults should be set correctly."""
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
    """cors_origins_list splits the env string on commas."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")

    from app import config as cfg

    cfg.get_settings.cache_clear()

    settings = cfg.Settings.from_env()
    assert "http://localhost:5173" in settings.cors_origins_list
    assert "http://localhost:3000" in settings.cors_origins_list
    assert len(settings.cors_origins_list) == 2

    cfg.get_settings.cache_clear()


def test_get_settings_cached(monkeypatch):
    """get_settings() returns the same object on repeated calls (lru_cache)."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    from app import config as cfg

    cfg.get_settings.cache_clear()

    s1 = cfg.get_settings()
    s2 = cfg.get_settings()
    assert s1 is s2

    cfg.get_settings.cache_clear()
