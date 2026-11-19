from __future__ import annotations

import pathlib

from app.config import Settings
from app.engine.providers import invoke_llm
from app.engine.state import AgentOutput, CriticVerdict, ModelConfig

_PROMPT_PATH = pathlib.Path(__file__).parent.parent.parent / "prompts" / "synthesizer.txt"


def _load_system_prompt() -> str:
    try:
        return _PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return (
            "You are a synthesizer agent. Merge the researcher's findings and the analyst's "
            "conclusions into one authoritative, coherent, and well-structured final answer "
            "for the user. Avoid contradictions. Use markdown formatting."
        )


async def run_synthesizer(
    query: str,
    plan: dict,
    research_out: AgentOutput,
    analyst_out: AgentOutput,
    critic_verdict: CriticVerdict,
    config: ModelConfig,
    settings: Settings,
) -> str:
    """
    Synthesise research and analysis into a single coherent final answer.

    Args:
        query:          The original user query.
        plan:           The planner's structured plan.
        research_out:   Output from the researcher agent.
        analyst_out:    Output from the analyst agent.
        critic_verdict: The critic's verdict (informs synthesis framing).
        config:         Per-request model configuration.
        settings:       Application settings.

    Returns:
        A markdown-formatted string ready for the end user.
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    system_prompt = _load_system_prompt()

    critic_note = (
        f"The critic found no significant disagreement between the two agents "
        f"(confidence: {critic_verdict.confidence:.0%}). {critic_verdict.reason}"
        if critic_verdict.agree
        else (
            f"The critic identified a disagreement and a revision round was run. "
            f"Critic note: {critic_verdict.reason}"
        )
    )

    user_content = (
        f"**User Query:** {query}\n\n"
        f"**Plan Approach:** {plan.get('approach', 'N/A')}\n\n"
        f"**Researcher Findings:**\n{research_out.content}\n\n"
        f"**Analyst Conclusions:**\n{analyst_out.content}\n\n"
        f"**Critic Assessment:** {critic_note}\n\n"
        "Synthesise the above into one clear, comprehensive, and well-structured answer "
        "for the user. Use markdown headings, bullet points, and code blocks where appropriate. "
        "Do not simply concatenate the two outputs — produce a unified, authoritative response."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    try:
        result = await invoke_llm(
            messages=messages,
            model=config.synthesizer_model,
            provider=config.synthesizer_provider,
            settings=settings,
            temperature=0.4,
        )
        return result.content
    except Exception as exc:
        raise RuntimeError(f"Synthesizer LLM call failed: {exc}") from exc
