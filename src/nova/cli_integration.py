"""
CLI Integration for Nova Deep Agent
====================================

Integration snippet showing how to use the new NovaDeepAgent in the CLI.
This replaces the existing multi-node iteration loop.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import os

from rich.console import Console
from rich.table import Table

from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger
from nova.tools.git import GitBranchManager
from nova.runner.test_runner import TestRunner
from nova.agent.deep_agent import NovaDeepAgent


def run_deep_agent_fix(
    repo_path: Path,
    state: AgentState,
    telemetry: JSONLLogger,
    runner: TestRunner,
    git_manager: Optional[GitBranchManager] = None,
    safety_conf: Optional[Any] = None,
    verbose: bool = False,
    console: Optional[Console] = None
) -> bool:
    """
    Run the deep agent to fix failing tests.
    
    This replaces the existing multi-node iteration loop in the CLI.
    
    Args:
        repo_path: Path to the repository
        state: Agent state tracking failures
        telemetry: Telemetry logger
        runner: Test runner for formatting failures
        git_manager: Git branch manager
        safety_conf: Safety configuration
        verbose: Enable verbose output
        console: Rich console for output
        
    Returns:
        True if all tests were fixed, False otherwise
    """
    if not console:
        console = Console()
    
    # Get initial failing tests
    failing_tests = state.failing_tests
    
    if not failing_tests:
        console.print("[green]✅ No failing tests found! Repository is already green.[/green]")
        state.final_status = "success"
        return True
    
    console.print(f"\n[bold red]Found {len(failing_tests)} failing test(s):[/bold red]")
    
    # Display failing tests table
    table = Table(title="Failing Tests", show_header=True, header_style="bold magenta")
    table.add_column("Test", style="cyan", no_wrap=True)
    table.add_column("Error", style="red")
    
    for test in failing_tests[:10]:  # Show max 10 tests
        test_name = test.test_name if hasattr(test, 'test_name') else str(test)
        error_msg = test.short_error if hasattr(test, 'short_error') else "Unknown error"
        table.add_row(test_name, error_msg)
    
    if len(failing_tests) > 10:
        table.add_row("...", f"({len(failing_tests) - 10} more)")
    
    console.print(table)
    
    # Prepare context strings for the agent prompt
    failures_table = runner.format_failures_table(failing_tests) if hasattr(runner, 'format_failures_table') else str(failing_tests)
    
    # Get error details from first 3 failing tests
    error_details = []
    for test in failing_tests[:3]:
        if hasattr(test, 'short_traceback'):
            error_details.append(test.short_traceback)
        elif hasattr(test, 'error'):
            error_details.append(str(test.error))
    error_details_str = "\n\n".join(error_details)
    
    # Code snippets (could gather relevant source code if available)
    code_snippets = ""  # Leave empty for now, could be enhanced
    
    # Initialize and run the new deep agent
    console.print("\n[bold]Initializing Nova Deep Agent...[/bold]")
    
    deep_agent = NovaDeepAgent(
        state=state,
        telemetry=telemetry,
        git_manager=git_manager,
        verbose=verbose,
        safety_config=safety_conf
    )
    
    console.print("[cyan]🤖 Running Deep Agent to fix failing tests...[/cyan]")
    
    success = deep_agent.run(
        failures_summary=failures_table,
        error_details=error_details_str,
        code_snippets=code_snippets
    )
    
    # After agent execution, print summary
    if success:
        console.print("\n[green bold]✅ SUCCESS - All tests fixed![/green bold]")
        state.final_status = "success"
    else:
        console.print(f"\n[red bold]❌ FAILED - Could not fix all tests[/red bold]")
        if state.final_status == "max_iters":
            console.print(f"[yellow]Reached maximum iterations ({state.max_iterations})[/yellow]")
        elif state.final_status == "error":
            console.print("[red]An error occurred during execution[/red]")
    
    # Log completion
    telemetry.log_event("completion", {
        "status": state.final_status,
        "iterations": state.current_iteration,
        "total_patches": len(state.patches_applied),
        "final_failures": state.total_failures
    })
    
    return success


def print_exit_summary(state: AgentState, status: str):
    """Print a summary of the agent run on exit."""
    console = Console()
    
    console.print("\n" + "═" * 60)
    console.print("[bold]Nova CI-Rescue Deep Agent Summary[/bold]")
    console.print("═" * 60)
    
    # Status with appropriate color
    status_color = "green" if status == "success" else "red" if "error" in status else "yellow"
    console.print(f"Status: [{status_color}]{status}[/{status_color}]")
    
    # Statistics
    console.print(f"Iterations: {state.current_iteration}/{state.max_iterations}")
    console.print(f"Patches Applied: {len(state.patches_applied)}")
    console.print(f"Final Failures: {state.total_failures}")
    
    if state.patches_applied:
        console.print("\nPatches Applied:")
        for i, patch in enumerate(state.patches_applied, 1):
            console.print(f"  {i}. Iteration {patch.get('iteration', 'unknown')}")
            if patch.get('files_changed'):
                console.print(f"     Files: {', '.join(patch['files_changed'])}")
    
    console.print("═" * 60)
