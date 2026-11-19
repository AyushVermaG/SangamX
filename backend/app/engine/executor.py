from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

from app.config import Settings
from app.engine.state import AgentOutput, ModelConfig, StreamEvent


async def parallel_execute(
    query: str,
    plan: dict,
    config: ModelConfig,
    settings: Settings,
    queue: asyncio.Queue,
    revision_context: Optional[str] = None,
) -> tuple[AgentOutput, AgentOutput]:
    """
    Run researcher and analyst agents concurrently using asyncio.gather.

    Args:
        query:            The original user query.
        plan:             The structured plan from the planner.
        config:           Per-request model configuration.
        settings:         Application settings (holds API keys).
        queue:            SSE event queue for streaming progress updates.
        revision_context: Optional critic feedback injected on the revision round.

    Returns:
        A 2-tuple ``(research_out, analyst_out)``.
    """
    from app.engine.agents.researcher import run_researcher
    from app.engine.agents.analyst import run_analyst

    # --- Emit agent_start events -------------------------------------------------
    now = datetime.utcnow()
    await queue.put(
        StreamEvent(
            event="agent_start",
            agent="researcher",
            data={"message": "Researcher starting…"},
            timestamp=now,
        ).model_dump(mode="json")
    )
    await queue.put(
        StreamEvent(
            event="agent_start",
            agent="analyst",
            data={"message": "Analyst starting…"},
            timestamp=now,
        ).model_dump(mode="json")
    )

    # --- Run both agents concurrently -------------------------------------------
    research_out, analyst_out = await asyncio.gather(
        run_researcher(
            plan=plan,
            query=query,
            config=config,
            settings=settings,
            context=revision_context,
        ),
        run_analyst(
            plan=plan,
            query=query,
            config=config,
            settings=settings,
            context=revision_context,
        ),
    )

    # --- Emit agent_done events --------------------------------------------------
    done_ts = datetime.utcnow()
    await queue.put(
        StreamEvent(
            event="agent_done",
            agent="researcher",
            data={"preview": research_out.content[:200]},
            timestamp=done_ts,
        ).model_dump(mode="json")
    )
    await queue.put(
        StreamEvent(
            event="agent_done",
            agent="analyst",
            data={"preview": analyst_out.content[:200]},
            timestamp=done_ts,
        ).model_dump(mode="json")
    )

    return research_out, analyst_out
