from __future__ import annotations

from typing import Any, Dict

from ..settings import NovaSettings
from ..telemetry import TelemetryRun


def reflect_node(state: Dict[str, Any], *, settings: NovaSettings, telemetry: TelemetryRun) -> Dict[str, Any]:
    telemetry.log_event({"node": "reflect", "msg": "enter"})
    if state.get("dry_run"):
        return {"done": True, "reflections": [*state.get("reflections", []), "Dry-run complete."]}

    tr = state.get("test_result") or {}
    failed = int(tr.get("failed", 0)) + int(tr.get("errors", 0))
    if tr and failed == 0 and int(tr.get("total", 0)) > 0:
        return {"done": True, "reflections": [*state.get("reflections", []), "All tests passing."]}

    # Continue if under iteration cap; otherwise stop
    if int(state.get("step", 0)) >= int(getattr(settings, "MAX_ITERS", 6)):
        return {"done": True, "reflections": [*state.get("reflections", []), "Reached max iterations."]}

    return {"done": False}
