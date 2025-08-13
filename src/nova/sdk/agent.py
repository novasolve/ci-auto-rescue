from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from ..agent import build_agent
from ..settings import NovaSettings, get_settings
from ..telemetry import TelemetryRun
from ..tools import run_pytest, PytestRunError


@dataclass
class RunSummary:
    success: bool
    iterations: int
    duration_s: float
    files_changed: int
    tools_used: list[str]
    branch_name: str | None
    failing: list[dict]


class NovaAgent:
    def __init__(self, settings: Optional[NovaSettings] = None) -> None:
        self.settings = settings or get_settings()

    def run_fix(
        self,
        repo_path: str | Path,
        *,
        max_iters: Optional[int] = None,
        timeout_s: Optional[int] = None,
        branch_name: Optional[str] = None,
        telemetry_enabled: bool = True,
        dry_run: bool = False,
    ) -> Dict:
        repo = Path(repo_path).resolve()
        # Apply overrides to a shallow copy-like instance (no mutation of global env)
        settings = get_settings()
        if max_iters is not None:
            settings.MAX_ITERS = int(max_iters)
        if timeout_s is not None:
            settings.GLOBAL_TIMEOUT_S = int(timeout_s)
        if not telemetry_enabled:
            settings.TELEMETRY_ENABLED = False

        telemetry = TelemetryRun(enabled=telemetry_enabled)
        telemetry.start_run({
            "repo_path": str(repo),
            "max_iters": settings.MAX_ITERS,
            "timeout_s": settings.GLOBAL_TIMEOUT_S,
            "dry_run": dry_run,
        })
        artifacts_dir = str(telemetry.root_dir)

        baseline: dict = {}
        if not dry_run:
            try:
                junit = Path(artifacts_dir) / "test_reports" / "baseline.xml"
                baseline = run_pytest(repo, settings.PYTEST_TIMEOUT_S, junit)
            except PytestRunError as e:
                telemetry.log_event({"event": "baseline_pytest_error", "error": str(e)})
                baseline = {"total": 0, "failed": 0, "errors": 0, "passed": 0, "failing": []}

        state: Dict = {
            "repo_path": str(repo),
            "run_id": telemetry.run_id,
            "artifacts_dir": artifacts_dir,
            "plan": None,
            "step": 0,
            "diffs": [],
            "failing_targets": None,
            "test_result": baseline,
            "reflections": [],
            "done": False,
            "branch_name": branch_name,
            "last_error": None,
            "used_tools": [],
            "dry_run": bool(dry_run),
            "allow_tests_mods": bool(settings.ALLOW_TEST_MODS),
        }

        agent = build_agent(settings, telemetry)
        start = time.time()
        # Invoke compiled graph until it reaches END
        final_state = agent.invoke(state)
        duration = time.time() - start

        tr = final_state.get("test_result") or {}
        success = (tr.get("failed", 0) + tr.get("errors", 0) == 0) and tr.get("total", 0) > 0 if not dry_run else True
        # Count changed files if present in last apply event; otherwise 0
        files_changed = 0
        if isinstance(final_state.get("diffs"), list):
            files_changed = len(final_state.get("diffs"))

        summary: RunSummary = RunSummary(
            success=bool(success),
            iterations=int(final_state.get("step", 0)),
            duration_s=float(duration),
            files_changed=int(files_changed),
            tools_used=list(final_state.get("used_tools", [])),
            branch_name=final_state.get("branch_name"),
            failing=list((tr.get("failing") or [])),
        )
        telemetry.end_run(success=summary.success, summary=summary.__dict__)
        return summary.__dict__
