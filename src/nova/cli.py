#!/usr/bin/env python3
"""
Nova CI-Rescue CLI interface.
"""

import os
import re
import json
import time
import subprocess
import tempfile
import typer
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
from nova.tools.datetime_utils import now_utc, delta_between, seconds_between
from rich.console import Console
from rich.table import Table

from nova.runner import TestRunner
from nova.agent import AgentState
from nova.config import NovaSettings, load_yaml_config, get_settings
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

    # If no command is provided, show help
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
    console.print(f"  • Initial failures: {state.initial_failures}")
    console.print(f"  • Remaining failures: {state.total_failures}")
    
    if state.total_failures == 0:
        console.print(f"  • [green]All tests fixed successfully![/green]")
    elif state.failing_tests and state.total_failures < len(state.failing_tests):
        fixed = len(state.failing_tests) - state.total_failures
        console.print(f"  • Tests fixed: {fixed}/{len(state.failing_tests)}")
    
    # Time elapsed
    if elapsed_seconds is not None:
        minutes, seconds = divmod(int(elapsed_seconds), 60)
        console.print(f"  • Time elapsed: {minutes}m {seconds}s")
    elif hasattr(state, 'start_time') and state.start_time:
        # Handle both datetime and float start_time
        if isinstance(state.start_time, float):
            elapsed = time.time() - state.start_time
        else:
            elapsed = seconds_between(now_utc(), state.start_time)
        minutes, seconds = divmod(int(elapsed), 60)
        console.print(f"  • Time elapsed: {minutes}m {seconds}s")
    
    # List saved patches if telemetry is enabled
    from nova.config import get_settings
    settings = get_settings()
    if settings.enable_telemetry and hasattr(state, 'telemetry') and state.telemetry:
        try:
            from pathlib import Path
            run_dir = state.telemetry.run_dir
            if run_dir and Path(run_dir).exists():
                patch_dir = Path(run_dir) / "patches"
                if patch_dir.exists():
                    console.print("\n[bold]📄 Saved patches:[/bold]")
                    patches = sorted(patch_dir.glob("*.patch"))
                    if patches:
                        for patch_file in patches:
                            console.print(f"  • {patch_file.name}")
                        console.print(f"  [dim](Saved in: {patch_dir})[/dim]")
                    else:
                        console.print("  [dim](No patches saved)[/dim]")
        except Exception as e:
            if state.verbose:
                console.print(f"[dim]Could not list patches: {e}[/dim]")
    
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
    legacy_agent: bool = typer.Option(
        False,
        "--legacy-agent",
        help="Use the legacy v1.0 LLM-based agent instead of the default LangChain Deep Agent",
        is_flag=True,
    ),
):
    """
    Fix failing tests in a repository using an AI agent.

    By default, uses the Nova Deep Agent (LangChain-based) for iterative fixes.
    Use the --legacy-agent flag to run the deprecated v1.0 LLM-based agent pipeline.
    """
    # Load configuration file if provided
    config_data = None
    if config_file is not None:
        try:
            config_data = load_yaml_config(config_file)
        except Exception as e:
            console.print(f"[red]Failed to load config: {e}[/red]")
            raise typer.Exit(1)

    # If config specifies a different repo_path and CLI used default ".", override
    if config_data and config_data.repo_path:
        default_repo = Path(".").resolve()
        if repo_path.resolve() == default_repo:
            repo_path = Path(config_data.repo_path)

    # Determine effective iteration count and timeout
    final_max_iters = max_iters if max_iters is not None else (
        config_data.max_iters if config_data and config_data.max_iters is not None else 6
    )
    final_timeout = timeout if timeout is not None else (
        config_data.timeout if config_data and config_data.timeout is not None else 1200
    )

    console.print(f"[green]Nova CI-Rescue[/green] 🚀")
    if config_file:
        console.print(f"[dim]Loaded configuration from {config_file}[/dim]")

    # Initialize Git branch management
    git_manager = GitBranchManager(repo_path)
    state = None
    telemetry = None
    success = False
    
    # Check for concurrent runs
    from nova.tools.lock import nova_lock
    
    try:
            branch_name = git_manager.create_fix_branch()
            console.print(f"[dim]Working on branch: {branch_name}[/dim]")
            
        # Set up Ctrl+C signal handler for clean abort
        git_manager.setup_signal_handler()
            
        # Initialize settings and telemetry
        settings = NovaSettings()
        if config_data and config_data.model:
            settings.default_llm_model = config_data.model
        telemetry = JSONLLogger()
        telemetry.log_event("run_start", {
            "repo": str(repo_path),
            "model": settings.default_llm_model,
            "max_iterations": final_max_iters,
            "timeout": final_timeout
        })
        
            # Initialize agent state
            state = AgentState(
                repo_path=repo_path,
            max_iterations=final_max_iters,
            timeout_seconds=final_timeout,
        )

        # Step 1: Run tests to identify initial failures
        runner = TestRunner(repo_path, verbose=verbose)
        failing_tests, initial_junit_xml = runner.run_tests(max_failures=5)

        # Optional fault localization (mark suspected files based on tracebacks)
        try:
            from nova.runner.test_runner import FaultLocalizer
            FaultLocalizer.localize_failures(failing_tests, coverage_data=None)
        except Exception:
            pass
            
            # Save initial test report
            if initial_junit_xml:
                telemetry.save_test_report(0, initial_junit_xml, report_type="junit")
            
            # Record initial failures in state
            state.add_failing_tests(failing_tests)
            telemetry.log_event("test_discovery", {
                "total_failures": state.total_failures,
                "failing_tests": state.failing_tests,
                "initial_report_saved": initial_junit_xml is not None
            })
            
            # If no failures, nothing to fix
            if not failing_tests:
                console.print("[green]✅ No failing tests found! Repository is already green.[/green]")
                state.final_status = "success"
                telemetry.log_event("completion", {"status": "no_failures"})
                telemetry.end_run(success=True)
            # Post no-failure result to GitHub if applicable
            token = os.getenv("GITHUB_TOKEN")
            repo = os.getenv("GITHUB_REPOSITORY")
            pr_num = os.getenv("PR_NUMBER")
            if not pr_num:
                pr_num = os.getenv("GITHUB_EVENT_NUMBER")
                if not pr_num:
                    github_ref = os.getenv("GITHUB_REF")
                    if github_ref and "pull/" in github_ref:
                        match = re.search(r"pull/(\d+)/", github_ref)
                        if match:
                            pr_num = match.group(1)
                if not pr_num:
                    event_path = os.getenv("GITHUB_EVENT_PATH")
                    if event_path and os.path.exists(event_path):
                        try:
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
            
        # Display failing tests summary table (up to first 10 failures)
            console.print(f"\n[bold red]Found {len(failing_tests)} failing test(s):[/bold red]")
            table = Table(title="Failing Tests", show_header=True, header_style="bold magenta")
            table.add_column("Test Name", style="cyan", no_wrap=False)
            table.add_column("Location", style="yellow")
            table.add_column("Error", style="red", no_wrap=False)
        for test in failing_tests[:10]:
            location = f"{test.file}:{test.line}" if hasattr(test, "file") else "N/A"
            error_preview = (test.short_traceback.split('\n')[0] if hasattr(test, "short_traceback") else str(test))[:60]
            if len(error_preview) == 60:
                error_preview += "..."
            name = getattr(test, "name", str(test))
            table.add_row(name, location, error_preview)
        if len(failing_tests) > 10:
            table.add_row("...", f"... and {len(failing_tests)-10} more", "")
            console.print(table)
            console.print()
            
        # Prepare safety limits configuration from YAML (if provided)
        safety_conf = None
        if config_data:
            from nova.tools.safety_limits import SafetyConfig
            safety_conf_obj = SafetyConfig()
            custom_limits = False
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

        # Either run the Deep Agent or the legacy agent loop
        success = False
        if not legacy_agent:
            # === Deep Agent Path (default) ===
            console.print("\n[bold]Initializing Nova Deep Agent...[/bold]")
            from nova.agent.deep_agent import NovaDeepAgent
            deep_agent = NovaDeepAgent(
                state=state,
                telemetry=telemetry,
                git_manager=git_manager,
                verbose=verbose,
                safety_config=safety_conf
            )
            console.print("[cyan]🤖 Running Deep Agent to fix failing tests...[/cyan]")
            failures_summary = runner.format_failures_table(failing_tests)
            error_details = "\n\n".join(test.short_traceback for test in failing_tests[:3])
            code_snippets = ""
            success = deep_agent.run(
                failures_summary=failures_summary,
                error_details=error_details,
                code_snippets=code_snippets
            )
            # Deep Agent handles iterations internally; no explicit loop needed here.
            if success:
                console.print("\n[green bold]✅ SUCCESS - All tests fixed![/green bold]")
                state.final_status = "success"
                else:
                console.print("\n[red bold]❌ FAILED - Some tests could not be fixed.[/red bold]")
                if state.final_status == "max_iters":
                    console.print(f"[yellow]Reached maximum iterations ({state.max_iterations}) without full success.[/yellow]")
                elif state.final_status == "error":
                    console.print("[yellow]Agent encountered an error during execution.[/yellow]")
        else:
            # === Legacy Agent Path (deprecated v1.0 approach) ===
            console.print("\n[bold]⚠️ Running legacy LLM-based agent (deprecated)...[/bold]")
                    from nova.agent.llm_agent import LLMAgent
            from nova.nodes.planner import planner_node
            from nova.nodes.actor import actor_node
            from nova.nodes.critic import critic_node
            from nova.nodes.apply_patch import apply_patch as apply_patch_func

            # Initialize the legacy LLM agent
            llm_agent = LLMAgent(repo_path=repo_path, model=settings.default_llm_model)

            critic_feedback: Optional[str] = None
            iteration = 0
            while iteration < state.max_iterations:
                console.print(f"\n[bold]Iteration {iteration+1}/{state.max_iterations}[/bold]")
                # Planner: generate a plan (stored in state.plan)
                planner_node(state=state, llm_agent=llm_agent, telemetry=telemetry, verbose=verbose)
                # Actor: generate a patch diff based on the plan (and any critic feedback)
                patch_diff = actor_node(state=state, llm_agent=llm_agent, telemetry=telemetry,
                                        critic_feedback=state.critic_feedback, verbose=verbose)
                if patch_diff is None:
                    # No patch could be generated
                    console.print("[red]❌ No patch could be generated by the agent[/red]")
                    state.final_status = "no_patch"
                    break
                
                # Critic: review the proposed patch using LLM
                approved, reason = critic_node(state=state, patch_diff=patch_diff, llm_agent=llm_agent,
                                               telemetry=telemetry, verbose=verbose)
                if not approved:
                    # Critic rejected the patch – provide feedback and iterate again (no patch applied)
                    console.print(f"[yellow]⚠️ Critic rejected patch: {reason}[/yellow]")
                    # If this was the last allowed iteration, exit
                    if iteration >= state.max_iterations - 1:
                        state.final_status = "patch_rejected"
                        break
                    # Otherwise, continue to next iteration with critic feedback (stored in state.critic_feedback)
                    iteration += 1
                    continue

                # Apply the approved patch to the repository
                result = apply_patch_func(state=state, patch_text=patch_diff, git_manager=git_manager, verbose=verbose)
                if not result.get("success"):
                    console.print(f"[red]❌ Failed to apply patch (iteration {iteration+1})[/red]")
                    # Determine failure reason (safety or apply error)
                    if result.get("safety_violation"):
                        console.print(f"[yellow]Safety violation: {result.get('safety_message', 'unknown')}[/yellow]")
                        state.final_status = "patch_rejected"
                    else:
                        state.final_status = "patch_error"
                        break

                # Patch successfully applied and committed; save patch diff and run tests again
                telemetry.save_patch(iteration+1, patch_diff)
                new_failures, junit_xml = runner.run_tests(max_failures=5)
                if junit_xml:
                    telemetry.save_test_report(iteration+1, junit_xml, report_type="junit")
                state.add_failing_tests(new_failures)
                if state.total_failures == 0:
                    console.print("\n[green bold]✅ SUCCESS - All tests fixed![/green bold]")
                    success = True
                    state.final_status = "success"
                    break
                else:
                    console.print(f"[cyan]🔄 {state.total_failures} tests still failing, continuing to next iteration...[/cyan]")
                    # Prepare for next iteration (failure details will feed the next plan)
                    iteration += 1
                    state.current_iteration = iteration
                    # (Critic feedback cleared on patch approval; state.plan will be updated by next planner_node)
                    continue

            # If loop ended without setting final_status, it means max iterations reached
            if state.final_status is None or (state.final_status not in {"success", "patch_error", "patch_rejected", "no_patch"}):
                # Reached max iterations without full success
                    state.final_status = "max_iters"
                console.print(f"\n[red bold]❌ FAILED - Reached max iterations ({state.max_iterations}) with tests still failing.[/red bold]")

        # Log completion status
            telemetry.log_event("completion", {
                "status": state.final_status,
                "iterations": state.current_iteration,
                "total_patches": len(state.patches_applied),
                "final_failures": state.total_failures
            })
        # Print comprehensive exit summary
        if state and state.final_status:
            elapsed = (datetime.now() - state.start_time).total_seconds()
            print_exit_summary(state, state.final_status, elapsed_seconds=elapsed)

        telemetry.end_run(success=(state.final_status == "success"))

        # GitHub integration: post results to PR if in CI environment
        token = os.getenv("GITHUB_TOKEN")
        repo = os.getenv("GITHUB_REPOSITORY")
        pr_num = os.getenv("PR_NUMBER") or os.getenv("GITHUB_EVENT_NUMBER") or None
        if not pr_num:
            github_ref = os.getenv("GITHUB_REF")
            if github_ref and "pull/" in github_ref:
                match = re.search(r"pull/(\d+)/", github_ref)
                if match:
                    pr_num = match.group(1)
            if not pr_num:
                event_path = os.getenv("GITHUB_EVENT_PATH")
                if event_path and os.path.exists(event_path):
                    try:
                        with open(event_path, "r") as f:
                            event_data = json.load(f)
                        if "pull_request" in event_data:
                            pr_num = str(event_data["pull_request"]["number"])
                    except:
                        pass
        if token and repo:
            try:
                from nova.github_integration import GitHubAPI, RunMetrics, ReportGenerator
                elapsed = (datetime.now() - state.start_time).total_seconds()
                # Count unique files changed across all applied patches
                files_changed = set()
                if state.patches_applied:
                    from nova.tools.safety_limits import SafetyLimits
                    safety = SafetyLimits()
                    for patch in state.patches_applied:
                        analysis = safety.analyze_patch(patch)
                        files_changed.update(analysis.files_modified | analysis.files_added)
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
                api = GitHubAPI(token)
                generator = ReportGenerator()
                head_sha = git_manager._get_current_head() if git_manager else None
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
                if pr_num:
                    existing_id = api.find_pr_comment(repo, int(pr_num), "<!-- ci-auto-rescue-report -->")
                    comment_body = generator.generate_pr_comment(metrics)
                    if existing_id:
                        api.update_pr_comment(repo, existing_id, comment_body)
                        if verbose:
                            console.print(f"[dim]✅ Updated existing PR comment[/dim]")
                    else:
                        api.create_pr_comment(repo, int(pr_num), comment_body)
                        if verbose:
                            console.print(f"[dim]✅ Created new PR comment[/dim]")
            except Exception as e:
                console.print(f"[yellow]⚠️ GitHub reporting failed: {e}[/yellow]")
                if verbose:
                    import traceback
                    console.print(f"[dim]{traceback.format_exc()}[/dim]")

        branch_name = git_manager.create_fix_branch()
        console.print(f"[dim]Working on branch: {branch_name}[/dim]")

        # Set up Ctrl+C signal handler for clean abort
        git_manager.setup_signal_handler()

        # Initialize settings and telemetry
        settings = NovaSettings()
        if config_data and config_data.model:
            settings.default_llm_model = config_data.model
        telemetry = JSONLLogger()
        telemetry.log_event("run_start", {
            "repo": str(repo_path),
            "model": settings.default_llm_model,
            "max_iterations": final_max_iters,
            "timeout": final_timeout
        })

        # Initialize agent state
        state = AgentState(
            repo_path=repo_path,
            max_iterations=final_max_iters,
            timeout_seconds=final_timeout,
        )

        # Step 1: Run tests to identify initial failures
        runner = TestRunner(repo_path, verbose=verbose)
        failing_tests, initial_junit_xml = runner.run_tests(max_failures=5)

        # Optional fault localization (mark suspected files based on tracebacks)
        try:
            from nova.runner.test_runner import FaultLocalizer
            FaultLocalizer.localize_failures(failing_tests, coverage_data=None)
        except Exception:
            pass

        # Save initial test report
        if initial_junit_xml:
            telemetry.save_test_report(0, initial_junit_xml, report_type="junit")

        # Record initial failures in state
        state.add_failing_tests(failing_tests)
        telemetry.log_event("test_discovery", {
            "total_failures": state.total_failures,
            "failing_tests": state.failing_tests,
            "initial_report_saved": initial_junit_xml is not None
        })

        # If no failures, nothing to fix
        if not failing_tests:
            if verbose:
                console.print("[green]✅ Repository is already green - no failing tests found.[/green]")
            state.final_status = "success"
            telemetry.log_event("completion", {"status": "no_failures"})
            telemetry.end_run(success=True)
            # Post no-failure result to GitHub if applicable
            token = os.getenv("GITHUB_TOKEN")
            repo = os.getenv("GITHUB_REPOSITORY")
            pr_num = os.getenv("PR_NUMBER")
            if not pr_num:
                pr_num = os.getenv("GITHUB_EVENT_NUMBER")
                if not pr_num:
                    github_ref = os.getenv("GITHUB_REF")
                    if github_ref and "pull/" in github_ref:
                        match = re.search(r"pull/(\d+)/", github_ref)
                        if match:
                            pr_num = match.group(1)
                if not pr_num:
                    event_path = os.getenv("GITHUB_EVENT_PATH")
                    if event_path and os.path.exists(event_path):
                        try:
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

        # Display failing tests summary table (up to first 10 failures)
        console.print(f"\n[bold red]Found {len(failing_tests)} failing test(s):[/bold red]")
        table = Table(title="Failing Tests", show_header=True, header_style="bold magenta")
        table.add_column("Test Name", style="cyan", no_wrap=False)
        table.add_column("Location", style="yellow")
        table.add_column("Error", style="red", no_wrap=False)
        for test in failing_tests[:10]:
            location = f"{test.file}:{test.line}" if hasattr(test, "file") else "N/A"
            error_preview = (test.short_traceback.split('\n')[0] if hasattr(test, "short_traceback") else str(test))[:60]
            if len(error_preview) == 60:
                error_preview += "..."
            name = getattr(test, "name", str(test))
            table.add_row(name, location, error_preview)
        if len(failing_tests) > 10:
            table.add_row("...", f"... and {len(failing_tests)-10} more", "")
        console.print(table)
        console.print()

        # Prepare safety limits configuration from YAML (if provided)
        safety_conf = None
        if config_data:
            from nova.tools.safety_limits import SafetyConfig
            safety_conf_obj = SafetyConfig()
            custom_limits = False
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

        # Either run the Deep Agent or the legacy agent loop
        success = False
        if not legacy_agent:
            # === Deep Agent Path (default) ===
            console.print("\n[bold]Initializing Nova Deep Agent...[/bold]")
            from nova.agent.deep_agent import NovaDeepAgent
            deep_agent = NovaDeepAgent(
                state=state,
                telemetry=telemetry,
                git_manager=git_manager,
                verbose=verbose,
                safety_config=safety_conf
            )
            console.print("[cyan]🤖 Running Deep Agent to fix failing tests...[/cyan]")
            failures_summary = runner.format_failures_table(failing_tests)
            error_details = "\n\n".join(test.short_traceback for test in failing_tests[:3])
            code_snippets = ""
            success = deep_agent.run(
                failures_summary=failures_summary,
                error_details=error_details,
                code_snippets=code_snippets
            )
            # Deep Agent handles iterations internally; no explicit loop needed here.
            if success:
                console.print("\n[green bold]✅ SUCCESS - All tests fixed![/green bold]")
                state.final_status = "success"
            else:
                console.print("\n[red bold]❌ FAILED - Some tests could not be fixed.[/red bold]")
                if state.final_status == "max_iters":
                    console.print(f"[yellow]Reached maximum iterations ({state.max_iterations}) without full success.[/yellow]")
                elif state.final_status == "error":
                    console.print("[yellow]Agent encountered an error during execution.[/yellow]")
        else:
            # === Legacy Agent Path (deprecated v1.0 approach) ===
            console.print("\n[bold]⚠️ Running legacy LLM-based agent (deprecated)...[/bold]")
            from nova.agent.llm_agent import LLMAgent
            from nova.nodes.planner import planner_node
            from nova.nodes.actor import actor_node
            from nova.nodes.critic import critic_node
            from nova.nodes.apply_patch import apply_patch as apply_patch_func

            # Initialize the legacy LLM agent
            llm_agent = LLMAgent(repo_path=repo_path, model=settings.default_llm_model)

            critic_feedback: Optional[str] = None
            iteration = 0
            while iteration < state.max_iterations:
                console.print(f"\n[bold]Iteration {iteration+1}/{state.max_iterations}[/bold]")
                # Planner: generate a plan (stored in state.plan)
                planner_node(state=state, llm_agent=llm_agent, telemetry=telemetry, verbose=verbose)
                # Actor: generate a patch diff based on the plan (and any critic feedback)
                patch_diff = actor_node(state=state, llm_agent=llm_agent, telemetry=telemetry,
                                        critic_feedback=state.critic_feedback, verbose=verbose)
                if patch_diff is None:
                    # No patch could be generated
                    console.print("[red]❌ No patch could be generated by the agent[/red]")
                    state.final_status = "no_patch"
                    break

                # Critic: review the proposed patch using LLM
                approved, reason = critic_node(state=state, patch_diff=patch_diff, llm_agent=llm_agent,
                                               telemetry=telemetry, verbose=verbose)
                if not approved:
                    # Critic rejected the patch – provide feedback and iterate again (no patch applied)
                    console.print(f"[yellow]⚠️ Critic rejected patch: {reason}[/yellow]")
                    # If this was the last allowed iteration, exit
                    if iteration >= state.max_iterations - 1:
                        state.final_status = "patch_rejected"
                        break
                    # Otherwise, continue to next iteration with critic feedback (stored in state.critic_feedback)
                    iteration += 1
                    continue

                # Apply the approved patch to the repository
                result = apply_patch_func(state=state, patch_text=patch_diff, git_manager=git_manager, verbose=verbose)
                if not result.get("success"):
                    console.print(f"[red]❌ Failed to apply patch (iteration {iteration+1})[/red]")
                    # Determine failure reason (safety or apply error)
                    if result.get("safety_violation"):
                        console.print(f"[yellow]Safety violation: {result.get('safety_message', 'unknown')}[/yellow]")
                        state.final_status = "patch_rejected"
                    else:
                        state.final_status = "patch_error"
                    break

                # Patch successfully applied and committed; save patch diff and run tests again
                telemetry.save_patch(iteration+1, patch_diff)
                new_failures, junit_xml = runner.run_tests(max_failures=5)
                if junit_xml:
                    telemetry.save_test_report(iteration+1, junit_xml, report_type="junit")
                state.add_failing_tests(new_failures)
                if state.total_failures == 0:
                    console.print("\n[green bold]✅ SUCCESS - All tests fixed![/green bold]")
                    success = True
                    state.final_status = "success"
                    break
                else:
                    console.print(f"[cyan]🔄 {state.total_failures} tests still failing, continuing to next iteration...[/cyan]")
                    # Prepare for next iteration (failure details will feed the next plan)
                    iteration += 1
                    state.current_iteration = iteration
                    # (Critic feedback cleared on patch approval; state.plan will be updated by next planner_node)
                    continue

            # If loop ended without setting final_status, it means max iterations reached
            if state.final_status is None or (state.final_status not in {"success", "patch_error", "patch_rejected", "no_patch"}):
                # Reached max iterations without full success
                state.final_status = "max_iters"
                console.print(f"\n[red bold]❌ FAILED - Reached max iterations ({state.max_iterations}) with tests still failing.[/red bold]")

        # Log completion status
        telemetry.log_event("completion", {
            "status": state.final_status,
            "iterations": state.current_iteration,
            "total_patches": len(state.patches_applied),
            "final_failures": state.total_failures
        })
        # Print comprehensive exit summary
        if state and state.final_status:
            elapsed = (datetime.now() - state.start_time).total_seconds()
            print_exit_summary(state, state.final_status, elapsed_seconds=elapsed)

        telemetry.end_run(success=(state.final_status == "success"))

        # GitHub integration: post results to PR if in CI environment
        token = os.getenv("GITHUB_TOKEN")
        repo = os.getenv("GITHUB_REPOSITORY")
        pr_num = os.getenv("PR_NUMBER") or os.getenv("GITHUB_EVENT_NUMBER") or None
        if not pr_num:
            github_ref = os.getenv("GITHUB_REF")
            if github_ref and "pull/" in github_ref:
                match = re.search(r"pull/(\d+)/", github_ref)
                if match:
                    pr_num = match.group(1)
            if not pr_num:
                event_path = os.getenv("GITHUB_EVENT_PATH")
                if event_path and os.path.exists(event_path):
                    try:
                        with open(event_path, "r") as f:
                            event_data = json.load(f)
                        if "pull_request" in event_data:
                            pr_num = str(event_data["pull_request"]["number"])
                    except:
                        pass
        if token and repo:
            try:
                from nova.github_integration import GitHubAPI, RunMetrics, ReportGenerator
                elapsed = (datetime.now() - state.start_time).total_seconds()
                # Count unique files changed across all applied patches
                files_changed = set()
                if state.patches_applied:
                    from nova.tools.safety_limits import SafetyLimits
                    safety = SafetyLimits()
                    for patch in state.patches_applied:
                        analysis = safety.analyze_patch(patch)
                        files_changed.update(analysis.files_modified | analysis.files_added)
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
                api = GitHubAPI(token)
                generator = ReportGenerator()
                head_sha = git_manager._get_current_head() if git_manager else None
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
                if pr_num:
                    existing_id = api.find_pr_comment(repo, int(pr_num), "<!-- ci-auto-rescue-report -->")
                    comment_body = generator.generate_pr_comment(metrics)
                    if existing_id:
                        api.update_pr_comment(repo, existing_id, comment_body)
                        if verbose:
                            console.print(f"[dim]✅ Updated existing PR comment[/dim]")
                    else:
                        api.create_pr_comment(repo, int(pr_num), comment_body)
                        if verbose:
                            console.print(f"[dim]✅ Created new PR comment[/dim]")
            except Exception as e:
                console.print(f"[yellow]⚠️ GitHub reporting failed: {e}[/yellow]")
                if verbose:
                    import traceback
                    console.print(f"[dim]{traceback.format_exc()}[/dim]")

    except KeyboardInterrupt:
        # Handle Ctrl+C interruption
        if state:
            state.final_status = "interrupted"
            console.print("\n[yellow]Interrupted by user[/yellow]")
            if telemetry:
                telemetry.log_event("interrupted", {"reason": "keyboard_interrupt"})
            print_exit_summary(state, "interrupted")
        else:
            console.print("\n[yellow]Interrupted by user[/yellow]")
        success = False
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        if state:
            state.final_status = "error"
            print_exit_summary(state, "error")
        if telemetry:
            telemetry.log_event("error", {"error": str(e)})
        success = False

    # Exit with appropriate code (0 if success, 1 if not)
    raise typer.Exit(0 if success else 1)

@app.command()
def eval(
    eval_file: Path = typer.Argument(
        ...,
        help="Path to evaluation YAML file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for results",
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
    console.print("[green]Nova CI-Rescue Evaluation[/green] 🔬")
    console.print(f"Loading evaluation config from: {eval_file}")
    
    # Implementation placeholder
    console.print("[yellow]Evaluation mode not fully implemented yet[/yellow]")
    raise typer.Exit(0)

@app.command()
def config():
    """
    Display current Nova configuration and verify setup.
    """
    from nova.config import get_settings
    
    console.print("[green]Nova CI-Rescue Configuration[/green] ⚙️")
    console.print()
    
    try:
        settings = get_settings()
        
        # Check Python version
        import sys
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        console.print(f"[cyan]Python Version:[/cyan] {py_version}")
        
        # Check API keys
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
        
        if has_openai or has_anthropic:
            console.print(f"[cyan]API Key:[/cyan] [green]✅ Configured[/green]")
            if has_openai:
                console.print(f"  • OpenAI: [green]Found[/green]")
            if has_anthropic:
                console.print(f"  • Anthropic: [green]Found[/green]")
        else:
            console.print(f"[cyan]API Key:[/cyan] [red]❌ Not configured[/red]")
            console.print("[yellow]Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env[/yellow]")
        
        # Display settings
        console.print(f"[cyan]Default Model:[/cyan] {settings.default_llm_model}")
        console.print(f"[cyan]Default Iterations:[/cyan] {settings.default_max_iterations}")
        console.print(f"[cyan]Default Timeout:[/cyan] {settings.default_timeout_seconds}s")
        
        # Check Docker availability
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                console.print(f"[cyan]Docker:[/cyan] [green]✅ Available[/green]")
            else:
                console.print(f"[cyan]Docker:[/cyan] [yellow]⚠️ Not available (sandboxing disabled)[/yellow]")
        except:
            console.print(f"[cyan]Docker:[/cyan] [yellow]⚠️ Not available (sandboxing disabled)[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/red]")
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
