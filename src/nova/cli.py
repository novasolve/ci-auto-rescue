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
from nova.tools.git import GitBranchManager

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
    
    # Initialize branch manager for nova-fix branch
    git_manager = GitBranchManager(repo_path, verbose=verbose)
    branch_name: Optional[str] = None
    success = False
    telemetry = None
    state = None
    
    try:
        # Create the nova-fix branch
        branch_name = git_manager.create_fix_branch()
        console.print(f"[dim]Working on branch: {branch_name}[/dim]")
        
        # Set up signal handler for Ctrl+C
        git_manager.setup_signal_handler()
        
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
        
        # Step 1: Run tests to identify failures (A1 - seed failing tests into planner)
        runner = TestRunner(repo_path, verbose=verbose)
        failing_tests = runner.run_tests(max_failures=5)
        
        # Store failures in agent state
        state.add_failing_tests(failing_tests)
        
        # Log the test discovery event
        telemetry.log_event("test_discovery", {
            "total_failures": state.total_failures,
            "failing_tests": state.failing_tests,
        })
        
        # Check if there are any failures (AC: if zero failures → exit 0 with message)
        if not failing_tests:
            console.print("[green]✅ No failing tests found! Repository is already green.[/green]")
            state.final_status = "success"
            telemetry.log_event("completion", {"status": "no_failures"})
            telemetry.end_run(success=True)
            success = True
            return
        
        # Display failing tests in a table
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
        
        # Prepare planner context (AC: planner prompt contains failing tests table)
        planner_context = state.get_planner_context()
        failures_table = runner.format_failures_table(failing_tests)
        
        if verbose:
            console.print("[dim]Planner context prepared with failing tests:[/dim]")
            console.print(failures_table)
            console.print()
        
        # TODO: Implement the actual agent loop (planner → actor → critic → apply → test → reflect)
        console.print("[yellow]⚠️  Agent loop not yet implemented. Stopping here.[/yellow]")
        console.print("[dim]Next steps: Implement planner → actor → critic → apply → test → reflect loop[/dim]")
        
        # Log completion status for not implemented scenario
        state.final_status = "not_implemented"
        telemetry.log_event("completion", {
            "status": state.final_status,
            "iterations": state.current_iteration,
        })
        telemetry.end_run(success=False)
        # (Agent loop not implemented; treat this run as unsuccessful for now)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        if telemetry:
            telemetry.log_event("interrupted", {"reason": "keyboard_interrupt"})
        success = False
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        if telemetry:
            telemetry.log_event("error", {"error": str(e)})
        success = False
    finally:
        # Clean up branch and restore original state
        if git_manager and branch_name:
            git_manager.cleanup(success=success)
            git_manager.restore_signal_handler()
        # Ensure telemetry run is ended if not already done
        if telemetry and not success and (state is None or state.final_status is None):
            telemetry.end_run(success=False)
        # Exit with error code 1 if the process did not succeed
        if not success:
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
