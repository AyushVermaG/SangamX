"""
Integration-style tests for the full LangGraph flow.
All LLM calls are mocked; no real API keys needed.
"""
from __future__ import annotations

import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("OPENAI_API_KEY", "test-key")

from app.engine.state import AgentOutput, CriticVerdict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_agent_output(agent: str) -> AgentOutput:
    return AgentOutput(agent=agent, content=f"{agent} output.", timestamp=datetime.utcnow())


def _make_verdict(agree: bool) -> CriticVerdict:
    return CriticVerdict(
        agree=agree,
        reason="Agree." if agree else "Disagree.",
        confidence=0.9 if agree else 0.7,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_graph_flow():
    """
    Mock all LLM-backed node calls; run_graph should populate final_answer.
    """
    from app.engine import graph as graph_module

    research_out = _make_agent_output("researcher")
    analyst_out = _make_agent_output("analyst")
    agree_verdict = _make_verdict(agree=True)

    patches = {
        "app.engine.graph.run_planner": AsyncMock(return_value={"plan": {"steps": ["step1"]}}),
        "app.engine.graph.run_researcher": AsyncMock(
            return_value={"research_out": research_out}
        ),
        "app.engine.graph.run_analyst": AsyncMock(return_value={"analyst_out": analyst_out}),
        "app.engine.graph.run_critic": AsyncMock(
            return_value={"critic_verdict": agree_verdict}
        ),
        "app.engine.graph.run_synthesizer": AsyncMock(
            return_value={"final_answer": "Paris is the capital of France."}
        ),
    }

    with (
        patch("app.engine.graph.run_planner", patches["app.engine.graph.run_planner"]),
        patch("app.engine.graph.run_researcher", patches["app.engine.graph.run_researcher"]),
        patch("app.engine.graph.run_analyst", patches["app.engine.graph.run_analyst"]),
        patch("app.engine.graph.run_critic", patches["app.engine.graph.run_critic"]),
        patch("app.engine.graph.run_synthesizer", patches["app.engine.graph.run_synthesizer"]),
    ):
        result = await graph_module.run_graph("What is the capital of France?")

    assert result.get("final_answer") is not None
    assert "Paris" in result["final_answer"]


@pytest.mark.asyncio
async def test_revision_round_triggered():
    """
    When the critic returns agree=False on the first round,
    revision_count should increment to 1 before the second critic pass.
    """
    from app.engine import graph as graph_module

    research_out = _make_agent_output("researcher")
    analyst_out = _make_agent_output("analyst")
    disagree_verdict = _make_verdict(agree=False)
    agree_verdict = _make_verdict(agree=True)

    # Critic disagrees first, agrees on second call
    critic_side_effects = [
        {"critic_verdict": disagree_verdict},
        {"critic_verdict": agree_verdict},
    ]
    mock_critic = AsyncMock(side_effect=critic_side_effects)

    with (
        patch("app.engine.graph.run_planner", AsyncMock(return_value={"plan": {}})),
        patch(
            "app.engine.graph.run_researcher",
            AsyncMock(return_value={"research_out": research_out}),
        ),
        patch(
            "app.engine.graph.run_analyst",
            AsyncMock(return_value={"analyst_out": analyst_out}),
        ),
        patch("app.engine.graph.run_critic", mock_critic),
        patch(
            "app.engine.graph.run_synthesizer",
            AsyncMock(return_value={"final_answer": "Revised answer."}),
        ),
    ):
        result = await graph_module.run_graph("test query")

    # Critic was called at least twice (initial + after revision)
    assert mock_critic.await_count >= 2
    assert result.get("final_answer") is not None


@pytest.mark.asyncio
async def test_revision_bounded():
    """
    Even if critic always disagrees, revision should cap at 1 extra round
    (revision_count <= 1 after the graph finishes).
    """
    from app.engine import graph as graph_module

    research_out = _make_agent_output("researcher")
    analyst_out = _make_agent_output("analyst")
    always_disagree = _make_verdict(agree=False)

    with (
        patch("app.engine.graph.run_planner", AsyncMock(return_value={"plan": {}})),
        patch(
            "app.engine.graph.run_researcher",
            AsyncMock(return_value={"research_out": research_out}),
        ),
        patch(
            "app.engine.graph.run_analyst",
            AsyncMock(return_value={"analyst_out": analyst_out}),
        ),
        patch("app.engine.graph.run_critic", AsyncMock(return_value={"critic_verdict": always_disagree})),
        patch(
            "app.engine.graph.run_synthesizer",
            AsyncMock(return_value={"final_answer": "Best effort answer."}),
        ),
    ):
        result = await graph_module.run_graph("test query")

    # Graph must terminate and provide a final_answer regardless of disagreement
    assert result.get("final_answer") is not None
    # revision_count must be capped (not unbounded)
    assert result.get("revision_count", 0) <= 1
