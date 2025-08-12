from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from ..settings import NovaSettings
from ..telemetry import TelemetryRun
from ..tools import run_pytest, PytestRunError


def run_tests_node(state: Dict[str, Any], *, settings: NovaSettings, telemetry: TelemetryRun) -> Dict[str, Any]:
    telemetry.log_event({"node": "run_tests", "msg": "enter"})
    if state.get("dry_run"):
        # Simulate unchanged test outcome
        res = state.get("test_result") or {"total": 0, "failed": 0, "errors": 0, "passed": 0, "failing": []}
        telemetry.log_event({"node": "run_tests", "note": "dry-run; skipping pytest"})
        return {"test_result": res}

    repo = Path(state.get("repo_path", "."))
    junit = Path(state.get("artifacts_dir", ".nova")) / "test_reports" / "report.xml"
    try:
        results = run_pytest(repo, settings.PYTEST_TIMEOUT_S, junit)
        telemetry.log_event({"node": "run_tests", "summary": {k: results.get(k) for k in ("total","failed","errors","passed")}})
        return {"test_result": results}
    except PytestRunError as e:
        return {"last_error": str(e)}
