from __future__ import annotations

from app.config import Settings
from app.engine.state import AgentOutput, CriticVerdict, ModelConfig


async def detect_disagreement(
    research_out: AgentOutput,
    analyst_out: AgentOutput,
    query: str,
    config: ModelConfig,
    settings: Settings,
) -> CriticVerdict:
    """
    Invoke the critic agent to judge whether researcher and analyst outputs agree.

    This is a thin wrapper around ``run_critic`` so that graph.py has a single
    well-named call for the disagreement-detection step.

    Returns:
        CriticVerdict with agree, reason, and confidence fields.
    """
    from app.engine.agents.critic import run_critic

    return await run_critic(
        research_out=research_out,
        analyst_out=analyst_out,
        query=query,
        config=config,
        settings=settings,
    )
