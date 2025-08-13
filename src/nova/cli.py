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
        
        # Set branch info in AgentState for reference
        state.branch_name = branch_name
        state.original_commit = git_manager._get_current_head()
        
        # Import our apply patch node
        from nova.nodes.apply_patch import apply_patch
        
        # Agent loop: iterate until tests are fixed or limits reached
        console.print("\n[bold]Starting agent loop...[/bold]")
        
        while state.increment_iteration():
            iteration = state.current_iteration
            console.print(f"\n[blue]━━━ Iteration {iteration}/{state.max_iterations} ━━━[/blue]")
            
            # 1. PLANNER: Generate a plan based on failing tests
            console.print(f"[cyan]🧠 Planning fix for {state.total_failures} failing test(s)...[/cyan]")
            # TODO: Implement actual planner logic
            # For now, using placeholder
            plan = {
                "approach": "Fix failing assertions",
                "target_tests": state.failing_tests[:2] if len(state.failing_tests) > 2 else state.failing_tests
            }
            telemetry.log_event("planner", {
                "iteration": iteration,
                "plan": plan,
                "failing_tests": state.total_failures
            })
            
            # 2. ACTOR: Generate a patch diff based on the plan
            console.print(f"[cyan]🎭 Generating patch...[/cyan]")
            # TODO: Implement actual actor logic with LLM
            # For now, using a mock patch for demonstration
            if iteration == 1:
                # Mock patch - in real implementation, this would come from LLM
                patch_diff = """--- a/test_sample.py
+++ b/test_sample.py
@@ -1,5 +1,5 @@
 def test_example():
-    assert False  # This will fail
+    assert True  # Fixed
     
 def test_another():
     pass
"""
            else:
                # No more patches for subsequent iterations in mock
                patch_diff = None
            
            if not patch_diff:
                console.print("[yellow]No patch generated. Stopping.[/yellow]")
                state.final_status = "no_patch"
                telemetry.log_event("actor_failed", {"iteration": iteration})
                break
            
            telemetry.log_event("actor", {
                "iteration": iteration,
                "patch_size": len(patch_diff.split('\n'))
            })
            
            # 3. CRITIC: Review and approve/reject the patch
            console.print(f"[cyan]🔍 Reviewing patch...[/cyan]")
            # TODO: Implement actual critic logic with LLM review
            # For now, auto-approve if patch is reasonable size
            patch_lines = patch_diff.split('\n')
            patch_approved = len(patch_lines) < 1000  # Simple size check
            
            if not patch_approved:
                console.print(f"[yellow]Patch rejected by critic at iteration {iteration}. Stopping.[/yellow]")
                state.final_status = "patch_rejected"
                telemetry.log_event("critic_rejected", {
                    "iteration": iteration,
                    "reason": "patch_too_large"
                })
                break
            
            console.print("[green]✓ Patch approved by critic[/green]")
            telemetry.log_event("critic_approved", {"iteration": iteration})
            
            # 4. APPLY PATCH: Apply the approved patch and commit
            console.print(f"[cyan]📝 Applying patch...[/cyan]")
            
            # Use our ApplyPatchNode to apply and commit the patch
            result = apply_patch(state, patch_diff, git_manager, verbose=verbose)
            
            if not result["success"]:
                console.print(f"[red]Failed to apply patch at iteration {iteration}[/red]")
                state.final_status = "patch_error"
                telemetry.log_event("patch_error", {
                    "iteration": iteration,
                    "step": result.get("step_number", 0)
                })
                break
            
            # Log successful patch application
            console.print(f"[green]✓ Patch applied and committed (step {result['step_number']})[/green]")
            telemetry.log_event("patch_applied", {
                "iteration": iteration,
                "step": result["step_number"],
                "files_changed": result["changed_files"],
                "commit": git_manager._get_current_head()
            })
            
            # Save patch artifact for auditing
            telemetry.save_artifact(f"diffs/step-{result['step_number']}.diff", patch_diff)
            
            # 5. RUN TESTS: Check if the patch fixed the failures
            console.print(f"[cyan]🧪 Running tests after patch...[/cyan]")
            new_failures = runner.run_tests(max_failures=5)
            
            # Update state with new test results
            previous_failures = state.total_failures
            state.add_failing_tests(new_failures)
            state.test_results.append({
                "iteration": iteration,
                "failures_before": previous_failures,
                "failures_after": state.total_failures
            })
            
            telemetry.log_event("test_results", {
                "iteration": iteration,
                "failures_before": previous_failures,
                "failures_after": state.total_failures,
                "fixed": previous_failures - state.total_failures
            })
            
            # 6. REFLECT: Check if we should continue or stop
            if state.total_failures == 0:
                # All tests passed - success!
                console.print(f"\n[bold green]✅ All tests passing! Fixed in {iteration} iteration(s).[/bold green]")
                state.final_status = "success"
                success = True
                break
            
            # Check if we made progress
            if state.total_failures < previous_failures:
                console.print(f"[green]Progress: Fixed {previous_failures - state.total_failures} test(s)[/green]")
            else:
                console.print(f"[yellow]No progress: {state.total_failures} test(s) still failing[/yellow]")
            
            # Check timeout
            if state.check_timeout():
                console.print("\n[red]⏰ Timeout reached. Stopping agent loop.[/red]")
                state.final_status = "timeout"
                break
            
            # Check if we're at max iterations
            if iteration >= state.max_iterations:
                console.print(f"\n[red]🚫 Max iterations ({state.max_iterations}) reached.[/red]")
                state.final_status = "max_iters"
                break
            
            # Continue to next iteration
            console.print(f"[dim]Continuing to iteration {iteration + 1}...[/dim]")
        
        # Log final completion status
        telemetry.log_event("completion", {
            "status": state.final_status,
            "iterations": state.current_iteration,
            "total_patches": len(state.patches_applied),
            "final_failures": state.total_failures
        })
        telemetry.end_run(success=success)
        
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
