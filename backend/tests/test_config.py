
"""
Tests for app.config.Settings.

Covers environment loading, provider defaults, Ollama fallback,
CORS parsing, and settings caching.
"""
from __future__ import annotations


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

    cfg.get_settings.cache_clear()
