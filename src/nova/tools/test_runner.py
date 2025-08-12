from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .sandbox import run_command


def ensure_reports_dir(repo_root: Path) -> Path:
    d = Path(repo_root) / ".nova_reports"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _safe_read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return None


def _extract_failure_info(test: Dict[str, Any]) -> Dict[str, Any]:
    nodeid = test.get("nodeid")
    tb = None
    msg = None

    def _from_phase(phase: str) -> None:
        nonlocal tb, msg
        phase_data = test.get(phase) or {}
        lr = phase_data.get("longrepr")
        if lr is None:
            return
        if isinstance(lr, str):
            tb = lr
            # message as first line
            msg = lr.strip().splitlines()[0] if lr.strip() else ""
        elif isinstance(lr, dict):
            tb = lr.get("reprcrash", {}).get("message") or lr.get("reprtraceback") or str(lr)
            if isinstance(tb, dict):
                msg = tb.get("message") or ""
                tb = json.dumps(tb)
            else:
                msg = msg or (str(tb).splitlines()[0] if tb else "")
        else:
            tb = str(lr)
            msg = msg or (str(tb).splitlines()[0] if tb else "")

    for phase in ("setup", "call", "teardown"):
        _from_phase(phase)
    return {"nodeid": nodeid, "message": msg or "", "traceback": tb or ""}


def _parse_json_report(report_path: Path) -> Dict[str, Any]:
    data = _safe_read_json(report_path) or {}
    tests = data.get("tests") or []
    failed: List[Dict[str, Any]] = []
    passed: List[str] = []
    errors: List[Dict[str, Any]] = []

    for t in tests:
        outcome = t.get("outcome")
        nodeid = t.get("nodeid")
        if outcome == "passed":
            passed.append(nodeid)
        elif outcome == "failed":
            failed.append(_extract_failure_info(t))
        elif outcome == "error":
            errors.append(_extract_failure_info(t))

    duration = float(data.get("duration", 0.0) or 0.0)
    return {"failed": failed, "passed": passed, "errors": errors, "duration": duration}


_summary_failed_re = re.compile(r"^FAILED\s+(?P<node>\S+)\s+-\s+(?P<msg>.*)$")
_summary_error_re = re.compile(r"^ERROR\s+(?P<node>\S+)\s+-\s+(?P<msg>.*)$")
_summary_passed_re = re.compile(r"^(?P<node>\S+)\s+PASSED$")


def _parse_text_fallback(text: str) -> Dict[str, Any]:
    failed: List[Dict[str, Any]] = []
    passed: List[str] = []
    errors: List[Dict[str, Any]] = []

    lines = text.splitlines()
    # Attempt to parse summary lines
    for line in lines:
        m = _summary_passed_re.match(line.strip())
        if m:
            passed.append(m.group("node"))
            continue
        m = _summary_failed_re.match(line.strip())
        if m:
            failed.append({
                "nodeid": m.group("node"),
                "message": m.group("msg"),
                "traceback": "",
            })
            continue
        m = _summary_error_re.match(line.strip())
        if m:
            errors.append({
                "nodeid": m.group("node"),
                "message": m.group("msg"),
                "traceback": "",
            })
            continue

    return {"failed": failed, "passed": passed, "errors": errors, "duration": 0.0}


def run_pytest(repo_root: Path, timeout: int, extra_args: Optional[List[str]] = None) -> Dict[str, Any]:
    repo_root = Path(repo_root)
    reports_dir = ensure_reports_dir(repo_root)
    report_file = reports_dir / "report.json"

    base_cmd = [
        "pytest",
        "-q",
        "--maxfail=1",
        "--disable-warnings",
        "--json-report",
        "--json-report-file",
        str(report_file.relative_to(repo_root)),
    ]
    if extra_args:
        base_cmd.extend(extra_args)

    res = run_command(base_cmd, cwd=repo_root, timeout=timeout, env={"NO_COLOR": "1"})

    # Prefer JSON report if present
    if report_file.exists():
        try:
            parsed = _parse_json_report(report_file)
            return parsed
        except Exception:
            # Fall back to text parsing using captured stdout/stderr
            text = (res.get("stdout", "") or "") + "\n" + (res.get("stderr", "") or "")
            return _parse_text_fallback(text)

    # If JSON missing (plugin unavailable or error), run a fallback invocation and parse stdout
    fallback_cmd = ["pytest", "-q", "--maxfail=1", "--disable-warnings", "-rA"]
    if extra_args:
        fallback_cmd.extend(extra_args)
    res_fb = run_command(fallback_cmd, cwd=repo_root, timeout=timeout, env={"NO_COLOR": "1"})
    text = (res_fb.get("stdout", "") or "") + "\n" + (res_fb.get("stderr", "") or "")
    return _parse_text_fallback(text)


__all__ = ["run_pytest", "ensure_reports_dir"]
