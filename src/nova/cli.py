from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from .agent.graph import build_agent
from .config import get_settings
from .telemetry.logger import JSONLLogger
from .tools import git_tool

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


@app.command()
def fix(
    repo_path: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True, readable=True, help="Path to the git repository to fix."),
    max_iters: Optional[int] = typer.Option(None, "--max-iters", help="Maximum agent iterations (override settings)."),
    timeout: Optional[int] = typer.Option(None, "--timeout", help="Overall timeout in seconds (override settings)."),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose console output."),
    no_telemetry: bool = typer.Option(False, "--no-telemetry", help="Disable local telemetry logging."),
):
    """Run Nova CI‑Rescue against a repository to attempt to fix failing tests."""
    settings = get_settings()
    if max_iters is not None or timeout is not None:
        updates = {}
        if max_iters is not None:
            updates["max_iters"] = int(max_iters)
        if timeout is not None:
            updates["run_timeout_sec"] = int(timeout)
        try:
            settings = settings.model_copy(update=updates)  # pydantic v2
        except Exception:
            # Fallback for pydantic v1
            data = settings.dict()
            data.update(updates)
            from pydantic import BaseModel

            settings = type("_Settings", (BaseModel,), {})(**data)  # type: ignore

    logger = JSONLLogger(settings=settings, enabled=not no_telemetry)

    run_id = logger.start_run(repo_path)
    console.print(Panel.fit(f"Nova CI‑Rescue starting at {_ts()}\nRun ID: {run_id}", title="Nova"))

    # Ensure git repo and try to create a fix branch
    branch_name: Optional[str] = None
    try:
        git_tool.ensure_repo(repo_path)
        try:
            branch_name = git_tool.create_fix_branch(repo_path)
            if verbose:
                console.print(f"Created branch: [bold]{branch_name}[/bold]")
        except git_tool.GitError as e:
            if verbose:
                console.print(f"[yellow]Warning:[/yellow] Could not create branch: {e}")
    except git_tool.GitError as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.end_run(success=False, summary={"error": str(e)})
        raise typer.Exit(2)

    # Build and run agent
    run_agent = build_agent(settings=settings, logger=logger)

    summary = None
    try:
        summary = run_agent(repo_path)
        success = bool(summary.get("success"))
        if success:
            console.print("[green]Success:[/green] All tests passing.")
        else:
            console.print("[yellow]Completed:[/yellow] Some tests still failing.")
        if verbose:
            console.print(json.dumps(summary, indent=2))
        logger.end_run(success=success, summary={"branch": branch_name, **(summary or {})})
        raise typer.Exit(0 if success else 1)
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted[/red] - resetting repository to HEAD...")
        try:
            git_tool.reset_hard(repo_path, "HEAD")
        except Exception:
            pass
        logger.end_run(success=False, summary={"interrupted": True, "branch": branch_name, **(summary or {}) if summary else {}})
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[red]Run failed:[/red] {e}")
        logger.end_run(success=False, summary={"error": str(e), "branch": branch_name, **(summary or {}) if summary else {}})
        raise typer.Exit(1)


@app.command()
def eval(
    repos: Path = typer.Option(..., "--repos", help="YAML file with a list of repos: [{name, repo_path}]"),
    no_telemetry: bool = typer.Option(True, "--no-telemetry", help="Disable telemetry during eval runs (default: True)."),
):
    """Batch evaluate Nova across multiple repositories.

    The YAML file should contain a list of entries: [{name: str, repo_path: str}].
    """
    import yaml

    settings = get_settings()
    try:
        data = yaml.safe_load(repos.read_text(encoding="utf-8"))
    except Exception as e:
        console.print(f"[red]Failed to read YAML:[/red] {e}")
        raise typer.Exit(2)

    if not isinstance(data, list):
        console.print("[red]Invalid YAML format[/red]: expected a list of items")
        raise typer.Exit(2)

    results = []
    successes = 0
    total = 0

    out_dir = Path("evals/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"{ts}.json"

    for item in data:
        name = item.get("name")
        repo_path = Path(item.get("repo_path", ".")).resolve()
        if not name or not repo_path.exists():
            console.print(f"[yellow]Skipping invalid item[/yellow]: {item}")
            continue
        console.print(Panel.fit(f"Evaluating {name}\n{repo_path}", title="Eval"))

        logger = JSONLLogger(settings, enabled=not no_telemetry)
        logger.start_run(repo_path)
        run_agent = build_agent(settings=settings, logger=logger)

        try:
            summary = run_agent(repo_path)
            success = bool(summary.get("success"))
            results.append({
                "name": name,
                "repo_path": str(repo_path),
                **summary,
            })
            if success:
                successes += 1
            total += 1
            logger.end_run(success=success, summary=summary)
        except Exception as e:
            results.append({
                "name": name,
                "repo_path": str(repo_path),
                "success": False,
                "error": str(e),
            })
            total += 1
            logger.end_run(success=False, summary={"error": str(e)})

    overall = {
        "timestamp": ts,
        "success_rate": (successes / total) if total else 0.0,
        "successes": successes,
        "total": total,
        "results": results,
    }
    out_path.write_text(json.dumps(overall, indent=2), encoding="utf-8")
    console.print(Panel.fit(f"Eval complete. Results -> {out_path}", title="Eval"))


if __name__ == "__main__":
    app()
