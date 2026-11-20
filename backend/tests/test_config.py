"""
Tests for app.config.Settings.

Verifies that settings are read correctly from environment variables,
defaults are sane, and the lru_cache works as expected.
Provider chain: Gemini (primary) → Groq (secondary) → Ollama (local fallback).
"""
from __future__ import annotations

import os


def test_settings_from_env(monkeypatch):
    """Settings reads API keys from environment variables."""
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-123")
    # NOTE: Project uses GROQ_API_KEY — OPENAI_API_KEY is a legacy reference removed.
    monkeypatch.setenv("GROQ_API_KEY", "groq-test-456")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    from app import config as cfg

    cfg.get_settings.cache_clear()

    settings = cfg.Settings.from_env()
    assert settings.gemini_api_key == "gemini-test-123"
    assert settings.groq_api_key == "groq-test-456"
    assert settings.log_level == "DEBUG"

    cfg.get_settings.cache_clear()


def test_settings_defaults(monkeypatch):
    """Model name defaults should match config.py defaults."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    # Remove any overriding model env vars
    for k in (
        "PLANNER_MODEL",
        "RESEARCHER_MODEL",
        "ANALYST_MODEL",
        "CRITIC_MODEL",
        "SYNTHESIZER_MODEL",
        "PLANNER_PROVIDER",
        "CRITIC_PROVIDER",
    ):
        monkeypatch.delenv(k, raising=False)

    from app import config as cfg

    cfg.get_settings.cache_clear()

    settings = cfg.Settings.from_env()
    gemini_default = "gemini-2.0-flash-exp"

    # Gemini-backed agents use the Gemini flash model by default
    assert settings.planner_model == gemini_default
    assert settings.researcher_model == gemini_default
    assert settings.analyst_model == gemini_default
    assert settings.synthesizer_model == gemini_default

    # Critic defaults to Groq (fast free-tier) — different model and provider
    assert settings.critic_provider == "groq"
    assert settings.critic_model == "llama-3.1-8b-instant"

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
