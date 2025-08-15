#!/usr/bin/env python3
"""
Nova CI-Rescue CLI interface.
"""

import os
import re
import sys
import json
import yaml
import time
import subprocess
import tempfile
import typer
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
from rich.console import Console
from rich.table import Table

from nova.runner import TestRunner
from nova.agent import AgentState
from nova.telemetry.logger import JSONLLogger
from nova.config import NovaSettings, load_yaml_config
from nova.tools.git import GitBranchManager

app = typer.Typer(
    name="nova",
    help="Nova CI-Rescue: Automated test fixing agent",
    add_completion=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, 
        "--version", 
        "-V", 
        help="Show Nova version and exit",
        is_eager=True
    )
):
    """
    Nova CI-Rescue: Automated test fixing agent.
    
    Main callback to handle global options like --version.
    """
    if version:
        from nova import __version__
        console.print(f"[green]Nova CI-Rescue[/green] v{__version__}")
        raise typer.Exit()
    
    # If no command is provided and not --version, show help
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()


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
    console.print(f"  • Initial failures: {len(state.failing_tests) if state.failing_tests else 0}")
    console.print(f"  • Remaining failures: {state.total_failures}")
    
    if state.total_failures == 0:
        console.print(f"  • [green]All tests fixed successfully![/green]")
    elif state.failing_tests and state.total_failures < len(state.failing_tests):
        fixed = len(state.failing_tests) - state.total_failures
        console.print(f"  • Tests fixed: {fixed}/{len(state.failing_tests)}")
    
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
    max_iters: Optional[int] = typer.Option(
        None,
        "--max-iters",
        "-i",
        help="Maximum number of fix iterations (default: 6)",
        min=1,
        max=20,
    ),
    timeout: Optional[int] = typer.Option(
        None,
        "--timeout",
        "-t",
        help="Overall timeout in seconds (default: 1200)",
        min=60,
        max=7200,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to YAML configuration file (options in file are used unless overridden by CLI flags)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
):
    """
    Fix failing tests in a repository.
    """
    # Load configuration file if provided
    config_data = None
    if config_file is not None:
        try:
            config_data = load_yaml_config(config_file)
        except Exception as e:
            console.print(f"[red]Failed to load config: {e}[/red]")
            raise typer.Exit(1)
    
    # Override CLI defaults with config values if present
    if config_data and config_data.repo_path:
        default_repo = Path(".").resolve()
        if repo_path.resolve() == default_repo:
            repo_path = Path(config_data.repo_path)
    
    final_max_iters = max_iters if max_iters is not None else (config_data.max_iters if config_data and config_data.max_iters is not None else 6)
    final_timeout = timeout if timeout is not None else (config_data.timeout if config_data and config_data.timeout is not None else 1200)
    
    console.print(f"[green]Nova CI-Rescue[/green] 🚀")
    if config_file:
        console.print(f"[dim]Loaded configuration from {config_file}[/dim]")
    console.print(f"Repository: {repo_path}")
    console.print(f"Max iterations: {final_max_iters}")
    console.print(f"Timeout: {final_timeout}s")
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
        
        # Override model from config if provided
        if config_data and config_data.model:
            settings.default_llm_model = config_data.model
        
        telemetry = JSONLLogger(settings, enabled=True)
        telemetry.start_run(repo_path)
        
        # Initialize agent state
        state = AgentState(
            repo_path=repo_path,
            max_iterations=final_max_iters,
            timeout_seconds=final_timeout,
        )
        
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
            
            # Post to GitHub even when no tests to fix
            token = os.getenv("GITHUB_TOKEN")
            repo = os.getenv("GITHUB_REPOSITORY")
            pr_num = os.getenv("PR_NUMBER")
            
            # Try to auto-detect PR number if not provided
            if not pr_num:
                # Try GitHub Actions event number
                pr_num = os.getenv("GITHUB_EVENT_NUMBER")
                
                # Try to parse from GITHUB_REF (e.g., refs/pull/123/merge)
                if not pr_num:
                    github_ref = os.getenv("GITHUB_REF")
                    if github_ref and "pull/" in github_ref:
                        import re
                        match = re.search(r"pull/(\d+)/", github_ref)
                        if match:
                            pr_num = match.group(1)
                
                # Try to parse from GitHub event JSON
                if not pr_num:
                    event_path = os.getenv("GITHUB_EVENT_PATH")
                    if event_path and os.path.exists(event_path):
                        try:
                            import json
                            with open(event_path, "r") as f:
                                event_data = json.load(f)
                            if "pull_request" in event_data:
                                pr_num = str(event_data["pull_request"]["number"])
                        except:
                            pass
            
            if token and repo:
                try:
                    from nova.github_integration import GitHubAPI, RunMetrics, ReportGenerator
                    
                    api = GitHubAPI(token)
                    metrics = RunMetrics(
                        runtime_seconds=0,
                        iterations=0,
                        files_changed=0,
                        status="success",
                        tests_fixed=0,
                        tests_remaining=0,
                        initial_failures=0,
                        final_failures=0
                    )
                    
                    # Get SHA for check run
                    head_sha = git_manager._get_current_head() if git_manager else None
                    
                    if head_sha:
                        api.create_check_run(
                            repo=repo,
                            sha=head_sha,
                            name="CI-Auto-Rescue",
                            status="completed",
                            conclusion="success",
                            title="CI-Auto-Rescue: No failing tests",
                            summary="✅ No failing tests found - repository is already green!"
                        )
                        if verbose:
                            console.print("[dim]✅ Posted check run to GitHub[/dim]")
                    
                    if pr_num:
                        api.create_pr_comment(
                            repo=repo,
                            pr_number=int(pr_num),
                            body="## ✅ Nova CI-Rescue: No failing tests to fix! 🎉\n\nAll tests are passing."
                        )
                        if verbose:
                            console.print("[dim]✅ Posted PR comment to GitHub[/dim]")
                        
                except Exception as e:
                    if verbose:
                        console.print(f"[yellow]⚠️ GitHub reporting failed: {e}[/yellow]")
            
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
        from nova.tools.safety_limits import SafetyConfig
        
        # Prepare safety limits configuration from YAML config if provided
        safety_conf = None
        if config_data:
            custom_limits = False
            safety_conf_obj = SafetyConfig()
            
            if config_data.max_changed_lines is not None:
                safety_conf_obj.max_lines_changed = config_data.max_changed_lines
                custom_limits = True
            
            if config_data.max_changed_files is not None:
                safety_conf_obj.max_files_modified = config_data.max_changed_files
                custom_limits = True
            
            if config_data.blocked_paths:
                for pattern in config_data.blocked_paths:
                    if pattern not in safety_conf_obj.denied_paths:
                        safety_conf_obj.denied_paths.append(pattern)
                custom_limits = True
            
            if custom_limits:
                safety_conf = safety_conf_obj
        
        # Initialize the LLM agent (enhanced version with full Planner/Actor/Critic)
        try:
            from nova.agent.llm_agent import LLMAgent
            llm_agent = LLMAgent(repo_path)
            
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

            # Ensure a clean working tree before generating a new patch
            try:
                if git_manager:
                    git_manager._run_git_command("reset", "--hard", "HEAD")
                    git_manager._run_git_command("clean", "-fd")
                    if verbose:
                        console.print("[dim]Working tree reset to HEAD and cleaned[/dim]")
            except Exception as e:
                if verbose:
                    console.print(f"[yellow]Warning: pre-iteration reset failed: {e}[/yellow]")
            
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

            # Enforce a maximum of 10 steps in the plan
            try:
                if isinstance(plan, dict) and isinstance(plan.get('steps'), list):
                    if len(plan['steps']) > 10:
                        plan['steps'] = plan['steps'][:10]
            except Exception:
                # If plan structure is unexpected, proceed without trimming
                pass

            # Store plan in state for reference
            state.plan = plan
            
            # Display plan summary
            if verbose:
                console.print("[dim]Plan created:[/dim]")
                console.print(f"  Approach: {plan.get('approach', 'Unknown')}")
                if plan.get('steps'):
                    console.print("  Steps (max 10):")
                    for i, step in enumerate(plan['steps'][:10], 1):
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
            patch_diff = llm_agent.generate_patch(state.failing_tests, iteration, plan=state.plan, critic_feedback=critic_feedback)
            
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
            result = apply_patch(state, patch_diff, git_manager, verbose=verbose, safety_config=safety_conf)
            
            if not result["success"]:
                if result.get("safety_violation"):
                    console.print(f"[red]🛡️ Patch rejected due to safety limits[/red]")
                    state.final_status = "safety_violation"
                    telemetry.log_event("safety_violation", {
                        "iteration": iteration,
                        "step": result.get("step_number", 0),
                        "message": result.get("safety_message", "")
                    })
                else:
                    console.print(f"[red]❌ Failed to apply patch[/red]")
                    telemetry.log_event("patch_error", {
                        "iteration": iteration,
                        "step": result.get("step_number", 0)
                    })
                    # Retry logic on patch application failure (including preflight failure)
                    if iteration < state.max_iterations:
                        console.print("[yellow]Patch apply failed – resetting state and retrying...[/yellow]")
                        try:
                            if git_manager:
                                git_manager._run_git_command("reset", "--hard", "HEAD")
                                git_manager._run_git_command("clean", "-fd")
                        except Exception as e:
                            if verbose:
                                console.print(f"[red]Failed to reset state after patch error: {e}[/red]")
                        # Provide feedback to next iteration
                        state.critic_feedback = "Patch application failed (possible context mismatch)."
                        # Continue to next iteration
                        continue
                    else:
                        state.final_status = "patch_error"
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
                
                # Reset state if no progress was made (prevent accumulating bad changes)
                if state.patches_applied and git_manager:
                    console.print("[yellow]↩️ Rolling back last patch to reset state...[/yellow]")
                    try:
                        # Reset to previous commit
                        git_manager._run_git_command("reset", "--hard", "HEAD~1")
                        # Remove the last patch from history
                        if state.patches_applied:
                            state.patches_applied.pop()
                        console.print("[dim]State reset to clean baseline[/dim]")
                        telemetry.log_event("state_reset", {
                            "iteration": iteration,
                            "reason": "no_progress",
                            "failures": state.total_failures
                        })
                    except Exception as e:
                        console.print(f"[red]Failed to reset state: {e}[/red]")
            
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
        
        # Post to GitHub if environment variables are set
        token = os.getenv("GITHUB_TOKEN")
        repo = os.getenv("GITHUB_REPOSITORY")  # e.g. "owner/repo"
        pr_num = os.getenv("PR_NUMBER")
        
        # Try to auto-detect PR number if not provided
        if not pr_num:
            # Try GitHub Actions event number
            pr_num = os.getenv("GITHUB_EVENT_NUMBER")
            
            # Try to parse from GITHUB_REF (e.g., refs/pull/123/merge)
            if not pr_num:
                github_ref = os.getenv("GITHUB_REF")
                if github_ref and "pull/" in github_ref:
                    import re
                    match = re.search(r"pull/(\d+)/", github_ref)
                    if match:
                        pr_num = match.group(1)
            
            # Try to parse from GitHub event JSON
            if not pr_num:
                event_path = os.getenv("GITHUB_EVENT_PATH")
                if event_path and os.path.exists(event_path):
                    try:
                        import json
                        with open(event_path, "r") as f:
                            event_data = json.load(f)
                        if "pull_request" in event_data:
                            pr_num = str(event_data["pull_request"]["number"])
                    except:
                        pass
        
        if token and repo:
            try:
                from nova.github_integration import GitHubAPI, RunMetrics, ReportGenerator
                
                # Calculate metrics
                elapsed = (datetime.now() - state.start_time).total_seconds()
                
                # Count unique files changed across all patches
                files_changed = set()
                if state.patches_applied:
                    from nova.tools.safety_limits import SafetyLimits
                    safety = SafetyLimits()
                    for patch in state.patches_applied:
                        analysis = safety.analyze_patch(patch)
                        files_changed.update(analysis.files_modified | analysis.files_added)
                
                # Create metrics
                metrics = RunMetrics(
                    runtime_seconds=int(elapsed),
                    iterations=state.current_iteration,
                    files_changed=len(files_changed),
                    status="success" if success else (state.final_status or "failure"),
                    tests_fixed=len(state.failing_tests) - state.total_failures if state.failing_tests else 0,
                    tests_remaining=state.total_failures,
                    initial_failures=len(state.failing_tests) if state.failing_tests else 0,
                    final_failures=state.total_failures,
                    branch_name=branch_name
                )
                
                # Post to GitHub
                api = GitHubAPI(token)
                generator = ReportGenerator()
                
                # Get commit SHA
                head_sha = git_manager._get_current_head() if git_manager else None
                
                # Create check run
                if head_sha:
                    api.create_check_run(
                        repo=repo,
                        sha=head_sha,
                        name="CI-Auto-Rescue",
                        status="completed",
                        conclusion="success" if success else "failure",
                        title=f"CI-Auto-Rescue: {metrics.status.upper()}",
                        summary=generator.generate_check_summary(metrics)
                    )
                    if verbose:
                        console.print("[dim]✅ Posted check run to GitHub[/dim]")
                
                # Create/update PR comment
                if pr_num:
                    existing_id = api.find_pr_comment(repo, int(pr_num), "<!-- ci-auto-rescue-report -->")
                    if existing_id:
                        api.update_pr_comment(repo, existing_id, generator.generate_pr_comment(metrics))
                        if verbose:
                            console.print(f"[dim]✅ Updated existing PR comment[/dim]")
                    else:
                        api.create_pr_comment(repo, int(pr_num), generator.generate_pr_comment(metrics))
                        if verbose:
                            console.print(f"[dim]✅ Created new PR comment[/dim]")
                        
            except Exception as e:
                console.print(f"[yellow]⚠️ GitHub reporting failed: {e}[/yellow]")
                if verbose:
                    import traceback
                    console.print(f"[dim]{traceback.format_exc()}[/dim]")
        
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
        # Clean up branch and restore original state
        if git_manager and branch_name:
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
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to YAML config file (applied to each fix run; CLI flags override file settings)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
):
    """
    Evaluate Nova on multiple repositories.
    """
    # Load configuration file if provided
    config_data = None
    if config_file is not None:
        try:
            config_data = load_yaml_config(config_file)
        except Exception as e:
            console.print(f"[red]Failed to load config: {e}[/red]")
            raise typer.Exit(1)
    
    console.print(f"[green]Nova CI-Rescue Evaluation[/green] 📊")
    if config_file:
        console.print(f"[dim]Loaded configuration from {config_file}[/dim]")
    console.print(f"Repos file: {repos_file}")
    console.print(f"Output directory: {output_dir}")
    console.print()
    
    # Load repository list from YAML
    try:
        with open(repos_file, "r") as f:
            repos_data = yaml.safe_load(f)
    except Exception as e:
        console.print(f"[red]Failed to read YAML file: {e}[/red]")
        raise typer.Exit(1)
    
    # Handle both 'runs' key and direct list format
    if isinstance(repos_data, dict) and 'runs' in repos_data:
        repos_list = repos_data['runs']
    elif isinstance(repos_data, list):
        repos_list = repos_data
    else:
        console.print("[red]Invalid YAML format: expected a list of repository entries or dict with 'runs' key[/red]")
        raise typer.Exit(1)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    total_success = 0
    total_failed = 0
    
    # Create summary table
    summary_table = Table(title="Evaluation Results", show_header=True, header_style="bold magenta")
    summary_table.add_column("Repository", style="cyan", no_wrap=False)
    summary_table.add_column("Status", style="green")
    summary_table.add_column("Duration", style="yellow")
    summary_table.add_column("Iterations", style="blue")
    summary_table.add_column("Tests Fixed", style="magenta")
    
    for entry in repos_list:
        # Parse entry - support both string and dict format
        repo_url = None
        repo_path = None
        branch = None
        name = None
        temp_dir = None
        
        if isinstance(entry, str):
            # Simple string format - could be path or URL
            source = entry
            if source.startswith("http") or source.startswith("git@"):
                repo_url = source
                name = Path(source).stem  # Extract name from URL
            else:
                repo_path = Path(source)
                name = repo_path.name
        else:
            # Dictionary format with detailed config
            repo_url = entry.get("url")
            repo_path = entry.get("path") or entry.get("repo") or entry.get("repo_path")
            branch = entry.get("branch")
            name = entry.get("name")
            
            # Determine source
            if repo_url:
                if not name:
                    name = Path(repo_url).stem
            elif repo_path:
                repo_path = Path(repo_path)
                if not name:
                    name = repo_path.name
            else:
                console.print(f"[red]Invalid entry: must have 'url' or 'path'[/red]")
                continue
        
        max_iters = entry.get("max_iters", 6) if isinstance(entry, dict) else 6
        timeout = entry.get("timeout", 1200) if isinstance(entry, dict) else 1200
        
        # Clone repository if URL provided
        if repo_url:
            console.print(f"\n[bold]Cloning {name} from {repo_url}...[/bold]")
            temp_dir = tempfile.TemporaryDirectory(prefix=f"nova_eval_{name}_")
            clone_cmd = ["git", "clone", "--depth=1"]
            if branch:
                clone_cmd.extend(["-b", branch])
            clone_cmd.extend([repo_url, temp_dir.name])
            
            result = subprocess.run(clone_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                console.print(f"[red]❌ Failed to clone {name}: {result.stderr}[/red]")
                results.append({
                    "name": name,
                    "repo": repo_url,
                    "success": False,
                    "duration": 0,
                    "iterations": 0,
                    "tests_fixed": 0,
                    "initial_failures": 0,
                    "error": "clone_failed"
                })
                total_failed += 1
                if temp_dir:
                    temp_dir.cleanup()
                continue
            repo_path = Path(temp_dir.name)
        else:
            # Use local path
            if not repo_path.is_absolute():
                # Resolve relative paths relative to the YAML file location
                repo_path = (repos_file.parent / repo_path).resolve()
            
            # Check if local path exists
            if not repo_path.exists():
                console.print(f"[yellow]⚠️ Skipping {name}: path does not exist ({repo_path})[/yellow]")
                results.append({
                    "name": name,
                    "repo": str(repo_path),
                    "success": False,
                    "duration": 0,
                    "iterations": 0,
                    "tests_fixed": 0,
                    "initial_failures": 0,
                    "error": "path_not_found"
                })
                total_failed += 1
                continue
            
            # Checkout branch if specified for local repo
            if branch:
                checkout_cmd = ["git", "-C", str(repo_path), "checkout", branch]
                subprocess.run(checkout_cmd, capture_output=True)
        
        # Announce which repo is being processed
        console.print(f"\n[bold]Running Nova on [cyan]{name}[/cyan]...[/bold]")
        console.print(f"  Path: {repo_path}")
        console.print(f"  Max iterations: {max_iters}")
        console.print(f"  Timeout: {timeout}s")
        
        # Run the fix command and time its execution
        start_time = datetime.now(timezone.utc)
        
        # Run nova fix on this repository
        cmd = [
            sys.executable, "-m", "nova", "fix",
            str(repo_path),
            "--max-iters", str(max_iters),
            "--timeout", str(timeout)
        ]
        if config_file:
            cmd.extend(["--config", str(config_file)])
        if verbose:
            cmd.append("--verbose")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(Path.cwd())
        )
        
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        success_flag = (result.exit_code == 0)
        
        # Extract iteration count and tests fixed from output
        iter_count = 0
        tests_fixed = 0
        initial_failures = 0
        
        for line in result.stdout.splitlines():
            # Look for iteration count
            if "Iterations completed:" in line:
                try:
                    match = re.search(r"Iterations completed: (\d+)/(\d+)", line)
                    if match:
                        iter_count = int(match.group(1))
                except Exception:
                    pass
            # Look for initial failures
            if "Initial failures:" in line:
                try:
                    match = re.search(r"Initial failures: (\d+)", line)
                    if match:
                        initial_failures = int(match.group(1))
                except Exception:
                    pass
            # Look for tests fixed
            if "Tests fixed:" in line:
                try:
                    match = re.search(r"Tests fixed: (\d+)/(\d+)", line)
                    if match:
                        tests_fixed = int(match.group(1))
                except Exception:
                    pass
        
        # If we didn't find explicit tests fixed, calculate from initial failures if success
        if success_flag and initial_failures > 0 and tests_fixed == 0:
            tests_fixed = initial_failures
        
        # Print status for this repo
        status_text = "✅ SUCCESS" if success_flag else "❌ FAILED"
        console.print(f"• [yellow]{name}[/yellow]: {status_text} after {int(elapsed)}s, {iter_count} iteration(s)")
        
        # Add to summary table
        summary_table.add_row(
            name,
            "SUCCESS" if success_flag else "FAILED",
            f"{int(elapsed)}s",
            str(iter_count),
            str(tests_fixed)
        )
        
        # Update counters
        if success_flag:
            total_success += 1
        else:
            total_failed += 1
        
        # Append result metrics
        results.append({
            "name": name,
            "repo": repo_url or str(repo_path),
            "success": success_flag,
            "duration": elapsed,
            "iterations": iter_count,
            "tests_fixed": tests_fixed,
            "initial_failures": initial_failures,
            "max_iterations": max_iters,
            "timeout": timeout
        })
        
        # Clean up temporary directory if we cloned a repo
        if temp_dir:
            temp_dir.cleanup()
    
    # Save all results to a JSON file with UTC timestamp
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    results_path = output_dir / f"{timestamp}.json"
    with open(results_path, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "config_file": str(repos_file),
            "total_repos": len(results),
            "successful": total_success,
            "failed": total_failed,
            "results": results
        }, f, indent=2)
    
    # Print summary
    console.print("\n" + "="*60)
    console.print(summary_table)
    console.print("="*60)
    console.print(f"\n[bold]Evaluation Complete[/bold]")
    console.print(f"  Total repositories: {len(results)}")
    console.print(f"  [green]Successful: {total_success}[/green]")
    console.print(f"  [red]Failed: {total_failed}[/red]")
    console.print(f"  Success rate: {100*total_success/len(results):.1f}%" if results else "N/A")
    console.print(f"\nResults saved to: [cyan]{results_path}[/cyan]")
    
    # Exit with non-zero code if any repo failed
    if total_failed > 0:
        raise typer.Exit(1)


@app.command()
def config():
    """
    Display current Nova configuration and verify setup.
    """
    import os
    from nova.config import get_settings
    
    console.print("[bold]Nova CI-Rescue Configuration Check[/bold]")
    console.print("=" * 50)
    
    try:
        settings = get_settings()
        
        # Check API keys
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
        
        if has_openai or has_anthropic:
            console.print("✅ API Key: Configured ", style="green", end="")
            if has_openai and has_anthropic:
                console.print("(OpenAI + Anthropic)", style="dim")
            elif has_openai:
                console.print("(OpenAI)", style="dim")
            else:
                console.print("(Anthropic)", style="dim")
        else:
            console.print("❌ API Key: Not configured", style="red")
            console.print("   Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env", style="yellow")
        
        # Display model configuration
        console.print(f"✅ Model: {settings.default_llm_model}", style="green")
        
        # Display iteration and timeout settings
        console.print(f"✅ Max Iterations: {settings.max_iters}", style="green")
        console.print(f"✅ Timeout: {settings.run_timeout_sec}s", style="green")
        console.print(f"✅ Test Timeout: {settings.test_timeout_sec}s", style="green")
        
        # Check telemetry directory
        telemetry_dir = Path(settings.telemetry_dir)
        if telemetry_dir.exists():
            console.print(f"✅ Telemetry Dir: {telemetry_dir}", style="green")
        else:
            console.print(f"ℹ️  Telemetry Dir: {telemetry_dir} (will be created)", style="yellow")
        
        # Display allowed domains
        if settings.allowed_domains:
            console.print(f"✅ Allowed Domains: {', '.join(settings.allowed_domains[:3])}...", style="green")
        
        # Check for .env file
        env_file = Path(".env")
        if env_file.exists():
            console.print(f"✅ Config File: .env found", style="green")
        else:
            console.print("ℹ️  Config File: Using environment variables", style="yellow")
        
        # Python version check
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if sys.version_info >= (3, 10):
            console.print(f"✅ Python Version: {py_version}", style="green")
        else:
            console.print(f"⚠️  Python Version: {py_version} (3.10+ recommended)", style="yellow")
        
        # Git check
        try:
            git_version = subprocess.run(
                ["git", "--version"], 
                capture_output=True, 
                text=True,
                timeout=5
            ).stdout.strip()
            console.print(f"✅ Git: {git_version}", style="green")
        except:
            console.print("⚠️  Git: Not found or not accessible", style="yellow")
        
        console.print("\n[bold green]Configuration check complete![/bold green]")
        
        if not (has_openai or has_anthropic):
            console.print("\n[yellow]⚠️  To get started, add your API key to .env file:[/yellow]")
            console.print("   cp env.example .env")
            console.print("   nano .env  # Add your API key")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]Error checking configuration: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def version():
    """
    Show Nova CI-Rescue version.
    """
    from nova import __version__
    console.print(f"[green]Nova CI-Rescue[/green] v{__version__}")


if __name__ == "__main__":
    app()
