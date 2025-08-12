from __future__ import annotations

from typing import Any, Dict

from ..llm import LLMClient
from ..llm.prompts import ACTOR_PROMPT
from ..settings import NovaSettings
from ..telemetry import TelemetryRun


def actor_node(state: Dict[str, Any], *, settings: NovaSettings, telemetry: TelemetryRun) -> Dict[str, Any]:
    telemetry.log_event({"node": "actor", "msg": "enter", "step": state.get("step")})
    plan = state.get("plan") or []
    idx = int(state.get("step", 0))
    curr = plan[idx] if idx < len(plan) else "No step"

    if state.get("dry_run"):
        telemetry.log_event({"node": "actor", "plan_step": curr, "note": "dry-run; skipping edit"})
        return {"proposed_diff": "", "used_tools": [*state.get("used_tools", []), "actor"], "approved": True}

    provider = "openai" if settings.OPENAI_API_KEY else ("anthropic" if settings.ANTHROPIC_API_KEY else None)
    if not provider:
        # Without LLM key, cannot generate real diff
        note = "No LLM key; actor cannot generate diff; marking for replan"
        telemetry.log_event({"node": "actor", "warning": note})
        return {"last_error": note, "proposed_diff": None}

    user = f"Plan step to implement:\n{curr}\n\n{ACTOR_PROMPT}"
    llm = LLMClient(provider=provider, telemetry=telemetry)
    diff = llm.complete(system=None, user=user, temperature=0)
    telemetry.log_event({"node": "actor", "produced_diff": diff[:500]})
    return {"proposed_diff": diff, "used_tools": [*state.get("used_tools", []), "actor"]}
