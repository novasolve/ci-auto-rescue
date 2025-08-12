from __future__ import annotations

import json
from typing import Any, Dict

from ..llm import LLMClient
from ..llm.prompts import PLANNER_PROMPT
from ..settings import NovaSettings
from ..telemetry import TelemetryRun


def planner_node(state: Dict[str, Any], *, settings: NovaSettings, telemetry: TelemetryRun) -> Dict[str, Any]:
    telemetry.log_event({"node": "planner", "msg": "enter", "step": state.get("step")})
    if state.get("dry_run"):
        steps = ["Dry-run: analyze failures", "Dry-run: propose minimal change"]
        telemetry.log_event({"node": "planner", "steps": steps})
        return {"plan": steps, "step": 0}

    # Summarize failing tests if present
    failing = state.get("test_result", {}).get("failing", [])
    context = {
        "failing": [{"nodeid": f.get("nodeid"), "message": f.get("message")} for f in failing][:10]
    }
    user = "Repo failing tests summary:\n" + json.dumps(context, ensure_ascii=False)

    provider = "openai" if settings.OPENAI_API_KEY else ("anthropic" if settings.ANTHROPIC_API_KEY else None)
    if not provider:
        steps = ["Plan step: read failures", "Plan step: narrow down target file", "Plan step: implement fix"]
        telemetry.log_event({"node": "planner", "steps": steps, "note": "no LLM key; fallback plan"})
        return {"plan": steps, "step": 0}

    llm = LLMClient(provider=provider, telemetry=telemetry)
    resp = llm.complete(system=PLANNER_PROMPT, user=user, temperature=0)
    # Try parse JSON, else fall back to lines
    try:
        data = json.loads(resp)
        steps = data.get("steps") or []
        if isinstance(steps, list) and all(isinstance(s, str) for s in steps):
            plan = steps
        else:
            plan = [resp]
    except Exception:
        plan = [s.strip() for s in resp.splitlines() if s.strip()][:5]
    telemetry.log_event({"node": "planner", "plan": plan})
    return {"plan": plan, "step": 0}
