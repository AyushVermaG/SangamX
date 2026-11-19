from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load .env from the backend directory (two levels up from this file: app/ -> backend/)
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=_env_path, override=False)

# ---------------------------------------------------------------------------
# Valid provider identifiers
# ---------------------------------------------------------------------------
VALID_PROVIDERS = {"gemini", "groq", "ollama"}


class Settings(BaseModel):
    """
    Application settings loaded from environment variables / .env file.
    Uses plain Pydantic v2 + python-dotenv (no pydantic-settings required).

    Provider priority: gemini (primary) → groq (secondary) → ollama (local fallback).
    ZERO paid API spending: only free-tier quotas and local inference.
    """

    # ------------------------------------------------------------------
    # API Keys  — NEVER expose to frontend
    # ------------------------------------------------------------------
    gemini_api_key: str = Field(default="")
    groq_api_key: str = Field(default="")

    # ------------------------------------------------------------------
    # Ollama (local fallback)
    # ------------------------------------------------------------------
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="qwen3:4b")
    # Max concurrent Ollama requests — tune for 16 GB RAM / NVIDIA GPU
    ollama_max_concurrency: int = Field(default=2)

    # ------------------------------------------------------------------
    # Per-agent provider + model  (provider: gemini | groq | ollama)
    # ------------------------------------------------------------------
    planner_provider: str = Field(default="gemini")
    planner_model: str = Field(default="gemini-2.0-flash-exp")

    researcher_provider: str = Field(default="gemini")
    researcher_model: str = Field(default="gemini-2.0-flash-exp")

    analyst_provider: str = Field(default="gemini")
    analyst_model: str = Field(default="gemini-2.0-flash-exp")

    critic_provider: str = Field(default="groq")
    critic_model: str = Field(default="llama-3.1-8b-instant")

    synthesizer_provider: str = Field(default="gemini")
    synthesizer_model: str = Field(default="gemini-2.0-flash-exp")

    # ------------------------------------------------------------------
    # Provider fallback settings
    # ------------------------------------------------------------------
    # Seconds before a single LLM call is considered timed-out
    llm_timeout: float = Field(default=60.0)
    # Maximum retry attempts per provider before moving to fallback
    provider_max_retries: int = Field(default=2)

    # ------------------------------------------------------------------
    # FastAPI / CORS
    # ------------------------------------------------------------------
    cors_origins: str = Field(default="http://localhost:5173")
    log_level: str = Field(default="INFO")

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @classmethod
    def from_env(cls) -> "Settings":
        """Construct Settings by reading from environment variables."""
        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "qwen3:4b"),
            ollama_max_concurrency=int(os.getenv("OLLAMA_MAX_CONCURRENCY", "2")),
            planner_provider=os.getenv("PLANNER_PROVIDER", "gemini"),
            planner_model=os.getenv("PLANNER_MODEL", "gemini-2.0-flash-exp"),
            researcher_provider=os.getenv("RESEARCHER_PROVIDER", "gemini"),
            researcher_model=os.getenv("RESEARCHER_MODEL", "gemini-2.0-flash-exp"),
            analyst_provider=os.getenv("ANALYST_PROVIDER", "gemini"),
            analyst_model=os.getenv("ANALYST_MODEL", "gemini-2.0-flash-exp"),
            critic_provider=os.getenv("CRITIC_PROVIDER", "groq"),
            critic_model=os.getenv("CRITIC_MODEL", "llama-3.1-8b-instant"),
            synthesizer_provider=os.getenv("SYNTHESIZER_PROVIDER", "gemini"),
            synthesizer_model=os.getenv("SYNTHESIZER_MODEL", "gemini-2.0-flash-exp"),
            llm_timeout=float(os.getenv("LLM_TIMEOUT", "60.0")),
            provider_max_retries=int(os.getenv("PROVIDER_MAX_RETRIES", "2")),
            cors_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
