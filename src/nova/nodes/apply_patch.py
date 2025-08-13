from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from ..settings import NovaSettings
from ..telemetry import TelemetryRun
from ..tools import apply_unified_diff, commit_all, ensure_branch, PatchError


def apply_patch_node(state: Dict[str, Any], *, settings: NovaSettings, telemetry: TelemetryRun) -> Dict[str, Any]:
    telemetry.log_event({"node": "apply_patch", "msg": "enter"})
    if state.get("dry_run"):
        telemetry.log_event({"node": "apply_patch", "note": "dry-run; skipping patch"})
        return {"step": int(state.get("step", 0)) + 1}

    if not state.get("approved"):
        return {"last_error": "Patch not approved"}
    diff = state.get("proposed_diff") or ""
    repo = Path(state.get("repo_path", "."))
    try:
        ensure_branch(repo)
        changed = apply_unified_diff(repo, diff, allow_tests_mods=bool(state.get("allow_tests_mods")), max_changed_lines=settings.DIFF_MAX_CHANGED_LINES)
        commit_all(repo, f"Nova fix: step {int(state.get('step', 0)) + 1}")
        telemetry.log_event({"node": "apply_patch", "changed_files": changed})
        return {"step": int(state.get("step", 0)) + 1, "last_error": None}
    except PatchError as e:
        return {"last_error": str(e)}
