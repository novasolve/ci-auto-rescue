#!/usr/bin/env python3
"""
Nova CI-Rescue Enhanced CLI with full telemetry.
Uses modular nodes for each stage of the agent loop.
"""

import os
import typer
from pathlib import Path
from typing import Optional
from datetime import datetime
from rich.console import Console
from rich.table import Table

from nova.agent import AgentState
from nova.telemetry.logger import JSONLLogger
from nova.config import NovaSettings
from nova.tools.git import GitBranchManager
from nova.tools.safety_limits import SafetyLimits
from nova.nodes import (
    PlannerNode,
    ActorNode,
    CriticNode,
    ApplyPatchNode,
    RunTestsNode,
    ReflectNode
)

app = typer.Typer(
    name="nova",
    help="Nova CI-Rescue: Automated test fixing agent with full telemetry",
    add_completion=False,
)
console = Console()


def print_exit_summary(state: AgentState, reason: str, elapsed_seconds: float = None) -> None:
    """Print a comprehensive summary when exiting the agent loop."""
    console.print("\n" + "=" * 60)
    console.print("[bold]EXECUTION SUMMARY[/bold]")
    console.print("=" * 60)
    
    # Exit reason with appropriate styling
    reason_map = {
        "success": ("[bold green]✅ Exit Reason: SUCCESS - All tests passing![/bold green]", True),
        "timeout": (f"[bold red]⏰ Exit Reason: TIMEOUT - Exceeded {state.timeout_seconds}s limit[/bold red]", False),
        "max_iters": (f"[bold red]🔄 Exit Reason: MAX ITERATIONS - Reached {state.max_iterations} iterations[/bold red]", False),
        "no_patch": ("[bold yellow]⚠️ Exit Reason: NO PATCH - Could not generate fix[/bold yellow]", False),
        "patch_rejected": ("[bold yellow]⚠️ Exit Reason: PATCH REJECTED - Critic rejected patch[/bold yellow]", False),
        "patch_error": ("[bold red]❌ Exit Reason: PATCH ERROR - Failed to apply patch[/bold red]", False),
        "interrupted": ("[bold yellow]🛑 Exit Reason: INTERRUPTED - User cancelled operation[/bold yellow]", False),
        "error": ("[bold red]❌ Exit Reason: ERROR - Unexpected error occurred[/bold red]", False),
        "no_progress": ("[bold yellow]⚠️ Exit Reason: NO PROGRESS - No improvement after multiple attempts[/bold yellow]", False),
    }
    
    message, is_success = reason_map.get(reason, (f"[bold yellow]Exit Reason: {reason.upper()}[/bold yellow]", False))
    console.print(message)
    console.print()
    
    # Statistics
    console.print("[bold]Statistics:[/bold]")
    console.print(f"  • Iterations completed: {state.current_iteration}/{state.max_iterations}")
    console.print(f"  • Patches applied: {len(state.patches_applied)}")
    console.print(f"  • Initial failures: {state.total_failures}")
    
    # Get current failure count from last test results
    current_failures = len(state.failing_tests) if state.failing_tests else 0
    console.print(f"  • Remaining failures: {current_failures}")
    
    if current_failures == 0:
        console.print(f"  • [green]All tests fixed successfully![/green]")
    elif state.total_failures > current_failures:
        fixed = state.total_failures - current_failures
        console.print(f"  • Tests fixed: {fixed}/{state.total_failures}")
    
    if elapsed_seconds is not None:
        minutes, seconds = divmod(int(elapsed_seconds), 60)
        console.print(f"  • Time elapsed: {minutes}m {seconds}s")
    else:
        elapsed = (datetime.now() - state.start_time).total_seconds()
        minutes, seconds = divmod(int(elapsed), 60)
        console.print(f"  • Time elapsed: {minutes}m {seconds}s")
    
    console.print("=" * 60)
    console.print()


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
    """Fix failing tests in a repository with full telemetry."""
    console.print(f"[green]Nova CI-Rescue Enhanced[/green] 🚀")
    console.print(f"Repository: {repo_path}")
    console.print(f"Max iterations: {max_iters}")
    console.print(f"Timeout: {timeout}s")
    console.print()
    
    # Initialize components
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
        run_id = telemetry.start_run(repo_path)
        console.print(f"[dim]Telemetry run ID: {run_id}[/dim]")
        console.print(f"[dim]Telemetry directory: {telemetry.run_dir}[/dim]")
        console.print()
        
        # Initialize agent state
        state = AgentState(
            repo_path=repo_path,
            max_iterations=max_iters,
            timeout_seconds=timeout,
            branch_name=branch_name,
            original_commit=git_manager._get_current_head()
        )
        
        # Initialize nodes
        planner_node = PlannerNode(verbose=verbose)
        actor_node = ActorNode(verbose=verbose)
        critic_node = CriticNode(verbose=verbose)
        apply_node = ApplyPatchNode(verbose=verbose)
        test_node = RunTestsNode(repo_path, verbose=verbose)
        reflect_node = ReflectNode(verbose=verbose)
        
        # Step 1: Initial test discovery
        console.print("[bold]Phase 1: Test Discovery[/bold]")
        console.print("[cyan]🔍 Discovering failing tests...[/cyan]")
        
        initial_results = test_node.execute(state, telemetry, step_number=0)
        
        # Log initial test discovery
        telemetry.log_event("test_discovery", {
            "total_failures": initial_results["failure_count"],
            "failing_tests": initial_results["failing_tests"][:10],  # First 10
            "junit_report_saved": initial_results.get("junit_report_saved", False)
        })
        
        # Check if there are any failures
        if initial_results["failure_count"] == 0:
            console.print("[green]✅ No failing tests found! Repository is already green.[/green]")
            state.final_status = "success"
            telemetry.log_event("completion", {"status": "no_failures"})
            telemetry.end_run(success=True)
            success = True
            return
        
        # Display failing tests in a table
        console.print(f"\n[bold red]Found {initial_results['failure_count']} failing test(s):[/bold red]")
        
        table = Table(title="Failing Tests", show_header=True, header_style="bold magenta")
        table.add_column("Test Name", style="cyan", no_wrap=False)
        table.add_column("Location", style="yellow")
        table.add_column("Error", style="red", no_wrap=False)
        
        for test in initial_results["failing_tests"][:5]:  # Show first 5
            location = f"{test['file']}:{test['line']}" if test.get('line', 0) > 0 else test['file']
            error_preview = test['short_traceback'].split('\n')[0][:60]
            if len(test['short_traceback'].split('\n')[0]) > 60:
                error_preview += "..."
            table.add_row(test['name'], location, error_preview)
        
        if initial_results['failure_count'] > 5:
            table.add_row("...", f"and {initial_results['failure_count'] - 5} more", "...")
        
        console.print(table)
        console.print()
        
        # Initialize LLM agent
        try:
            from nova.agent.llm_agent_enhanced import EnhancedLLMAgent
            llm_agent = EnhancedLLMAgent(repo_path)
            model_name = settings.default_llm_model
            console.print(f"[dim]Using {model_name} for autonomous test fixing[/dim]")
        except ImportError:
            console.print("[yellow]Warning: Could not import enhanced LLM agent[/yellow]")
            from nova.agent.llm_agent import LLMAgent
            llm_agent = LLMAgent(repo_path)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not initialize LLM agent: {e}[/yellow]")
            from nova.agent.mock_llm import MockLLMAgent
            llm_agent = MockLLMAgent(repo_path)
        
        # Agent loop
        console.print("\n[bold]Phase 2: Agent Loop[/bold]")
        
        while state.increment_iteration():
            iteration = state.current_iteration
            console.print(f"\n[blue]━━━ Iteration {iteration}/{state.max_iterations} ━━━[/blue]")
            
            # 1. PLANNER
            plan = planner_node.execute(state, llm_agent, telemetry, state.critic_feedback)
            
            # 2. ACTOR
            patch_diff = actor_node.execute(state, llm_agent, telemetry, plan)
            
            if not patch_diff:
                console.print("[red]❌ Could not generate a patch[/red]")
                state.final_status = "no_patch"
                break
            
            # Save patch artifact before critic review
            telemetry.save_patch(state.current_step + 1, patch_diff)
            
            # 3. CRITIC
            approved, reason = critic_node.execute(state, patch_diff, llm_agent, telemetry)
            
            if not approved:
                # Check if we have more iterations
                if iteration < state.max_iterations:
                    console.print(f"[yellow]Will try a different approach in iteration {iteration + 1}...[/yellow]")
                    continue
                else:
                    state.final_status = "patch_rejected"
                    break
            
            # 4. APPLY PATCH
            apply_result = apply_node.execute(state, patch_diff, git_manager)
            
            # Log patch application
            telemetry.log_event("patch_applied", {
                "iteration": iteration,
                "step": apply_result["step_number"],
                "success": apply_result["success"],
                "files_changed": apply_result.get("changed_files", [])
            })
            
            if not apply_result["success"]:
                console.print(f"[red]❌ Failed to apply patch[/red]")
                state.final_status = "patch_error"
                break
            
            # 5. RUN TESTS
            test_results = test_node.execute(state, telemetry, apply_result["step_number"])
            
            # 6. REFLECT
            should_continue, decision, metadata = reflect_node.execute(state, test_results, telemetry)
            
            if not should_continue:
                if decision == "success":
                    success = True
                break
        
        # Print exit summary
        if state and state.final_status:
            elapsed = (datetime.now() - state.start_time).total_seconds()
            print_exit_summary(state, state.final_status, elapsed)
        
        # Log final completion
        telemetry.log_event("completion", {
            "status": state.final_status,
            "iterations": state.current_iteration,
            "total_patches": len(state.patches_applied),
            "final_failures": len(state.failing_tests) if state.failing_tests else 0
        })
        
        # End telemetry run
        telemetry.end_run(success=success, summary={
            "run_id": run_id,
            "repo": str(repo_path),
            "status": state.final_status,
            "iterations": state.current_iteration,
            "patches_applied": len(state.patches_applied),
            "duration_seconds": (datetime.now() - state.start_time).total_seconds()
        })
        
        if success:
            console.print(f"\n[green]✨ Success! Check telemetry at: {telemetry.run_dir}[/green]")
        else:
            console.print(f"\n[yellow]📊 Telemetry saved at: {telemetry.run_dir}[/yellow]")
        
    except KeyboardInterrupt:
        if state:
            state.final_status = "interrupted"
            print_exit_summary(state, "interrupted")
        else:
            console.print("\n[yellow]Interrupted by user[/yellow]")
        if telemetry:
            telemetry.log_event("interrupted", {"reason": "keyboard_interrupt"})
            telemetry.end_run(success=False)
        success = False
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        if state:
            state.final_status = "error"
            print_exit_summary(state, "error")
        if telemetry:
            telemetry.log_event("error", {"error": str(e), "type": type(e).__name__})
            telemetry.end_run(success=False)
        success = False
    finally:
        # Clean up branch and restore original state
        if git_manager and branch_name:
            git_manager.cleanup(success=success)
            git_manager.restore_signal_handler()
        
        # Exit with appropriate code
        raise SystemExit(0 if success else 1)


@app.command()
def version():
    """Show Nova CI-Rescue version."""
    console.print("[green]Nova CI-Rescue Enhanced[/green] v0.2.0")


if __name__ == "__main__":
    app()
