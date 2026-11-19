from __future__ import annotations

import json
import pathlib

from app.config import Settings
from app.engine.providers import invoke_llm
from app.engine.state import AgentOutput, CriticVerdict, ModelConfig

_PROMPT_PATH = pathlib.Path(__file__).parent.parent.parent / "prompts" / "critic.txt"


def _load_system_prompt() -> str:
    try:
        return _PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return (
            "You are a critic agent. Compare the researcher and analyst outputs for "
            "factual contradictions or incompatible recommendations. "
            'Return JSON: {"agree": bool, "reason": str, "confidence": float (0-1)}'
        )


async def run_critic(
    research_out: AgentOutput,
    analyst_out: AgentOutput,
    query: str,
    config: ModelConfig,
    settings: Settings,
) -> CriticVerdict:
    """
    Evaluate whether the researcher and analyst outputs are consistent.

    Args:
        research_out: Output from the researcher agent.
        analyst_out:  Output from the analyst agent.
        query:        The original user query.
        config:       Model configuration.
        settings:     Application settings.

    Returns:
        CriticVerdict with agree, reason, and confidence.
        Defaults to agree=True if the LLM response cannot be parsed
        (safe fallback — prevents infinite revision loops).
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    system_prompt = _load_system_prompt()

    user_content = (
        f"**Original Query:** {query}\n\n"
        f"**Researcher Output:**\n{research_out.content}\n\n"
        f"**Analyst Output:**\n{analyst_out.content}\n\n"
        "Evaluate whether these two outputs agree or contradict each other on key facts "
        "and recommendations. Return ONLY valid JSON in the format:\n"
        '{"agree": true/false, "reason": "explanation", "confidence": 0.0-1.0}'
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    try:
        result = await invoke_llm(
            messages=messages,
            model=config.critic_model,
            provider=config.critic_provider,
            settings=settings,
            temperature=0.1,
        )
        raw = result.content

        # Strip markdown code fences if present
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        verdict_data = json.loads(raw)
        return CriticVerdict(
            agree=bool(verdict_data.get("agree", True)),
            reason=str(verdict_data.get("reason", "No reason provided.")),
            confidence=float(verdict_data.get("confidence", 0.8)),
        )

    except json.JSONDecodeError as exc:
        # Safe fallback: default to agreement to avoid infinite revision loops
        return CriticVerdict(
            agree=True,
            reason=f"Could not parse critic response (JSON error): {exc}. Defaulting to agreement.",
            confidence=0.5,
        )
    except Exception as exc:
        raise RuntimeError(f"Critic LLM call failed: {exc}") from exc
