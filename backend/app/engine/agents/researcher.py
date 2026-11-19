from __future__ import annotations

import pathlib
from datetime import datetime
from typing import Optional

from app.config import Settings
from app.engine.providers import invoke_llm
from app.engine.state import AgentOutput, ModelConfig

_PROMPT_PATH = pathlib.Path(__file__).parent.parent.parent / "prompts" / "researcher.txt"


def _load_system_prompt() -> str:
    try:
        return _PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return (
            "You are a research agent. Gather comprehensive, factual information "
            "to address the user query according to the given plan."
        )


async def run_researcher(
    plan: dict,
    query: str,
    config: ModelConfig,
    settings: Settings,
    context: Optional[str] = None,
) -> AgentOutput:
    """
    Research the query according to the plan and return structured findings.

    Args:
        plan:     The structured plan from the planner.
        query:    The original user query.
        config:   Model configuration.
        settings: Application settings.
        context:  Optional critic feedback for revision rounds.

    Returns:
        AgentOutput with agent="researcher", including provider metadata.
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    system_prompt = _load_system_prompt()

    research_tasks = [t for t in plan.get("tasks", []) if t.get("type") == "research"]
    tasks_text = "\n".join(
        f"- [{t.get('id', '?')}] (priority {t.get('priority', 3)}): {t.get('description', '')}"
        for t in research_tasks
    )

    user_content = (
        f"**User Query:** {query}\n\n"
        f"**Research Plan Approach:** {plan.get('approach', 'N/A')}\n\n"
        f"**Your Research Tasks:**\n{tasks_text if tasks_text else 'General research on the query.'}\n\n"
        f"**Complexity:** {plan.get('complexity', 'medium')}"
    )

    if context:
        user_content += (
            f"\n\n**Critic Feedback (Revision Round):**\n{context}\n\n"
            "Please specifically address these concerns in your revised research."
        )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    try:
        result = await invoke_llm(
            messages=messages,
            model=config.researcher_model,
            provider=config.researcher_provider,
            settings=settings,
            temperature=0.3,
        )
        return AgentOutput(
            agent="researcher",
            content=result.content,
            metadata={
                "provider": result.provider,
                "model": result.model,
                "tasks_count": len(research_tasks),
                "is_revision": context is not None,
                **result.metadata,
            },
            timestamp=datetime.utcnow(),
        )
    except Exception as exc:
        raise RuntimeError(f"Researcher LLM call failed: {exc}") from exc
