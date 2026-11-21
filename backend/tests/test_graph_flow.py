
"""
Integration-style tests for the full LangGraph flow.
All LLM calls are mocked; no real API keys needed.
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("GROQ_API_KEY", "test-key")

# Skip graph tests if LangGraph is not installed.
pytest.importorskip("langgraph")

from app.engine.state import AgentOutput, AgentState, CriticVerdict, ModelConfig


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


def _make_agent_output(agent: str) -> AgentOutput:
    return AgentOutput(
        agent=agent,
        content=f"{agent} output.",
        timestamp=datetime.utcnow(),
    )


def _make_verdict(agree: bool) -> CriticVerdict:
    return CriticVerdict(
        agree=agree,
        reason="Agree." if agree else "Disagree.",
        confidence=0.9 if agree else 0.7,
    )


PLAN = {
    "tasks": [],
    "approach": "Research first.",
    "complexity": "low",
}


@pytest.mark.asyncio
async def test_full_graph_flow():
    """The complete graph should produce a final answer."""
    from app.engine.graph import run_graph

    research_out = _make_agent_output("researcher")
    analyst_out = _make_agent_output("analyst")
    agree_verdict = _make_verdict(agree=True)

    queue = asyncio.Queue()
    config = ModelConfig()

    with (
        patch(
            "app.engine.agents.planner.run_planner",
            new_callable=AsyncMock,
            return_value=PLAN,
        ),
        patch(
            "app.engine.agents.researcher.run_researcher",
            new_callable=AsyncMock,
            return_value=research_out,
        ),
        patch(
            "app.engine.agents.analyst.run_analyst",
            new_callable=AsyncMock,
            return_value=analyst_out,
        ),
        patch(
            "app.engine.graph.detect_disagreement",
            new_callable=AsyncMock,
            return_value=agree_verdict,
        ),
        patch(
            "app.engine.agents.synthesizer.run_synthesizer",
            new_callable=AsyncMock,
            return_value="Paris is the capital of France.",
        ),
    ):
        result = await run_graph(_initial_state(), queue, config)

    assert result.get("final_answer") is not None
    assert "Paris" in result["final_answer"]


@pytest.mark.asyncio
async def test_revision_round_triggered():
    """A disagreement should trigger one revision round."""
    from app.engine.graph import run_graph

    research_out = _make_agent_output("researcher")
    analyst_out = _make_agent_output("analyst")

    disagree_verdict = _make_verdict(agree=False)
    agree_verdict = _make_verdict(agree=True)

    mock_crit = AsyncMock(
        side_effect=[disagree_verdict, agree_verdict]
    )

    queue = asyncio.Queue()
    config = ModelConfig()

    with (
        patch(
            "app.engine.agents.planner.run_planner",
            new_callable=AsyncMock,
            return_value=PLAN,
        ),
        patch(
            "app.engine.agents.researcher.run_researcher",
            new_callable=AsyncMock,
            return_value=research_out,
        ),
        patch(
            "app.engine.agents.analyst.run_analyst",
            new_callable=AsyncMock,
            return_value=analyst_out,
        ),
        patch("app.engine.graph.detect_disagreement", mock_crit),
        patch(
            "app.engine.agents.synthesizer.run_synthesizer",
            new_callable=AsyncMock,
            return_value="Revised answer.",
        ),
    ):
        result = await run_graph(
            _initial_state("test query"), queue, config
        )

    assert mock_crit.await_count >= 2
    assert result.get("final_answer") is not None


@pytest.mark.asyncio
async def test_revision_bounded():
    """The graph must never exceed MAX_REVISIONS=1."""
    from app.engine.graph import run_graph

    research_out = _make_agent_output("researcher")
    analyst_out = _make_agent_output("analyst")
    always_disagree = _make_verdict(agree=False)

    queue = asyncio.Queue()
    config = ModelConfig()

    with (
        patch(
            "app.engine.agents.planner.run_planner",
            new_callable=AsyncMock,
            return_value=PLAN,
        ),
        patch(
            "app.engine.agents.researcher.run_researcher",
            new_callable=AsyncMock,
            return_value=research_out,
        ),
        patch(
            "app.engine.agents.analyst.run_analyst",
            new_callable=AsyncMock,
            return_value=analyst_out,
        ),
        patch(
            "app.engine.graph.detect_disagreement",
            new_callable=AsyncMock,
            return_value=always_disagree,
        ),
        patch(
            "app.engine.agents.synthesizer.run_synthesizer",
            new_callable=AsyncMock,
            return_value="Best effort answer.",
        ),
    ):
        result = await run_graph(
            _initial_state("test query"), queue, config
        )

    assert result.get("final_answer") is not None
    assert result.get("revision_count", 0) <= 1


@pytest.mark.asyncio
async def test_graph_emits_events_to_queue():
    """The graph should emit agent progress events."""
    from app.engine.graph import run_graph

    research_out = _make_agent_output("researcher")
    analyst_out = _make_agent_output("analyst")
    agree_verdict = _make_verdict(agree=True)

    queue = asyncio.Queue()
    config = ModelConfig()

    with (
        patch(
            "app.engine.agents.planner.run_planner",
            new_callable=AsyncMock,
            return_value=PLAN,
        ),
        patch(
            "app.engine.agents.researcher.run_researcher",
            new_callable=AsyncMock,
            return_value=research_out,
        ),
        patch(
            "app.engine.agents.analyst.run_analyst",
            new_callable=AsyncMock,
            return_value=analyst_out,
        ),
        patch(
            "app.engine.graph.detect_disagreement",
            new_callable=AsyncMock,
            return_value=agree_verdict,
        ),
        patch(
            "app.engine.agents.synthesizer.run_synthesizer",
            new_callable=AsyncMock,
            return_value="Final answer text.",
        ),
    ):
        await run_graph(_initial_state(), queue, config)

    assert not queue.empty()

    events = []
    while not queue.empty():
        events.append(queue.get_nowait())

    event_types = {
        event.get("event")
        for event in events
        if isinstance(event, dict)
    }

    assert "agent_start" in event_types
    assert "agent_done" in event_types


@pytest.mark.asyncio
async def test_revision_routing_triggered_on_disagreement():
    """Disagreement should route to revision_node."""
    from app.engine.graph import _build_graph
    from app.config import get_settings

    queue = asyncio.Queue()
    config = ModelConfig()
    settings = get_settings()

    state = {
        **_initial_state(),
        "critic_verdict": _make_verdict(agree=False),
        "revision_count": 0,
    }

    with patch("app.engine.graph.StateGraph") as mock_state_graph:
        mock_builder = MagicMock()
        mock_state_graph.return_value = mock_builder

        _build_graph(queue, config, settings)

        mock_builder.add_conditional_edges.assert_called_once()
        args, _ = mock_builder.add_conditional_edges.call_args
        _, route_fn, _ = args

        assert route_fn(state) == "revision_node"


@pytest.mark.asyncio
async def test_graph_error_propagates():
    """Unhandled graph errors should propagate to the backend."""
    from app.engine import graph as graph_module

    state = _initial_state("test query")
    queue = asyncio.Queue()
    config = ModelConfig()

    mock_compiled_graph = AsyncMock()
    mock_compiled_graph.ainvoke.side_effect = RuntimeError(
        "Critical node execution failure"
    )

    with patch.object(
        graph_module,
        "_build_graph",
        return_value=mock_compiled_graph,
    ):
        with pytest.raises(
            RuntimeError,
            match="Critical node execution failure",
        ):
            await graph_module.run_graph(state, queue, config)
