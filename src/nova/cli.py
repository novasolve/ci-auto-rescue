#!/usr/bin/env python3
"""
Nova CI-Rescue CLI interface.
"""

import typer
import subprocess
import time
from pathlib import Path
from typing import Optional
from datetime import datetime
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


def print_exit_summary(state: AgentState, reason: str, elapsed_seconds: float = None) -> None:
    """
    Print a comprehensive summary when exiting the agent loop.
    
    Args:
        state: The current agent state
        reason: The reason for exit (timeout, max_iters, success, etc.)
        elapsed_seconds: Optional elapsed time in seconds
    """
    console.print("\n" + "=" * 60)
    console.print("[bold]EXECUTION SUMMARY[/bold]")
    console.print("=" * 60)
    
    # Exit reason with appropriate styling
    if reason == "success":
        console.print(f"[bold green]✅ Exit Reason: SUCCESS - All tests passing![/bold green]")
    elif reason == "timeout":
        console.print(f"[bold red]⏰ Exit Reason: TIMEOUT - Exceeded {state.timeout_seconds}s limit[/bold red]")
    elif reason == "max_iters":
        console.print(f"[bold red]🔄 Exit Reason: MAX ITERATIONS - Reached {state.max_iterations} iterations[/bold red]")
    elif reason == "no_patch":
        console.print(f"[bold yellow]⚠️ Exit Reason: NO PATCH - Could not generate fix[/bold yellow]")
    elif reason == "patch_rejected":
        console.print(f"[bold yellow]⚠️ Exit Reason: PATCH REJECTED - Critic rejected patch[/bold yellow]")
    elif reason == "patch_error":
        console.print(f"[bold red]❌ Exit Reason: PATCH ERROR - Failed to apply patch[/bold red]")
    elif reason == "interrupted":
        console.print(f"[bold yellow]🛑 Exit Reason: INTERRUPTED - User cancelled operation[/bold yellow]")
    elif reason == "error":
        console.print(f"[bold red]❌ Exit Reason: ERROR - Unexpected error occurred[/bold red]")
    else:
        console.print(f"[bold yellow]Exit Reason: {reason.upper()}[/bold yellow]")
    
    console.print()
    
    # Statistics
    console.print("[bold]Statistics:[/bold]")
    console.print(f"  • Iterations completed: {state.current_iteration}/{state.max_iterations}")
    console.print(f"  • Patches applied: {len(state.patches_applied)}")
    console.print(f"  • Initial failures: {state.initial_failures}")
    console.print(f"  • Remaining failures: {state.total_failures}")
    
    if state.total_failures == 0:
        console.print(f"  • [green]All tests fixed successfully![/green]")
    elif state.failing_tests and state.total_failures < len(state.failing_tests):
        fixed = len(state.failing_tests) - state.total_failures
        console.print(f"  • Tests fixed: {fixed}/{len(state.failing_tests)}")
    
    if elapsed_seconds is not None:
        minutes, seconds = divmod(int(elapsed_seconds), 60)
        console.print(f"  • Time elapsed: {minutes}m {seconds}s")
    elif hasattr(state, 'start_time') and state.start_time:
        # Handle both datetime and float start_time
        if isinstance(state.start_time, float):
            elapsed = time.time() - state.start_time
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
        telemetry = JSONLLogger(settings, enabled=settings.enable_telemetry)
        if settings.enable_telemetry:
            telemetry.start_run(repo_path)
        
        # Initialize agent state
        state = AgentState(
            repo_path=repo_path,
            max_iterations=max_iters,
            timeout_seconds=timeout,
        )
        state.start_time = datetime.now()  # Track start time for PR generation
        
        # Step 1: Run tests to identify failures (A1 - seed failing tests into planner)
        runner = TestRunner(repo_path, verbose=verbose)
        failing_tests, initial_junit_xml = runner.run_tests(max_failures=5)
        
        # Save initial test report
        if initial_junit_xml:
            telemetry.save_test_report(0, initial_junit_xml, report_type="junit")
        
        # Store failures in agent state
        state.add_failing_tests(failing_tests)
        
        # Log the test discovery event
        telemetry.log_event("test_discovery", {
            "total_failures": state.total_failures,
            "failing_tests": state.failing_tests,
            "initial_report_saved": initial_junit_xml is not None
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
        
        # Initialize the LLM agent (enhanced version with full Planner/Actor/Critic)
        try:
            from nova.agent.llm_agent_enhanced import EnhancedLLMAgent
            llm_agent = EnhancedLLMAgent(repo_path)
            
            # Determine which model we're using
            model_name = settings.default_llm_model
            if "gpt" in model_name.lower():
                console.print(f"[dim]Using OpenAI {model_name} for autonomous test fixing[/dim]")
            elif "claude" in model_name.lower():
                console.print(f"[dim]Using Anthropic {model_name} for autonomous test fixing[/dim]")
            else:
                console.print(f"[dim]Using {model_name} for autonomous test fixing[/dim]")
                
        except ImportError as e:
            console.print(f"[yellow]Warning: Could not import enhanced LLM agent: {e}[/yellow]")
            console.print("[yellow]Falling back to basic LLM agent[/yellow]")
            try:
                from nova.agent.llm_agent import LLMAgent
                llm_agent = LLMAgent(repo_path)
            except Exception as e2:
                console.print(f"[yellow]Warning: Could not initialize LLM agent: {e2}[/yellow]")
                console.print("[yellow]Falling back to mock agent for demo[/yellow]")
                from nova.agent.mock_llm import MockLLMAgent
                llm_agent = MockLLMAgent(repo_path)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not initialize enhanced LLM agent: {e}[/yellow]")
            console.print("[yellow]Falling back to mock agent for demo[/yellow]")
            from nova.agent.mock_llm import MockLLMAgent
            llm_agent = MockLLMAgent(repo_path)
        
        # Agent loop: iterate until tests are fixed or limits reached
        console.print("\n[bold]Starting agent loop...[/bold]")
        
        while state.increment_iteration():
            iteration = state.current_iteration
            console.print(f"\n[blue]━━━ Iteration {iteration}/{state.max_iterations} ━━━[/blue]")
            
            # 1. PLANNER: Generate a plan based on failing tests
            console.print(f"[cyan]🧠 Planning fix for {state.total_failures} failing test(s)...[/cyan]")
            
            # Log planner start
            telemetry.log_event("planner_start", {
                "iteration": iteration,
                "failing_tests": state.total_failures
            })
            
            # Use LLM to create plan (with critic feedback if available)
            critic_feedback = getattr(state, 'critic_feedback', None) if iteration > 1 else None
            plan = llm_agent.create_plan(state.failing_tests, iteration, critic_feedback)
            
            # Store plan in state for reference
            state.plan = plan
            
            # Display plan summary
            if verbose:
                console.print("[dim]Plan created:[/dim]")
                console.print(f"  Approach: {plan.get('approach', 'Unknown')}")
                if plan.get('steps'):
                    console.print("  Steps:")
                    for i, step in enumerate(plan['steps'][:3], 1):
                        console.print(f"    {i}. {step}")
            
            # Log planner completion
            telemetry.log_event("planner_complete", {
                "iteration": iteration,
                "plan": plan,
                "failing_tests": state.total_failures
            })
            
            # 2. ACTOR: Generate a patch diff based on the plan
            console.print(f"[cyan]🎭 Generating patch based on plan...[/cyan]")
            
            # Log actor start
            telemetry.log_event("actor_start", {"iteration": iteration})
            
            # Generate patch with plan context and critic feedback if available
            patch_diff = llm_agent.generate_patch(state.failing_tests, iteration, plan=state.plan, critic_feedback=critic_feedback, state=state)
            
            if not patch_diff:
                console.print("[red]❌ Could not generate a patch[/red]")
                state.final_status = "no_patch"
                telemetry.log_event("actor_failed", {"iteration": iteration})
                break
            
            # Display patch info
            patch_lines = patch_diff.split('\n')
            if verbose:
                console.print(f"[dim]Generated patch: {len(patch_lines)} lines[/dim]")
            
            # Log actor completion
            telemetry.log_event("actor_complete", {
                "iteration": iteration,
                "patch_size": len(patch_lines)
            })
            # Save patch artifact (before apply, so we have it even if apply fails)
            telemetry.save_patch(state.current_step + 1, patch_diff)
            
            # 3. CRITIC: Review and approve/reject the patch
            console.print(f"[cyan]🔍 Reviewing patch with critic...[/cyan]")
            
            # Log critic start
            telemetry.log_event("critic_start", {"iteration": iteration})
            
            # Use LLM to review patch
            patch_approved, review_reason = llm_agent.review_patch(patch_diff, state.failing_tests)
            
            if verbose:
                console.print(f"[dim]Review result: {review_reason}[/dim]")
            
            if not patch_approved:
                console.print(f"[red]❌ Patch rejected: {review_reason}[/red]")
                # Store critic feedback for next iteration
                state.critic_feedback = review_reason
                telemetry.log_event("critic_rejected", {
                    "iteration": iteration,
                    "reason": review_reason
                })
                
                # Check if we have more iterations available
                if iteration < state.max_iterations:
                    console.print(f"[yellow]Will try a different approach in iteration {iteration + 1}...[/yellow]")
                    continue  # Try again with critic feedback
                else:
                    # Only set final status if we're out of iterations
                    state.final_status = "patch_rejected"
                    break
            
            console.print("[green]✓ Patch approved by critic[/green]")
            
            # Clear critic feedback since patch was approved
            state.critic_feedback = None
            
            # Log critic approval
            telemetry.log_event("critic_approved", {
                "iteration": iteration,
                "reason": review_reason
            })
            
            # 4. APPLY PATCH: Apply the approved patch and commit
            console.print(f"[cyan]📝 Applying patch...[/cyan]")
            
            # Use our ApplyPatchNode to apply and commit the patch
            result = apply_patch(state, patch_diff, git_manager, verbose=verbose)
            
            if not result["success"]:
                console.print(f"[red]❌ Failed to apply patch[/red]")
                state.final_status = "patch_error"
                telemetry.log_event("patch_error", {
                    "iteration": iteration,
                    "step": result.get("step_number", 0)
                })
                break
            else:
                # Log successful patch application (only if not already done by fallback)
                console.print(f"[green]✓ Patch applied and committed (step {result['step_number']})[/green]")
            telemetry.log_event("patch_applied", {
                "iteration": iteration,
                "step": result["step_number"],
                "files_changed": result["changed_files"],
                "commit": git_manager._get_current_head()
            })
            
            # Save patch artifact for auditing
            # The patch was already saved before apply, no need to save again
            
            # 5. RUN TESTS: Check if the patch fixed the failures
            console.print(f"[cyan]🧪 Running tests after patch...[/cyan]")
            new_failures, junit_xml = runner.run_tests(max_failures=5)
            
            # Save test report artifact
            if junit_xml:
                telemetry.save_test_report(result['step_number'], junit_xml, report_type="junit")
            
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
            telemetry.log_event("reflect_start", {
                "iteration": iteration,
                "failures_before": previous_failures,
                "failures_after": state.total_failures
            })
            
            if state.total_failures == 0:
                # All tests passed - success!
                console.print(f"\n[bold green]✅ All tests passing! Fixed in {iteration} iteration(s).[/bold green]")
                state.final_status = "success"
                success = True
                telemetry.log_event("reflect_complete", {
                    "iteration": iteration,
                    "decision": "success",
                    "reason": "all_tests_passing"
                })
                break
            
            # Check if we made progress
            if state.total_failures < previous_failures:
                fixed_count = previous_failures - state.total_failures
                console.print(f"[green]✓ Progress: Fixed {fixed_count} test(s), {state.total_failures} remaining[/green]")
            else:
                console.print(f"[yellow]⚠ No progress: {state.total_failures} test(s) still failing[/yellow]")
            
            # Check timeout
            if state.check_timeout():
                console.print(f"[red]⏰ Timeout reached ({state.timeout_seconds}s)[/red]")
                state.final_status = "timeout"
                telemetry.log_event("reflect_complete", {
                    "iteration": iteration,
                    "decision": "stop",
                    "reason": "timeout"
                })
                break
            
            # Check if we're at max iterations
            if iteration >= state.max_iterations:
                console.print(f"[red]🔄 Maximum iterations reached ({state.max_iterations})[/red]")
                state.final_status = "max_iters"
                telemetry.log_event("reflect_complete", {
                    "iteration": iteration,
                    "decision": "stop",
                    "reason": "max_iterations"
                })
                break
            
            # Continue to next iteration
            console.print(f"[dim]Continuing to iteration {iteration + 1}...[/dim]")
            telemetry.log_event("reflect_complete", {
                "iteration": iteration,
                "decision": "continue",
                "reason": "more_failures_to_fix"
            })
        
        # Print exit summary
        if state and state.final_status:
            print_exit_summary(state, state.final_status)
        
        # Log final completion status
        telemetry.log_event("completion", {
            "status": state.final_status,
            "iterations": state.current_iteration,
            "total_patches": len(state.patches_applied),
            "final_failures": state.total_failures
        })
        telemetry.end_run(success=success)
        
    except KeyboardInterrupt:
        if state:
            state.final_status = "interrupted"
            print_exit_summary(state, "interrupted")
        else:
            console.print("\n[yellow]Interrupted by user[/yellow]")
        if telemetry:
            telemetry.log_event("interrupted", {"reason": "keyboard_interrupt"})
        success = False
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        if state:
            state.final_status = "error"
            print_exit_summary(state, "error")
        if telemetry:
            telemetry.log_event("error", {"error": str(e)})
        success = False
    finally:
        # If successful, offer to create a PR
        pr_created = False
        if success and state and branch_name and git_manager:
            try:
                console.print("\n[bold green]✅ Success! Changes saved to branch:[/bold green] " + branch_name)
                
                # Ask if user wants to create a PR
                from nova.tools.pr_generator import PRGenerator
                pr_gen = PRGenerator(repo_path)
                
                # Check if PR already exists
                if pr_gen.check_pr_exists(branch_name):
                    console.print("[yellow]A PR already exists for this branch[/yellow]")
                else:
                    console.print("\n[cyan]🤖 Using GPT-5 to generate a pull request...[/cyan]")
                    
                    # Calculate execution time
                    elapsed_time = (datetime.now() - state.start_time).total_seconds() if hasattr(state, 'start_time') else 0
                    minutes, seconds = divmod(int(elapsed_time), 60)
                    execution_time = f"{minutes}m {seconds}s"
                    
                    # Get fixed tests and changed files
                    # Use initial_failing_tests for PR generation (what we originally fixed)
                    fixed_tests = state.initial_failing_tests if state.initial_failing_tests else []
                    changed_files = []
                    
                    # Get list of changed files from git
                    try:
                        result = subprocess.run(
                            ["git", "diff", "--name-only", "HEAD~" + str(len(state.patches_applied))],
                            capture_output=True,
                            text=True,
                            cwd=repo_path
                        )
                        if result.returncode == 0:
                            changed_files = [f for f in result.stdout.strip().split('\n') if f]
                    except:
                        pass
                    
                    # Gather reasoning logs from telemetry
                    reasoning_logs = []
                    if telemetry and hasattr(telemetry, 'events'):
                        reasoning_logs = telemetry.events
                    elif telemetry:
                        # Try to read from telemetry files
                        try:
                            telemetry_dir = Path(repo_path) / ".nova"
                            if telemetry_dir.exists():
                                # Get the most recent run directory
                                run_dirs = sorted([d for d in telemetry_dir.iterdir() if d.is_dir()], 
                                                key=lambda x: x.stat().st_mtime, reverse=True)
                                if run_dirs:
                                    trace_file = run_dirs[0] / "trace.jsonl"
                                    if trace_file.exists():
                                        import json
                                        with open(trace_file) as f:
                                            for line in f:
                                                try:
                                                    reasoning_logs.append(json.loads(line))
                                                except:
                                                    pass
                        except Exception as e:
                            print(f"[yellow]Could not read reasoning logs: {e}[/yellow]")
                    
                    # Generate PR content using GPT-5
                    console.print("[dim]Generating PR title and description...[/dim]")
                    title, description = pr_gen.generate_pr_content(
                        fixed_tests=fixed_tests,
                        patches_applied=state.patches_applied,
                        changed_files=changed_files,
                        execution_time=execution_time,
                        reasoning_logs=reasoning_logs
                    )
                    
                    console.print(f"\n[bold]PR Title:[/bold] {title}")
                    console.print(f"\n[bold]PR Description:[/bold]")
                    console.print(description[:500] + "..." if len(description) > 500 else description)
                    
                    # Push the branch first
                    console.print("\n[cyan]Pushing branch to remote...[/cyan]")
                    push_result = subprocess.run(
                        ["git", "push", "origin", branch_name],
                        capture_output=True,
                        text=True,
                        cwd=repo_path
                    )
                    
                    if push_result.returncode != 0:
                        console.print(f"[yellow]Warning: Failed to push branch: {push_result.stderr}[/yellow]")
                        console.print("[dim]Attempting to create PR anyway...[/dim]")
                    
                    # Create the PR
                    console.print("\n[cyan]Creating pull request...[/cyan]")
                    success_pr, pr_url_or_error = pr_gen.create_pr(
                        branch_name=branch_name,
                        title=title,
                        description=description,
                        base_branch="main",  # Could make this configurable
                        draft=False
                    )
                    
                    if success_pr:
                        console.print(f"\n[bold green]🎉 Pull Request created successfully![/bold green]")
                        console.print(f"[link={pr_url_or_error}]{pr_url_or_error}[/link]")
                        pr_created = True
                    else:
                        console.print(f"\n[yellow]Could not create PR: {pr_url_or_error}[/yellow]")
                        console.print(f"[dim]You can manually create a PR from branch: {branch_name}[/dim]")
                        
            except Exception as e:
                console.print(f"\n[yellow]Error creating PR: {e}[/yellow]")
                console.print(f"[dim]You can manually create a PR from branch: {branch_name}[/dim]")
        
        # Clean up branch and restore original state (unless PR was created)
        if git_manager and branch_name:
            if pr_created:
                # Don't delete the branch if we created a PR
                git_manager.cleanup(success=False)  # This will keep the branch
                console.print(f"\n[dim]Branch '{branch_name}' preserved for PR[/dim]")
            else:
                git_manager.cleanup(success=success)
            git_manager.restore_signal_handler()
        # Ensure telemetry run is ended if not already done
        if telemetry and not success and (state is None or state.final_status is None):
            telemetry.end_run(success=False)
        # Exit with appropriate code (0 for success, 1 for failure)
        raise SystemExit(0 if success else 1)


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






