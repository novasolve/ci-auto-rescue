#!/usr/bin/env python3
"""
Nova CI-Rescue CLI interface.
"""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table

from nova.runner import TestRunner
from nova.agent import AgentState
from nova.telemetry.logger import JSONLLogger
from nova.config import NovaSettings

app = typer.Typer(
    name="nova",
    help="Nova CI-Rescue: Automated test fixing agent",
    add_completion=False,
)
console = Console()


@app.command()
def fix(
    repo_path: Path = typer.Argument(
        Path("."),
        help="Path to repository to fix",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    max_iters: int = typer.Option(
        6,
        "--max-iters",
        "-i",
        help="Maximum number of fix iterations",
        min=1,
        max=20,
    ),
    timeout: int = typer.Option(
        1200,
        "--timeout",
        "-t",
        help="Overall timeout in seconds",
        min=60,
        max=7200,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
):
    """
    Fix failing tests in a repository.
    """
    console.print(f"[green]Nova CI-Rescue[/green] 🚀")
    console.print(f"Repository: {repo_path}")
    console.print(f"Max iterations: {max_iters}")
    console.print(f"Timeout: {timeout}s")
    console.print()
    
    # Initialize settings and telemetry
    settings = NovaSettings()
    telemetry = JSONLLogger(settings, enabled=True)
    telemetry.start_run(repo_path)
    
    # Initialize agent state
    state = AgentState(
        repo_path=repo_path,
        max_iterations=max_iters,
        timeout_seconds=timeout,
    )
    
    # Step 1: Run tests to identify failures (A1 - Seed failing tests into Planner)
    runner = TestRunner(repo_path, verbose=verbose)
    failing_tests = runner.run_tests(max_failures=5)
    
    # Store failures in agent state
    state.add_failing_tests(failing_tests)
    
    # Log the test discovery
    telemetry.log_event("test_discovery", {
        "total_failures": state.total_failures,
        "failing_tests": state.failing_tests,
    })
    
    # Check if there are any failures (AC: If zero failures → exit 0 with "No failing tests")
    if not failing_tests:
        console.print("[green]✅ No failing tests found! Repository is already green.[/green]")
        state.final_status = "success"
        telemetry.log_event("completion", {"status": "no_failures"})
        telemetry.end_run(success=True)
        raise typer.Exit(0)
    
    # Display failing tests table
    console.print(f"\n[bold red]Found {len(failing_tests)} failing test(s):[/bold red]")
    
    table = Table(title="Failing Tests", show_header=True, header_style="bold magenta")
    table.add_column("Test Name", style="cyan", no_wrap=False)
    table.add_column("Location", style="yellow")
    table.add_column("Error", style="red", no_wrap=False)
    
    for test in failing_tests:
        location = f"{test.file}:{test.line}" if test.line > 0 else test.file
        error_preview = test.short_traceback.split('\n')[0][:60]
        if len(test.short_traceback.split('\n')[0]) > 60:
            error_preview += "..."
        table.add_row(test.name, location, error_preview)
    
    console.print(table)
    console.print()
    
    # Prepare planner context (AC: Planner prompt contains failing tests table)
    planner_context = state.get_planner_context()
    failures_table = runner.format_failures_table(failing_tests)
    
    if verbose:
        console.print("[dim]Planner context prepared with failing tests:[/dim]")
        console.print(failures_table)
        console.print()
    
    # TODO: Implement the actual agent loop (planner, actor, critic, apply, test, reflect)
    console.print("[yellow]⚠️  Agent loop not yet implemented. Stopping here.[/yellow]")
    console.print("[dim]Next steps: Implement planner → actor → critic → apply → test → reflect loop[/dim]")
    
    # Log completion
    state.final_status = "not_implemented"
    telemetry.log_event("completion", {
        "status": state.final_status,
        "iterations": state.current_iteration,
    })
    telemetry.end_run(success=False)
    
    raise typer.Exit(1)


@app.command()
def eval(
    repos_file: Path = typer.Argument(
        ...,
        help="YAML file containing repositories to evaluate",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    output_dir: Path = typer.Option(
        Path("./evals/results"),
        "--output",
        "-o",
        help="Directory for evaluation results",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
):
    """
    Evaluate Nova on multiple repositories.
    """
    console.print(f"[green]Nova CI-Rescue Evaluation[/green] 📊")
    console.print(f"Repos file: {repos_file}")
    console.print(f"Output directory: {output_dir}")
    
    # TODO: Implement the actual eval logic
    console.print("[yellow]Eval command not yet implemented[/yellow]")
    raise typer.Exit(1)


@app.command()
def version():
    """
    Show Nova CI-Rescue version.
    """
    console.print("[green]Nova CI-Rescue[/green] v0.1.0")


if __name__ == "__main__":
    app()
