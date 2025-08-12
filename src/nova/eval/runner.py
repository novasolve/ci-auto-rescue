from __future__ import annotations

import json
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import yaml

from ..agent.graph import build_agent
from ..config import NovaSettings
from ..telemetry.logger import JSONLLogger
from ..tools import git_tool


@dataclass
class _Item:
    name: str
    repo_path: Path


def _load_items(config_path: Path) -> List[_Item]:
    data = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    items: List[_Item] = []
    if not isinstance(data, list):
        return items
    for entry in data:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        repo = entry.get("repo_path")
        if not name or not repo:
            continue
        p = Path(repo).expanduser().resolve()
        if not p.exists():
            continue
        items.append(_Item(name=name, repo_path=p))
    return items


def _infer_used_tools(repo_path: Path, settings: NovaSettings) -> List[str]:
    tools: List[str] = []
    # Heuristics only; detailed telemetry is added elsewhere
    if settings.openai_api_key:
        tools.append("llm")
    if settings.openswe_base_url:
        tools.append("openswe")
    # Try to see if git is available/usable
    try:
        git_tool.current_branch(repo_path)
        tools.append("git")
    except Exception:
        pass
    tools.append("pytest")
    return sorted(set(tools))


def run_batch(config_path: Path, settings: NovaSettings) -> Dict[str, Any]:
    """Run Nova agent over a batch of repositories defined in a YAML file.

    YAML format: a list of entries with fields {name: str, repo_path: str}

    Returns a dict containing overall stats and per-repo results:
    {
      "total": int,
      "successes": int,
      "success_rate": float,
      "avg_duration": float,
      "results": [
        {"name", "repo_path", "success", "duration", "iterations", "used_tools", ...}
      ]
    }
    """
    items = _load_items(Path(config_path))

    results: List[Dict[str, Any]] = []
    durations: List[float] = []
    successes = 0

    for it in items:
        logger = JSONLLogger(settings, enabled=False)
        logger.start_run(it.repo_path)
        run_agent = build_agent(settings=settings, logger=logger)

        start = time.monotonic()
        summary: Dict[str, Any] | None = None
        success = False
        try:
            summary = run_agent(it.repo_path)
            success = bool(summary.get("success"))
        except Exception as e:
            summary = {"success": False, "error": str(e), "iterations": 0, "duration": 0.0}
        finally:
            duration = float(summary.get("duration", time.monotonic() - start)) if summary else (time.monotonic() - start)
            durations.append(duration)

        if success:
            successes += 1

        used_tools = _infer_used_tools(it.repo_path, settings)

        row = {
            "name": it.name,
            "repo_path": str(it.repo_path),
            "success": success,
            "duration": float(summary.get("duration", duration)) if summary else duration,
            "iterations": int(summary.get("iterations", 0)) if summary else 0,
            "used_tools": used_tools,
        }
        # Include tests summary if present (but keep compact)
        if summary and "tests" in summary:
            try:
                tests = summary["tests"]
                if isinstance(tests, dict):
                    row["tests"] = {
                        "failed": len(tests.get("failed", [])),
                        "errors": len(tests.get("errors", [])),
                        "passed": len(tests.get("passed", [])),
                        "duration": float(tests.get("duration", 0.0)),
                    }
            except Exception:
                pass

        results.append(row)
        logger.end_run(success=success, summary=row)

    total = len(items)
    overall: Dict[str, Any] = {
        "total": total,
        "successes": successes,
        "success_rate": (successes / total) if total else 0.0,
        "avg_duration": (sum(durations) / len(durations)) if durations else 0.0,
        "results": results,
    }
    if durations:
        overall["median_duration"] = statistics.median(durations)
    return overall


__all__ = ["run_batch"]
