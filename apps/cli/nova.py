from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from nova.settings import get_settings
from nova.sdk import NovaAgent

app = typer.Typer(help="Nova CI-Rescue CLI")
console = Console()


@app.command()
def fix(
    repo_path: str = typer.Argument(..., help="Path to the target repository"),
    max_iters: int = typer.Option(None, help="Max iterations (default from settings)"),
    timeout: int = typer.Option(None, help="Global timeout seconds (default from settings)"),
    branch: Optional[str] = typer.Option(None, help="Branch name to create/switch to"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose console output"),
    no_telemetry: bool = typer.Option(False, "--no-telemetry", help="Disable local telemetry"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run the loop without applying edits or running tests"),
):
    console.log("Starting nova fix...")
    settings = get_settings()
    agent = NovaAgent(settings)
    summary = agent.run_fix(
        repo_path,
        max_iters=max_iters,
        timeout_s=timeout,
        branch_name=branch,
        telemetry_enabled=not no_telemetry,
        dry_run=dry_run,
    )
    console.log("Run complete.")
    table = Table(title="Nova fix summary")
    table.add_column("Field")
    table.add_column("Value")
    for k in ["success", "iterations", "duration_s", "files_changed", "branch_name"]:
        table.add_row(k, str(summary.get(k)))
    console.print(table)
    if verbose:
        console.print_json(data=summary)


@app.command()
def eval(
    repos: Path = typer.Option(..., "--repos", help="Path to repos.yaml"),
    max_iters: int = typer.Option(None, help="Max iterations per scenario"),
    timeout: int = typer.Option(None, help="Global timeout seconds per scenario"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Run scenarios in dry-run mode"),
):
    """Run batch evaluation across multiple scenarios.

    Expected YAML format:
    - name: scenario-name
      repo_path: /path/to/repo
      # optional: target_tests, seed_script
    """
    settings = get_settings()
    agent = NovaAgent(settings)
    try:
        scenarios = yaml.safe_load(Path(repos).read_text())
    except Exception as e:
        raise typer.BadParameter(f"Failed to read {repos}: {e}")
    if not isinstance(scenarios, list):
        raise typer.BadParameter("repos.yaml must be a list of scenarios")

    results = []
    start_all = time.time()
    for sc in scenarios:
        name = sc.get("name") or sc.get("repo_path")
        repo_path = sc.get("repo_path")
        if not repo_path:
            console.print(f"[yellow]Skipping scenario without repo_path: {name}")
            continue
        console.rule(f"Scenario: {name}")
        t0 = time.time()
        summary = agent.run_fix(repo_path, max_iters=max_iters, timeout_s=timeout, dry_run=dry_run)
        dt = time.time() - t0
        results.append({"name": name, **summary, "duration_s": dt})

    overall = {
        "scenarios": len(results),
        "fixed": sum(1 for r in results if r.get("success")),
        "success_rate": (sum(1 for r in results if r.get("success")) / max(1, len(results))) * 100.0,
        "duration_s": time.time() - start_all,
    }
    console.rule("Evaluation summary")
    table = Table()
    table.add_column("Scenario")
    table.add_column("Success")
    table.add_column("Iterations")
    table.add_column("Duration (s)")
    for r in results:
        table.add_row(r.get("name", ""), str(r.get("success")), str(r.get("iterations")), f"{r.get('duration_s'):.2f}")
    console.print(table)
    console.print(f"Success rate: {overall['success_rate']:.1f}% ({overall['fixed']}/{overall['scenarios']})")

    # Persist results
    out_dir = Path("evals/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"results_{ts}.json"
    out_path.write_text(json.dumps({"results": results, "overall": overall}, indent=2))
    console.print(f"Wrote results to {out_path}")


if __name__ == "__main__":
    app()

