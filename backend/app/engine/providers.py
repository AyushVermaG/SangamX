"""
SangamX Provider Abstraction
============================

Supported providers (in priority order):
  1. gemini  — Google Gemini API (primary, free tier via API key)
  2. groq    — Groq API (secondary, free tier via API key)
  3. ollama  — Local Ollama server (fallback, always free, no API key)

ZERO-COST GUARANTEE
-------------------
This module NEVER falls back to a paid provider. The fallback chain is:
  primary (cloud) → Ollama (local)

If Ollama is also unavailable, AllProvidersFailedError is raised.
No paid upgrade, no silent billing. Period.

Concurrency
-----------
Ollama inference is GPU/CPU-bound. A module-level asyncio.Semaphore limits
concurrent Ollama calls to `settings.ollama_max_concurrency` (default 2).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, List

from app.config import Settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ProviderError(RuntimeError):
    """Base class for provider-related errors."""


class QuotaExceededError(ProviderError):
    """Cloud provider returned HTTP 429 or quota exhausted signal."""


class ProviderUnavailableError(ProviderError):
    """Cloud provider is unreachable or timed out."""


class OllamaUnavailableError(ProviderError):
    """Local Ollama server is not running or unreachable."""


class AllProvidersFailedError(ProviderError):
    """All providers failed and no further fallback is available.

    This error is intentionally NOT caught by the caller — it propagates
    to the API layer which reports it as a task error.
    """


# ---------------------------------------------------------------------------
# Response type
# ---------------------------------------------------------------------------


@dataclass
class LLMResponse:
    """Result of an LLM invocation, including which provider actually served it."""

    content: str
    provider: str   # "gemini" | "groq" | "ollama"
    model: str      # exact model name used
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Module-level Ollama concurrency semaphore
# ---------------------------------------------------------------------------

_ollama_semaphore: asyncio.Semaphore | None = None


def _get_ollama_semaphore(max_concurrency: int) -> asyncio.Semaphore:
    """Return (or lazily create) the module-level Ollama semaphore."""
    global _ollama_semaphore
    if _ollama_semaphore is None or _ollama_semaphore._value != max_concurrency:  # type: ignore[attr-defined]
        _ollama_semaphore = asyncio.Semaphore(max_concurrency)
    return _ollama_semaphore


def reset_ollama_semaphore() -> None:
    """Reset the semaphore (used in tests to avoid state leakage)."""
    global _ollama_semaphore
    _ollama_semaphore = None


# ---------------------------------------------------------------------------
# Individual provider constructors
# ---------------------------------------------------------------------------


def _build_gemini(model: str, api_key: str, temperature: float):
    """Build a ChatGoogleGenerativeAI instance."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as exc:
        raise ProviderUnavailableError(
            "langchain-google-genai is not installed. Run: pip install langchain-google-genai"
        ) from exc

    if not api_key:
        raise ProviderUnavailableError(
            "GEMINI_API_KEY is not set. Add it to your .env file."
        )

    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=temperature,
    )


def _build_groq(model: str, api_key: str, temperature: float):
    """Build a ChatGroq instance."""
    try:
        from langchain_groq import ChatGroq
    except ImportError as exc:
        raise ProviderUnavailableError(
            "langchain-groq is not installed. Run: pip install langchain-groq"
        ) from exc

    if not api_key:
        raise ProviderUnavailableError(
            "GROQ_API_KEY is not set. Add it to your .env file."
        )

    return ChatGroq(
        model=model,
        api_key=api_key,
        temperature=temperature,
    )


def _build_ollama(model: str, base_url: str, temperature: float):
    """Build a ChatOllama instance."""
    try:
        from langchain_ollama import ChatOllama
    except ImportError as exc:
        raise OllamaUnavailableError(
            "langchain-ollama is not installed. Run: pip install langchain-ollama"
        ) from exc

    return ChatOllama(
        model=model,
        base_url=base_url,
        temperature=temperature,
    )


# ---------------------------------------------------------------------------
# Error classifiers
# ---------------------------------------------------------------------------


def _is_quota_error(exc: BaseException) -> bool:
    """Return True if the exception signals a quota / rate-limit from a cloud provider."""
    msg = str(exc).lower()
    quota_signals = (
        "429",
        "quota",
        "rate limit",
        "rate_limit",
        "resource exhausted",
        "resourceexhausted",
        "too many requests",
        "exceeded",
        "limit exceeded",
    )
    if any(sig in msg for sig in quota_signals):
        return True
    # Check exception type names (avoids import dependencies)
    type_name = type(exc).__name__.lower()
    return any(t in type_name for t in ("ratelimit", "quota", "resourceexhausted"))


def _is_unavailable_error(exc: BaseException) -> bool:
    """Return True if the exception signals provider unavailability / timeout."""
    msg = str(exc).lower()
    unavailable_signals = (
        "timeout",
        "connection",
        "unreachable",
        "unavailable",
        "serviceunavailable",
        "503",
        "502",
        "network",
        "connect error",
        "connecterror",
    )
    if any(sig in msg for sig in unavailable_signals):
        return True
    type_name = type(exc).__name__.lower()
    return any(t in type_name for t in ("timeout", "connection", "unavailable"))


# ---------------------------------------------------------------------------
# Core invocation logic
# ---------------------------------------------------------------------------


async def _invoke_with_timeout(llm, messages: List[Any], timeout: float) -> str:
    """Invoke a LangChain LLM with a timeout. Returns response content string."""
    try:
        response = await asyncio.wait_for(llm.ainvoke(messages), timeout=timeout)
        return response.content.strip()
    except asyncio.TimeoutError as exc:
        raise ProviderUnavailableError(
            f"LLM call timed out after {timeout}s"
        ) from exc


async def _invoke_cloud(
    provider: str,
    model: str,
    messages: List[Any],
    settings: Settings,
    temperature: float,
    max_retries: int,
) -> str:
    """
    Attempt to invoke a cloud provider (gemini or groq) with retry logic.

    Raises:
        QuotaExceededError     — on HTTP 429 / quota signal (do NOT retry cloud)
        ProviderUnavailableError — on timeout / connection failure (retried up to max_retries)
    """
    if provider == "gemini":
        llm = _build_gemini(model, settings.gemini_api_key, temperature)
    elif provider == "groq":
        llm = _build_groq(model, settings.groq_api_key, temperature)
    else:
        raise ProviderUnavailableError(f"Unknown cloud provider: {provider!r}")

    last_exc: BaseException | None = None
    for attempt in range(1, max_retries + 1):
        try:
            return await _invoke_with_timeout(llm, messages, settings.llm_timeout)
        except Exception as exc:
            if _is_quota_error(exc):
                # Quota exceeded — no point retrying the same provider
                logger.warning(
                    "Provider %r quota exceeded (attempt %d/%d): %s",
                    provider, attempt, max_retries, exc,
                )
                raise QuotaExceededError(
                    f"Provider {provider!r} quota exceeded: {exc}"
                ) from exc
            elif _is_unavailable_error(exc):
                last_exc = exc
                logger.warning(
                    "Provider %r unavailable (attempt %d/%d): %s",
                    provider, attempt, max_retries, exc,
                )
                if attempt < max_retries:
                    await asyncio.sleep(1.0 * attempt)  # simple backoff
            else:
                # Unknown error — propagate immediately
                raise ProviderUnavailableError(
                    f"Provider {provider!r} error: {exc}"
                ) from exc

    raise ProviderUnavailableError(
        f"Provider {provider!r} unavailable after {max_retries} attempts: {last_exc}"
    ) from last_exc


async def _invoke_ollama(
    model: str,
    messages: List[Any],
    settings: Settings,
    temperature: float,
) -> str:
    """
    Invoke the local Ollama server with concurrency limiting.

    Raises:
        OllamaUnavailableError — if Ollama is not running or the model is missing.
    """
    semaphore = _get_ollama_semaphore(settings.ollama_max_concurrency)
    llm = _build_ollama(model, settings.ollama_base_url, temperature)

    async with semaphore:
        try:
            return await _invoke_with_timeout(llm, messages, settings.llm_timeout * 2)
        except OllamaUnavailableError:
            raise
        except Exception as exc:
            if _is_unavailable_error(exc) or "connection" in str(exc).lower():
                raise OllamaUnavailableError(
                    f"Ollama server at {settings.ollama_base_url} is unreachable: {exc}. "
                    "Make sure Ollama is running: `ollama serve`"
                ) from exc
            raise OllamaUnavailableError(f"Ollama error: {exc}") from exc


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def invoke_llm(
    messages: List[Any],
    model: str,
    provider: str,
    settings: Settings,
    temperature: float = 0.3,
) -> LLMResponse:
    """
    Invoke an LLM through the provider abstraction with automatic Ollama fallback.

    Fallback chain (ZERO paid tier):
        primary provider → Ollama local fallback

    Args:
        messages:    LangChain message list (HumanMessage, SystemMessage, etc.)
        model:       Model name for the primary provider.
        provider:    "gemini" | "groq" | "ollama"
        settings:    Application settings (holds API keys, URLs, timeouts).
        temperature: Sampling temperature (0–1).

    Returns:
        LLMResponse with .content, .provider (actual), .model (actual).

    Raises:
        AllProvidersFailedError — if primary provider AND Ollama both fail.
    """
    if provider == "ollama":
        # Direct local call — no cloud involved
        try:
            content = await _invoke_ollama(model, messages, settings, temperature)
            return LLMResponse(content=content, provider="ollama", model=model)
        except OllamaUnavailableError as exc:
            raise AllProvidersFailedError(
                f"Ollama requested directly but is unavailable: {exc}"
            ) from exc

    # Cloud provider attempt
    primary_error: str = ""
    try:
        content = await _invoke_cloud(
            provider=provider,
            model=model,
            messages=messages,
            settings=settings,
            temperature=temperature,
            max_retries=settings.provider_max_retries,
        )
        logger.debug("Provider %r (%s) succeeded.", provider, model)
        return LLMResponse(content=content, provider=provider, model=model)

    except (QuotaExceededError, ProviderUnavailableError) as exc:
        primary_error = str(exc)
        logger.warning(
            "Primary provider %r failed (%s). Attempting Ollama fallback.",
            provider, exc,
        )

    # Ollama fallback — ZERO paid tier
    ollama_model = settings.ollama_model
    logger.info(
        "Falling back to Ollama (model=%r, base_url=%r).",
        ollama_model, settings.ollama_base_url,
    )
    try:
        content = await _invoke_ollama(ollama_model, messages, settings, temperature)
        logger.info("Ollama fallback succeeded.")
        return LLMResponse(
            content=content,
            provider="ollama",
            model=ollama_model,
            metadata={"fallback_reason": primary_error},
        )
    except OllamaUnavailableError as exc:
        raise AllProvidersFailedError(
            f"All providers failed.\n"
            f"  Primary ({provider}/{model}): {primary_error}\n"
            f"  Ollama ({ollama_model}): {exc}\n"
            "Check your .env API keys and ensure Ollama is running: `ollama serve`"
        ) from exc


def get_llm(model_name: str, settings: Settings, temperature: float = 0.3):
    """
    Backward-compatible synchronous LLM constructor.

    Detects provider from model name prefix:
      gemini-*  → Gemini
      ollama/*  → Ollama
      (other)   → Groq

    NOTE: Prefer invoke_llm() for new code — it has fallback and recording.
    This function exists for compatibility with the existing agent call sites
    during migration; agents are being updated to use invoke_llm().
    """
    if model_name.startswith("gemini"):
        return _build_gemini(model_name, settings.gemini_api_key, temperature)
    elif model_name.startswith("ollama/"):
        bare = model_name.removeprefix("ollama/")
        return _build_ollama(bare, settings.ollama_base_url, temperature)
    else:
        return _build_groq(model_name, settings.groq_api_key, temperature)
