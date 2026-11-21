"""
Tests for the critic / disagreement detection logic.
Mocks invoke_llm; no real API keys required.

Root causes of previous staleness:
  - Patched non-existent `_get_critic_llm` helper (removed in provider refactor).
  - Called run_critic(research, analysis) with 2 args; actual signature takes 5.
  - Called detect_disagreement(research, analysis) with 2 args; actual takes 5.
  - detect_disagreement returns CriticVerdict, not bool.
  - Import paths were wrong (app.engine.critic vs app.engine.agents.critic).
"""
from __future__ import annotations

import os
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("GROQ_API_KEY", "test-key")

from app.engine.state import AgentOutput, CriticVerdict
from app.config import Settings
from app.engine.state import ModelConfig
from app.engine.providers import LLMResponse


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_agent_output(agent: str, content: str) -> AgentOutput:
    return AgentOutput(agent=agent, content=content, timestamp=datetime.utcnow())


def _make_settings() -> Settings:
    return Settings(
        gemini_api_key="test-key",
        groq_api_key="test-key",
        ollama_model="qwen3:4b",
        llm_timeout=5.0,
        provider_max_retries=1,
    )


def _make_config() -> ModelConfig:
    return ModelConfig()


# ---------------------------------------------------------------------------
# run_critic tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_critic_agree():
    """When invoke_llm returns agree=True JSON, CriticVerdict.agree is True."""
    from app.engine.agents.critic import run_critic

    verdict_json = '{"agree": true, "reason": "Both outputs align.", "confidence": 0.9}'
    research = _make_agent_output("researcher", "Paris is the capital.")
    analysis = _make_agent_output("analyst", "Paris is confirmed.")

    with patch("app.engine.agents.critic.invoke_llm") as mock_invoke:
        mock_invoke.return_value = LLMResponse(
            content=verdict_json, provider="groq", model="llama-3.1-8b-instant"
        )
        verdict = await run_critic(
            research_out=research,
            analyst_out=analysis,
            query="What is the capital of France?",
            config=_make_config(),
            settings=_make_settings(),
        )

    assert isinstance(verdict, CriticVerdict)
    assert verdict.agree is True
    assert verdict.confidence == 0.9


@pytest.mark.asyncio
async def test_critic_disagree():
    """When invoke_llm returns agree=False JSON, CriticVerdict.agree is False."""
    from app.engine.agents.critic import run_critic

    verdict_json = '{"agree": false, "reason": "Outputs contradict.", "confidence": 0.8}'
    research = _make_agent_output("researcher", "Paris is the capital.")
    analysis = _make_agent_output("analyst", "Lyon is the capital.")

    with patch("app.engine.agents.critic.invoke_llm") as mock_invoke:
        mock_invoke.return_value = LLMResponse(
            content=verdict_json, provider="groq", model="llama-3.1-8b-instant"
        )
        verdict = await run_critic(
            research_out=research,
            analyst_out=analysis,
            query="What is the capital of France?",
            config=_make_config(),
            settings=_make_settings(),
        )

    assert isinstance(verdict, CriticVerdict)
    assert verdict.agree is False
    assert verdict.reason == "Outputs contradict."


@pytest.mark.asyncio
async def test_critic_json_parse_failure_defaults_to_agree():
    """When invoke_llm returns invalid JSON, run_critic safely defaults to agree=True."""
    from app.engine.agents.critic import run_critic

    research = _make_agent_output("researcher", "R content.")
    analysis = _make_agent_output("analyst", "A content.")

    with patch("app.engine.agents.critic.invoke_llm") as mock_invoke:
        mock_invoke.return_value = LLMResponse(
            content="not valid json at all", provider="groq", model="llama-3.1-8b-instant"
        )
        verdict = await run_critic(
            research_out=research,
            analyst_out=analysis,
            query="Some query",
            config=_make_config(),
            settings=_make_settings(),
        )

    assert isinstance(verdict, CriticVerdict)
    # Safe fallback: defaults to agreement to prevent infinite revision loops
    assert verdict.agree is True
    assert "JSON error" in verdict.reason or "Could not parse" in verdict.reason


# ---------------------------------------------------------------------------
# detect_disagreement tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_detect_disagreement_returns_verdict_when_disagree():
    """detect_disagreement returns CriticVerdict with agree=False when critic disagrees."""
    from app.engine.disagreement import detect_disagreement

    mock_verdict = CriticVerdict(agree=False, reason="Contradictory outputs.", confidence=0.75)

    with patch("app.engine.agents.critic.run_critic", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_verdict

        research = _make_agent_output("researcher", "A")
        analysis = _make_agent_output("analyst", "B")

        result = await detect_disagreement(
            research_out=research,
            analyst_out=analysis,
            query="Some query",
            config=_make_config(),
            settings=_make_settings(),
        )

    assert isinstance(result, CriticVerdict)
    assert result.agree is False
    assert result.confidence == 0.75
    mock_run.assert_awaited_once()


@pytest.mark.asyncio
async def test_detect_disagreement_returns_verdict_when_agree():
    """detect_disagreement returns CriticVerdict with agree=True when critic agrees."""
    from app.engine.disagreement import detect_disagreement

    mock_verdict = CriticVerdict(agree=True, reason="Outputs align.", confidence=0.9)

    with patch("app.engine.agents.critic.run_critic", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_verdict

        research = _make_agent_output("researcher", "Paris is the capital.")
        analysis = _make_agent_output("analyst", "Paris confirmed.")

        result = await detect_disagreement(
            research_out=research,
            analyst_out=analysis,
            query="Capital of France?",
            config=_make_config(),
            settings=_make_settings(),
        )

    assert isinstance(result, CriticVerdict)
    assert result.agree is True
    mock_run.assert_awaited_once()
