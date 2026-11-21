from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Literal, Optional

from langgraph.graph import END, START, StateGraph

from app.config import Settings, get_settings
from app.engine.disagreement import detect_disagreement
from app.engine.executor import parallel_execute
from app.engine.state import AgentState, CriticVerdict, ModelConfig, StreamEvent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MAX_REVISIONS = 1


def _emit(queue: asyncio.Queue, event: str, agent: str | None = None, **data) -> None:
    """Fire-and-forget: schedule a StreamEvent on the queue from sync code."""
    evt = StreamEvent(
        event=event,
        agent=agent,
        data=data,
        timestamp=datetime.utcnow(),
    )
    queue.put_nowait(evt.model_dump(mode="json"))


# ---------------------------------------------------------------------------
# Node factory
# We close over *queue*, *config*, and *settings* at graph-build time so that
# every node receives a plain AgentState dict (what LangGraph expects).
# ---------------------------------------------------------------------------


def _build_graph(queue: asyncio.Queue, config: ModelConfig, settings: Settings):
    """Construct and compile the LangGraph StateGraph for one engine run."""

    # ------------------------------------------------------------------ nodes

    async def planner_node(state: AgentState) -> dict:
        """Decompose the user query into a structured plan."""
        from app.engine.agents.planner import run_planner

        _emit(queue, "agent_start", "planner", message="Planner decomposing query…")
        try:
            plan = await run_planner(
                query=state["query"],
                config=config,
                settings=settings,
            )
            _emit(
                queue,
                "agent_done",
                "planner",
                approach=plan.get("approach", ""),
                complexity=plan.get("complexity", ""),
                tasks_count=len(plan.get("tasks", [])),
            )
            return {"plan": plan}
        except Exception as exc:
            logger.exception("Planner failed: %s", exc)
            _emit(queue, "error", "planner", message=str(exc))
            return {"error": str(exc)}

    async def parallel_node(state: AgentState) -> dict:
        """Run researcher and analyst in parallel."""
        revision_context: str | None = None
        if state.get("critic_verdict") and not state["critic_verdict"].agree:  # type: ignore[union-attr]
            verdict: CriticVerdict = state["critic_verdict"]  # type: ignore[assignment]
            revision_context = verdict.reason

        if revision_context:
            _emit(
                queue,
                "revision_start",
                None,
                message="Revision round triggered.",
                reason=revision_context,
                round=state.get("revision_count", 0) + 1,
            )

        research_out, analyst_out = await parallel_execute(
            query=state["query"],
            plan=state["plan"] or {},
            config=config,
            settings=settings,
            queue=queue,
            revision_context=revision_context,
        )
        return {
            "research_out": research_out,
            "analyst_out": analyst_out,
        }

    async def critic_node(state: AgentState) -> dict:
        """Evaluate researcher and analyst outputs for disagreement."""
        _emit(queue, "agent_start", "critic", message="Critic evaluating outputs…")
        try:
            verdict = await detect_disagreement(
                research_out=state["research_out"],  # type: ignore[arg-type]
                analyst_out=state["analyst_out"],  # type: ignore[arg-type]
                query=state["query"],
                config=config,
                settings=settings,
            )
            _emit(
                queue,
                "agent_done",
                "critic",
                agree=verdict.agree,
                confidence=verdict.confidence,
                reason=verdict.reason,
            )
            if not verdict.agree:
                _emit(
                    queue,
                    "disagreement",
                    None,
                    reason=verdict.reason,
                    confidence=verdict.confidence,
                )
            return {
                "critic_verdict": verdict,
                "revision_count": state.get("revision_count", 0),
            }
        except Exception as exc:
            logger.exception("Critic failed: %s", exc)
            _emit(queue, "error", "critic", message=str(exc))
            return {"error": str(exc)}

    async def revision_node(state: AgentState) -> dict:
        """Increment the revision counter before the next parallel round."""
        new_count = state.get("revision_count", 0) + 1
        logger.info("Revision round %d starting.", new_count)
        return {"revision_count": new_count}

    async def synthesizer_node(state: AgentState) -> dict:
        """Merge all outputs into the final answer."""
        from app.engine.agents.synthesizer import run_synthesizer

        _emit(queue, "agent_start", "synthesizer", message="Synthesizer generating final answer…")
        try:
            final_answer = await run_synthesizer(
                query=state["query"],
                plan=state["plan"] or {},
                research_out=state["research_out"],  # type: ignore[arg-type]
                analyst_out=state["analyst_out"],  # type: ignore[arg-type]
                critic_verdict=state["critic_verdict"],  # type: ignore[arg-type]
                config=config,
                settings=settings,
            )
            _emit(
                queue,
                "final_answer",
                "synthesizer",
                content=final_answer,
                preview=final_answer[:300],
            )
            _emit(queue, "agent_done", "synthesizer", message="Done.")
            return {"final_answer": final_answer}
        except Exception as exc:
            logger.exception("Synthesizer failed: %s", exc)
            _emit(queue, "error", "synthesizer", message=str(exc))
            return {"error": str(exc)}

    # ------------------------------------------------------------------ edges

    def route_after_critic(state: AgentState) -> Literal["revision_node", "synthesizer_node"]:
        """
        If the critic disagrees AND we haven't hit the revision cap, loop back.
        Otherwise proceed to synthesis.
        """
        verdict: CriticVerdict | None = state.get("critic_verdict")  # type: ignore[assignment]
        revision_count: int = state.get("revision_count", 0)

        if verdict is not None and not verdict.agree and revision_count < MAX_REVISIONS:
            return "revision_node"
        return "synthesizer_node"

    # ------------------------------------------------------------------ build

    builder = StateGraph(AgentState)

    builder.add_node("planner_node", planner_node)
    builder.add_node("parallel_node", parallel_node)
    builder.add_node("critic_node", critic_node)
    builder.add_node("revision_node", revision_node)
    builder.add_node("synthesizer_node", synthesizer_node)

    builder.add_edge(START, "planner_node")
    builder.add_edge("planner_node", "parallel_node")
    builder.add_edge("parallel_node", "critic_node")
    builder.add_conditional_edges(
        "critic_node",
        route_after_critic,
        {
            "revision_node": "revision_node",
            "synthesizer_node": "synthesizer_node",
        },
    )
    builder.add_edge("revision_node", "parallel_node")
    builder.add_edge("synthesizer_node", END)

    return builder.compile()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


async def run_graph(
    state: AgentState,
    queue: asyncio.Queue,
    config: Optional[ModelConfig] = None,
) -> AgentState:
    """
    Entry point for the multi-agent graph execution.

    Orchestrates:
        planner → (researcher ‖ analyst) → critic → [revision loop] → synthesizer

    Pushes StreamEvent-compatible dicts into *queue* as execution progresses.
    Returns the final AgentState when the graph terminates.

    Raises:
        RuntimeError: if any critical node fails and the error propagates.
    """
    settings: Settings = get_settings()

    # Warn if no cloud keys are configured (Ollama-only mode)
    if not settings.gemini_api_key and not settings.groq_api_key:
        logger.warning(
            "No cloud API keys configured (GEMINI_API_KEY / GROQ_API_KEY). "
            "All requests will use Ollama local fallback."
        )

    # Configuration precedence:
    # 1. Explicit request overrides take priority.
    # 2. Missing fields inherit from backend Settings (.env).
    # 3. Application defaults apply when neither provides a value.
    req_config = config or ModelConfig()
    merged = ModelConfig(
        planner_provider=req_config.planner_provider or getattr(settings, "planner_provider", None) or "gemini",
        planner_model=req_config.planner_model or getattr(settings, "planner_model", None) or "gemini-2.0-flash-exp",
        researcher_provider=req_config.researcher_provider or getattr(settings, "researcher_provider", None) or "gemini",
        researcher_model=req_config.researcher_model or getattr(settings, "researcher_model", None) or "gemini-2.0-flash-exp",
        analyst_provider=req_config.analyst_provider or getattr(settings, "analyst_provider", None) or "gemini",
        analyst_model=req_config.analyst_model or getattr(settings, "analyst_model", None) or "gemini-2.0-flash-exp",
        critic_provider=req_config.critic_provider or getattr(settings, "critic_provider", None) or "groq",
        critic_model=req_config.critic_model or getattr(settings, "critic_model", None) or "llama-3.1-8b-instant",
        synthesizer_provider=req_config.synthesizer_provider or getattr(settings, "synthesizer_provider", None) or "gemini",
        synthesizer_model=req_config.synthesizer_model or getattr(settings, "synthesizer_model", None) or "gemini-2.0-flash-exp",
    )

    graph = _build_graph(queue, merged, settings)

    try:
        final_state: AgentState = await graph.ainvoke(state)  # type: ignore[assignment]
        return final_state
    except Exception as exc:
        logger.exception("Graph execution failed: %s", exc)
        # Propagate so the API layer can mark the task as errored
        raise
