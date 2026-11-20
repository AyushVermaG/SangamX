"""
Integration and flow tests for the LangGraph workflow entry point (app/engine/graph.py).
Tests verify the backend-facing run_graph(state, queue, config) contract:
- Passing state, event queue, and model config to run_graph()
- Graph execution and return of populated final state
- Disagreement conditional routing logic (revision vs synthesizer)
- Bounded revision behavior (capped at MAX_REVISIONS)
- Exception propagation to caller for proper error state handling
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("GROQ_API_KEY", "test-key")

from app.engine.state import AgentOutput, AgentState, CriticVerdict, ModelConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_initial_state(query: str = "What is the capital of France?") -> AgentState:
    return {
        "query": query,
        "session_id": "test-session-123",
        "plan": None,
        "research_out": None,
        "analyst_out": None,
        "critic_verdict": None,
        "revision_count": 0,
        "final_answer": None,
        "streaming_log": [],
        "error": None,
    }


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
    run_graph(state, queue, config) should compile the graph, execute ainvoke(state),
    and return the updated AgentState containing final_answer.
    """
    from app.engine import graph as graph_module

    state = _make_initial_state("What is the capital of France?")
    queue = asyncio.Queue()
    config = ModelConfig()

    expected_answer = "Paris is the capital of France."
    mock_compiled_graph = AsyncMock()
    mock_compiled_graph.ainvoke.return_value = {
        **state,
        "final_answer": expected_answer,
    }

    with patch.object(graph_module, "_build_graph", return_value=mock_compiled_graph) as mock_build:
        result = await graph_module.run_graph(state, queue, config)

    mock_build.assert_called_once()
    mock_compiled_graph.ainvoke.assert_awaited_once_with(state)
    assert result.get("final_answer") == expected_answer


@pytest.mark.asyncio
async def test_revision_routing_triggered_on_disagreement():
    """
    Graph routing logic routes to 'revision_node' when critic disagrees
    and revision_count < MAX_REVISIONS.
    """
    from app.engine.graph import _build_graph
    from app.config import get_settings

    queue = asyncio.Queue()
    config = ModelConfig()
    settings = get_settings()

    # We inspect the conditional route function created by _build_graph
    # Or test route_after_critic logic directly
    disagree_verdict = _make_verdict(agree=False)
    state: AgentState = {
        **_make_initial_state(),
        "critic_verdict": disagree_verdict,
        "revision_count": 0,
    }

    # Extract the route_after_critic function from _build_graph scope
    # By calling _build_graph with stubs, we can test route_after_critic
    with patch("app.engine.graph.StateGraph") as mock_state_graph:
        mock_builder = MagicMock()
        mock_state_graph.return_value = mock_builder
        _build_graph(queue, config, settings)

        # Find the conditional edge registration
        mock_builder.add_conditional_edges.assert_called_once()
        args, kwargs = mock_builder.add_conditional_edges.call_args
        source_node, route_fn, routes_dict = args

        assert source_node == "critic_node"
        assert routes_dict == {
            "revision_node": "revision_node",
            "synthesizer_node": "synthesizer_node",
        }

        # Test routing when disagree and count == 0 -> revision_node
        assert route_fn(state) == "revision_node"

        # Test routing when agree -> synthesizer_node
        agree_state: AgentState = {
            **_make_initial_state(),
            "critic_verdict": _make_verdict(agree=True),
            "revision_count": 0,
        }
        assert route_fn(agree_state) == "synthesizer_node"


@pytest.mark.asyncio
async def test_revision_bounded_at_max():
    """
    Even if critic disagrees, if revision_count >= MAX_REVISIONS (1),
    route_after_critic must route to 'synthesizer_node' to prevent infinite loops.
    """
    from app.engine.graph import _build_graph
    from app.config import get_settings

    queue = asyncio.Queue()
    config = ModelConfig()
    settings = get_settings()

    disagree_verdict = _make_verdict(agree=False)
    capped_state: AgentState = {
        **_make_initial_state(),
        "critic_verdict": disagree_verdict,
        "revision_count": 1,  # Reached MAX_REVISIONS
    }

    with patch("app.engine.graph.StateGraph") as mock_state_graph:
        mock_builder = MagicMock()
        mock_state_graph.return_value = mock_builder
        _build_graph(queue, config, settings)

        args, _ = mock_builder.add_conditional_edges.call_args
        _, route_fn, _ = args

        # At max revisions, must route to synthesizer_node
        assert route_fn(capped_state) == "synthesizer_node"


@pytest.mark.asyncio
async def test_graph_error_propagates():
    """
    If graph execution raises an unhandled exception, run_graph should re-raise
    so the API layer can record the task status as 'error'.
    """
    from app.engine import graph as graph_module

    state = _make_initial_state("test query")
    queue = asyncio.Queue()
    config = ModelConfig()

    mock_compiled_graph = AsyncMock()
    mock_compiled_graph.ainvoke.side_effect = RuntimeError("Critical node execution failure")

    with patch.object(graph_module, "_build_graph", return_value=mock_compiled_graph):
        with pytest.raises(RuntimeError, match="Critical node execution failure"):
            await graph_module.run_graph(state, queue, config)
