from __future__ import annotations

import json
import pathlib

from app.config import Settings
from app.engine.providers import invoke_llm
from app.engine.state import ModelConfig

_PROMPT_PATH = pathlib.Path(__file__).parent.parent.parent / "prompts" / "planner.txt"


def _load_system_prompt() -> str:
    try:
        return _PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return (
            "You are a planning agent. Break the user query into a structured JSON plan "
            "with keys: tasks (list of {id, type, description, priority}), approach, complexity."
        )


async def run_planner(
    query: str,
    config: ModelConfig,
    settings: Settings,
) -> dict:
    """
    Generate a structured research plan from the user query.

    Returns a dict with keys:
      tasks: list of {id, type, description, priority}
      approach: str
      complexity: "low" | "medium" | "high"
      _provider_meta: dict (actual provider/model used)
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    system_prompt = _load_system_prompt()
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"User query: {query}"),
    ]

    try:
        result = await invoke_llm(
            messages=messages,
            model=config.planner_model,
            provider=config.planner_provider,
            settings=settings,
            temperature=0.2,
        )
        raw = result.content

        # Strip markdown code fences if present
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        plan = json.loads(raw)

        # Validate required keys; fill defaults if missing
        plan.setdefault("tasks", [])
        plan.setdefault("approach", "Research and analyse the query.")
        plan.setdefault("complexity", "medium")

        # Attach provider metadata for transparency
        plan["_provider_meta"] = {
            "agent": "planner",
            "provider": result.provider,
            "model": result.model,
        }

        return plan

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Planner returned non-JSON response: {exc}. Raw: {raw[:500]}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"Planner LLM call failed: {exc}") from exc
