"""
Tests for the critic / disagreement detection logic.
Mocks LLM calls; no real API keys required.
"""
from __future__ import annotations

import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("OPENAI_API_KEY", "test-key")

from app.engine.state import AgentOutput, CriticVerdict


def _make_agent_output(agent: str, content: str) -> AgentOutput:
    return AgentOutput(agent=agent, content=content, timestamp=datetime.utcnow())


# ---------------------------------------------------------------------------
# Helpers that build a fake LLM response with a given agree value
# ---------------------------------------------------------------------------

def _llm_response(agree: bool) -> MagicMock:
    verdict_json = (
        '{"agree": true, "reason": "Both outputs align.", "confidence": 0.9}'
        if agree
        else '{"agree": false, "reason": "Outputs contradict.", "confidence": 0.8}'
    )
    msg = MagicMock()
    msg.content = verdict_json
    return msg


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_critic_agree():
    """When LLM returns agree=True, CriticVerdict.agree should be True."""
    from app.engine import critic as critic_module

    fake_llm = AsyncMock()
    fake_llm.ainvoke.return_value = _llm_response(agree=True)

    research = _make_agent_output("researcher", "Paris is the capital.")
    analysis = _make_agent_output("analyst", "Paris is confirmed.")

    with patch.object(critic_module, "_get_critic_llm", return_value=fake_llm):
        verdict = await critic_module.run_critic(research, analysis)

    assert isinstance(verdict, CriticVerdict)
    assert verdict.agree is True


@pytest.mark.asyncio
async def test_critic_disagree():
    """When LLM returns agree=False, CriticVerdict.agree should be False."""
    from app.engine import critic as critic_module

    fake_llm = AsyncMock()
    fake_llm.ainvoke.return_value = _llm_response(agree=False)

    research = _make_agent_output("researcher", "Paris is the capital.")
    analysis = _make_agent_output("analyst", "Lyon is the capital.")

    with patch.object(critic_module, "_get_critic_llm", return_value=fake_llm):
        verdict = await critic_module.run_critic(research, analysis)

    assert isinstance(verdict, CriticVerdict)
    assert verdict.agree is False


@pytest.mark.asyncio
async def test_disagreement_detection():
    """detect_disagreement returns True when critic verdict has agree=False."""
    from app.engine import disagreement as dis_module

    mock_verdict = CriticVerdict(agree=False, reason="Contradictory outputs.", confidence=0.75)

    # Patch run_critic inside disagreement module
    with patch.object(dis_module, "run_critic", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_verdict

        research = _make_agent_output("researcher", "A")
        analysis = _make_agent_output("analyst", "B")

        result = await dis_module.detect_disagreement(research, analysis)

    assert result is True
    mock_run.assert_awaited_once()
