"""
Tests for app.config.Settings.
"""
from __future__ import annotations

import os


def test_settings_from_env(monkeypatch):
    """Settings reads API keys from environment variables."""
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-123")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-456")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    from app import config as cfg

    cfg.get_settings.cache_clear()

    settings = cfg.Settings.from_env()
    assert settings.gemini_api_key == "gemini-test-123"
    assert settings.openai_api_key == "openai-test-456"
    assert settings.log_level == "DEBUG"

    cfg.get_settings.cache_clear()


def test_settings_defaults(monkeypatch):
    """Model name defaults should be gemini-2.0-flash-exp."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    # Remove any overriding model env vars
    for k in ("PLANNER_MODEL", "RESEARCHER_MODEL", "ANALYST_MODEL", "CRITIC_MODEL", "SYNTHESIZER_MODEL"):
        monkeypatch.delenv(k, raising=False)

    from app import config as cfg

    cfg.get_settings.cache_clear()

    settings = cfg.Settings.from_env()
    default_model = "gemini-2.0-flash-exp"
    assert settings.planner_model == default_model
    assert settings.researcher_model == default_model
    assert settings.analyst_model == default_model
    assert settings.critic_model == default_model
    assert settings.synthesizer_model == default_model

    cfg.get_settings.cache_clear()


def test_settings_cors_origins_list(monkeypatch):
    """cors_origins_list splits the env string on commas."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
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
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    from app import config as cfg

    cfg.get_settings.cache_clear()

    s1 = cfg.get_settings()
    s2 = cfg.get_settings()
    assert s1 is s2

    cfg.get_settings.cache_clear()
