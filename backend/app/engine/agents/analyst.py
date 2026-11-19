from __future__ import annotations

import pathlib
from datetime import datetime
from typing import Optional

from app.config import Settings
from app.engine.providers import invoke_llm
from app.engine.state import AgentOutput, ModelConfig

_PROMPT_PATH = pathlib.Path(__file__).parent.parent.parent / "prompts" / "analyst.txt"


def _load_system_prompt() -> str:
    try:
        return _PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return (
            "You are an analytical agent. Analyse the information related to the query, "
            "identify patterns, draw conclusions, and make recommendations based on evidence."
        )


async def run_analyst(
    plan: dict,
    query: str,
    config: ModelConfig,
    settings: Settings,
    context: Optional[str] = None,
) -> AgentOutput:
    """
    Analyse the query according to the plan and return structured analytical output.

    Args:
        plan:     The structured plan from the planner.
        query:    The original user query.
        config:   Model configuration.
        settings: Application settings.
        context:  Optional critic feedback for revision rounds.

    Returns:
        AgentOutput with agent="analyst", including provider metadata.
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    system_prompt = _load_system_prompt()

    analysis_tasks = [t for t in plan.get("tasks", []) if t.get("type") == "analysis"]
    tasks_text = "\n".join(
        f"- [{t.get('id', '?')}] (priority {t.get('priority', 3)}): {t.get('description', '')}"
        for t in analysis_tasks
    )

    user_content = (
        f"**User Query:** {query}\n\n"
        f"**Plan Approach:** {plan.get('approach', 'N/A')}\n\n"
        f"**Your Analysis Tasks:**\n{tasks_text if tasks_text else 'General analysis of the query.'}\n\n"
        f"**Complexity:** {plan.get('complexity', 'medium')}"
    )

    if context:
        user_content += (
            f"\n\n**Critic Feedback (Revision Round):**\n{context}\n\n"
            "Please specifically address these concerns in your revised analysis."
        )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    try:
        result = await invoke_llm(
            messages=messages,
            model=config.analyst_model,
            provider=config.analyst_provider,
            settings=settings,
            temperature=0.3,
        )
        return AgentOutput(
            agent="analyst",
            content=result.content,
            metadata={
                "provider": result.provider,
                "model": result.model,
                "tasks_count": len(analysis_tasks),
                "is_revision": context is not None,
                **result.metadata,
            },
            timestamp=datetime.utcnow(),
        )
    except Exception as exc:
        raise RuntimeError(f"Analyst LLM call failed: {exc}") from exc
