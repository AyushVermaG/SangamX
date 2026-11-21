"""
Integration-style tests for the full LangGraph flow.
All LLM calls are mocked; no real API keys needed.

Root causes of previous staleness:
  - Patched `app.engine.graph.run_planner` etc. — these names are NOT importable
    at graph module level; they are lazy-imported inside node closures using
    `from app.engine.agents.X import run_X`. Patches must target the source module.
  - run_graph() now requires (state: AgentState, queue: asyncio.Queue, config: ModelConfig).
    Old tests called run_graph("query") with a bare string.
  - Mock return values were wrong: nodes call the agent functions and use their
    return values directly. run_planner → dict, run_researcher/analyst → AgentOutput,
    detect_disagreement → CriticVerdict, run_synthesizer → str.
  - Stale OPENAI_API_KEY env setup replaced with GROQ_API_KEY.

NOTE: These tests require `langgraph` and `langchain-core` to be installed.
      They are skipped automatically when those packages are unavailable.
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("GROQ_API_KEY", "test-key")

# ---------------------------------------------------------------------------
# Skip entire module if langgraph is not installed
# ---------------------------------------------------------------------------
langgraph = pytest.importorskip(
    "langgraph",
    reason="langgraph not installed — run `pip install langgraph` to enable graph tests",
)

from app.engine.state import AgentOutput, CriticVerdict, ModelConfig, AgentState


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


def _initial_state(query: str = "What is the capital of France?") -> AgentState:
    return AgentState(
        query=query,
        session_id=None,
        plan=None,
        research_out=None,
        analyst_out=None,
        critic_verdict=None,
        revision_count=0,
        final_answer=None,
        streaming_log=[],
        error=None,
    )


PLAN = {"tasks": [], "approach": "Research first.", "complexity": "low"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_graph_flow():
    """
    Mock all agent functions at their source modules.
    run_graph should populate final_answer in the returned state.
    """
    from app.engine.graph import run_graph

    research_out = _make_agent_output("researcher")
    analyst_out = _make_agent_output("analyst")
    agree_verdict = _make_verdict(agree=True)

    queue: asyncio.Queue = asyncio.Queue()
    config = ModelConfig()

    with (
        patch("app.engine.agents.planner.run_planner", new_callable=AsyncMock) as mock_plan,
        patch("app.engine.agents.researcher.run_researcher", new_callable=AsyncMock) as mock_res,
        patch("app.engine.agents.analyst.run_analyst", new_callable=AsyncMock) as mock_ana,
        patch("app.engine.graph.detect_disagreement", new_callable=AsyncMock) as mock_crit,
        patch("app.engine.agents.synthesizer.run_synthesizer", new_callable=AsyncMock) as mock_syn,
    ):
        # Return types must match what each node actually expects from the agent function
        mock_plan.return_value = PLAN
        mock_res.return_value = research_out
        mock_ana.return_value = analyst_out
        mock_crit.return_value = agree_verdict
        mock_syn.return_value = "Paris is the capital of France."

        result = await run_graph(_initial_state(), queue, config)

    assert result.get("final_answer") is not None
    assert "Paris" in result["final_answer"]


@pytest.mark.asyncio
async def test_revision_round_triggered():
    """
    When the critic returns agree=False on the first round,
    revision_count should increment and critic is called again.
    """
    from app.engine.graph import run_graph

    research_out = _make_agent_output("researcher")
    analyst_out = _make_agent_output("analyst")
    disagree_verdict = _make_verdict(agree=False)
    agree_verdict = _make_verdict(agree=True)

    # Critic disagrees first, agrees on second call
    mock_crit = AsyncMock(side_effect=[disagree_verdict, agree_verdict])

    queue: asyncio.Queue = asyncio.Queue()
    config = ModelConfig()

    with (
        patch("app.engine.agents.planner.run_planner", new_callable=AsyncMock,
              return_value=PLAN),
        patch("app.engine.agents.researcher.run_researcher", new_callable=AsyncMock,
              return_value=research_out),
        patch("app.engine.agents.analyst.run_analyst", new_callable=AsyncMock,
              return_value=analyst_out),
        patch("app.engine.graph.detect_disagreement", mock_crit),
        patch("app.engine.agents.synthesizer.run_synthesizer", new_callable=AsyncMock,
              return_value="Revised answer."),
    ):
        result = await run_graph(_initial_state("test query"), queue, config)

    # Critic must have been called at least twice (initial + after revision)
    assert mock_crit.await_count >= 2
    assert result.get("final_answer") is not None


@pytest.mark.asyncio
async def test_revision_bounded():
    """
    Even if the critic always disagrees, the revision loop is capped
    at MAX_REVISIONS=1. The graph must still produce a final_answer.
    """
    from app.engine.graph import run_graph

    research_out = _make_agent_output("researcher")
    analyst_out = _make_agent_output("analyst")
    always_disagree = _make_verdict(agree=False)

    queue: asyncio.Queue = asyncio.Queue()
    config = ModelConfig()

    with (
        patch("app.engine.agents.planner.run_planner", new_callable=AsyncMock,
              return_value=PLAN),
        patch("app.engine.agents.researcher.run_researcher", new_callable=AsyncMock,
              return_value=research_out),
        patch("app.engine.agents.analyst.run_analyst", new_callable=AsyncMock,
              return_value=analyst_out),
        patch("app.engine.graph.detect_disagreement", new_callable=AsyncMock,
              return_value=always_disagree),
        patch("app.engine.agents.synthesizer.run_synthesizer", new_callable=AsyncMock,
              return_value="Best effort answer."),
    ):
        result = await run_graph(_initial_state("test query"), queue, config)

    # Graph must terminate and always produce a final_answer
    assert result.get("final_answer") is not None
    # revision_count must be capped (not unbounded) — MAX_REVISIONS = 1
    assert result.get("revision_count", 0) <= 1


@pytest.mark.asyncio
async def test_graph_emits_events_to_queue():
    """
    The graph should push StreamEvent-compatible dicts into the queue
    as it progresses through nodes.
    """
    from app.engine.graph import run_graph

    research_out = _make_agent_output("researcher")
    analyst_out = _make_agent_output("analyst")
    agree_verdict = _make_verdict(agree=True)

    queue: asyncio.Queue = asyncio.Queue()
    config = ModelConfig()

    with (
        patch("app.engine.agents.planner.run_planner", new_callable=AsyncMock,
              return_value=PLAN),
        patch("app.engine.agents.researcher.run_researcher", new_callable=AsyncMock,
              return_value=research_out),
        patch("app.engine.agents.analyst.run_analyst", new_callable=AsyncMock,
              return_value=analyst_out),
        patch("app.engine.graph.detect_disagreement", new_callable=AsyncMock,
              return_value=agree_verdict),
        patch("app.engine.agents.synthesizer.run_synthesizer", new_callable=AsyncMock,
              return_value="Final answer text."),
    ):
        await run_graph(_initial_state(), queue, config)

    # At least some events must have been emitted
    assert not queue.empty()
    events = []
    while not queue.empty():
        events.append(queue.get_nowait())

    event_types = {e.get("event") for e in events if isinstance(e, dict)}
    # Planner and synthesizer events are always emitted
    assert "agent_start" in event_types
    assert "agent_done" in event_types
