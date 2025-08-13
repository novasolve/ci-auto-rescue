from __future__ import annotations

from typing import Any, Dict

from ..settings import NovaSettings
from ..telemetry import TelemetryRun
from ..tools import parse_unified_diff, changed_line_count, PatchError
from ..llm.prompts import CRITIC_PROMPT
from ..llm import LLMClient


def critic_node(state: Dict[str, Any], *, settings: NovaSettings, telemetry: TelemetryRun) -> Dict[str, Any]:
    telemetry.log_event({"node": "critic", "msg": "enter"})
    if state.get("dry_run"):
        return {"approved": True}

    diff = state.get("proposed_diff") or ""
    if not diff.strip():
        return {"approved": False, "last_error": "Empty diff"}
    try:
        patch = parse_unified_diff(diff)
        lines = changed_line_count(patch)
        if lines > settings.DIFF_MAX_CHANGED_LINES:
            return {"approved": False, "last_error": f"Diff too large: {lines}"}
    except PatchError as e:
        return {"approved": False, "last_error": str(e)}

    provider = "openai" if settings.OPENAI_API_KEY else ("anthropic" if settings.ANTHROPIC_API_KEY else None)
    if not provider:
        # Approve based on static checks only
        return {"approved": True}

    llm = LLMClient(provider=provider, telemetry=telemetry)
    review = llm.complete(system=CRITIC_PROMPT, user=diff[:8000], temperature=0)
    first = (review.splitlines() or [""])[0].strip().lower()
    approved = first.startswith("approved")
    telemetry.log_event({"node": "critic", "decision": first})
    return {"approved": approved, "last_error": None if approved else "Rejected by critic"}
