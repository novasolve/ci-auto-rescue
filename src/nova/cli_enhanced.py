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
            apply_result = apply_node.execute(state, patch_diff, git_manager, logger=telemetry, iteration=iteration)
            
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
        
        # Generate proof-of-release run report (D3)
        if state and telemetry:
            from nova.github_integration import ReportGenerator
            from nova.tools.safety_limits import SafetyLimits
            generator = ReportGenerator()
            
            # Calculate total lines changed across all applied patches
            total_lines_changed = 0
            try:
                safety = SafetyLimits()
                for patch_text in state.patches_applied:
                    analysis = safety.analyze_patch(patch_text)
                    total_lines_changed += analysis.total_lines_changed
            except Exception:
                total_lines_changed = None
            
            # Prepare markdown content
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            report_md = "# Nova CI-Rescue Run Report\n\n"
            report_md += f"**Run Timestamp:** {timestamp_str}\n\n"
            
            # Include high-level summary (status, runtime, iterations, files, tests)
            elapsed_seconds = int((datetime.now() - state.start_time).total_seconds())
            initial_failures = len(initial_results.get("failing_tests", []))
            final_failures = len(state.failing_tests) if state.failing_tests else 0
            tests_fixed = initial_failures - final_failures
            
            # Count changed files
            files_changed = set()
            for patch in state.patches_applied:
                analysis = SafetyLimits().analyze_patch(patch)
                files_changed.update(analysis.files_modified | analysis.files_added)
            
            # Create metrics object for summary generation
            from nova.github_integration import RunMetrics
            metrics = RunMetrics(
                runtime_seconds=elapsed_seconds,
                iterations=state.current_iteration,
                files_changed=len(files_changed),
                status="success" if success else (state.final_status or "failure"),
                tests_fixed=tests_fixed,
                tests_remaining=final_failures,
                initial_failures=initial_failures,
                final_failures=final_failures,
                branch_name=branch_name
            )
            
            report_md += generator.generate_check_summary(metrics) + "\n"
            
            # Add diff statistics section
            report_md += "### Diff Summary\n"
            if total_lines_changed is not None:
                report_md += f"- Total lines changed (diff): **{total_lines_changed}**\n"
            report_md += f"- Files changed: **{len(files_changed)}**\n"
            if metrics.branch_name:
                report_md += f"- Fix Branch: `{metrics.branch_name}`\n"
            if metrics.status == "success" and metrics.tests_fixed == metrics.initial_failures:
                report_md += f"- ✅ All {metrics.initial_failures} failing tests were fixed.\n"
            elif metrics.tests_fixed > 0:
                report_md += f"- ⚠️ {metrics.tests_fixed} out of {metrics.initial_failures} tests fixed; {metrics.final_failures} still failing.\n"
            else:
                report_md += f"- ❌ No tests were fixed. {metrics.final_failures} failures remain.\n"
            
            # Save the markdown report to .nova/<run>/reports/summary.md
            reports_dir = telemetry.run_dir / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            report_file = reports_dir / "summary.md"
            with open(report_file, "w") as f:
                f.write(report_md)
            console.print(f"[dim]Run summary saved to {report_file}[/dim]")
        
        # GitHub PR reporting
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
                
                # Compute metrics from state
                elapsed = (datetime.now() - state.start_time).total_seconds()
                
                # Count changed files
                files_changed = set()
                for patch in state.patches_applied:
                    analysis = SafetyLimits().analyze_patch(patch)
                    files_changed.update(analysis.files_modified | analysis.files_added)
                
                metrics = RunMetrics(
                    runtime_seconds=int(elapsed),
                    iterations=state.current_iteration,
                    files_changed=len(files_changed),
                    status="success" if success else (state.final_status or "failure"),
                    tests_fixed=(len(state.failing_tests) - state.total_failures) if state.failing_tests else 0,
                    tests_remaining=state.total_failures,
                    initial_failures=len(state.failing_tests) if state.failing_tests else 0,
                    final_failures=state.total_failures,
                    branch_name=branch_name
                )
                
                # Post check-run
                head_sha = git_manager._get_current_head()
                if head_sha:
                    generator = ReportGenerator()
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
                
                # Post or update PR comment
                if pr_num:
                    generator = ReportGenerator()
                    existing = api.find_pr_comment(repo, int(pr_num), "<!-- ci-auto-rescue-report -->")
                    comment_body = generator.generate_pr_comment(metrics)
                    
                    if existing:
                        api.update_pr_comment(repo, existing, comment_body)
                        if verbose:
                            console.print("[dim]✅ Updated existing PR comment[/dim]")
                    else:
                        api.create_pr_comment(repo, int(pr_num), comment_body)
                        if verbose:
                            console.print("[dim]✅ Created new PR comment[/dim]")
                            
            except Exception as e:
                console.print(f"[yellow]⚠️ GitHub reporting failed: {e}[/yellow]")
        
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
def eval(
    repos_file: Path = typer.Argument(..., help="YAML file containing repositories to evaluate", exists=True),
    output_dir: Path = typer.Option(Path("./evals/results"), "--output", "-o", help="Directory for evaluation results"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="YAML config file for runs", exists=True)
):
    """Evaluate Nova on multiple repositories."""
    import yaml
    import json
    import subprocess
    import re
    from datetime import timezone
    
    def load_yaml_config(config_file: Path) -> dict:
        """Load YAML configuration file."""
        with open(config_file, "r") as f:
            return yaml.safe_load(f)
    
    # Load optional config for common settings
    config_data = load_yaml_config(config_file) if config_file else None
    console.print(f"[green]Nova CI-Rescue Evaluation[/green] 📊")
    if config_file:
        console.print(f"[dim]Loaded configuration from {config_file}[/dim]")
    console.print(f"Repos file: {repos_file}")
    console.print(f"Output directory: {output_dir}\n")

    # Parse YAML for list of repos (supports either `runs:` key or direct list)
    try:
        with open(repos_file, "r") as f:
            repos_data = yaml.safe_load(f)
    except Exception as e:
        console.print(f"[red]Failed to read YAML file: {e}[/red]")
        raise typer.Exit(1)
    if isinstance(repos_data, dict) and 'runs' in repos_data:
        repos_list = repos_data['runs']
    elif isinstance(repos_data, list):
        repos_list = repos_data
    else:
        console.print("[red]Invalid YAML format: expected a list or 'runs:' key[/red]")
        raise typer.Exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    total_success = total_failed = 0

    # Prepare summary table with clear headers
    summary_table = Table(title="Evaluation Results", header_style="bold magenta")
    summary_table.add_column("Repository", style="cyan")
    summary_table.add_column("Status", style="green")
    summary_table.add_column("Duration", style="yellow")
    summary_table.add_column("Iterations", style="blue")
    summary_table.add_column("Tests Fixed", style="magenta")

    # Optional parallel execution (stubbed for future, runs sequentially for now)
    jobs = 1  # (Could be parameterized: e.g., typer.Option(1, "--jobs"))
    if jobs > 1 and len(repos_list) > 1:
        console.print(f"[yellow]Running eval on {len(repos_list)} repos with up to {jobs} parallel jobs...[/yellow]")
        # Parallel execution not yet fully implemented – sequential fallback
    else:
        jobs = 1

    for entry in repos_list:
        # Determine repo path and identify scenario name
        repo_path = Path(entry.get("path") or entry.get("repo") or entry.get("repo_path", "."))
        if not repo_path.is_absolute():
            repo_path = (repos_file.parent / repo_path).resolve()
        name = entry.get("name") or repo_path.name
        max_iters = entry.get("max_iters") or entry.get("max_iterations", 6)
        timeout = entry.get("timeout", 1200)

        if not repo_path.exists():
            console.print(f"[yellow]⚠️ Skipping {name}: path not found ({repo_path})[/yellow]")
            results.append({"name": name, "repo": str(repo_path), "success": False, "error": "path_not_found"})
            total_failed += 1
            continue

        console.print(f"\n[bold]Running Nova on [cyan]{name}[/cyan]...[/bold]")
        console.print(f"  Path: {repo_path}")
        console.print(f"  Max iterations: {max_iters}")
        console.print(f"  Timeout: {timeout}s")

        # Execute `nova fix` for this repo in a subprocess
        start_time = datetime.now(timezone.utc)
        cmd = ["python", "-m", "nova", "fix", str(repo_path), "--max-iters", str(max_iters), "--timeout", str(timeout)]
        if config_file:
            cmd += ["--config", str(config_file)]
        if verbose:
            cmd.append("--verbose")
        result = subprocess.run(cmd, capture_output=True, text=True)
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        success_flag = (result.returncode == 0)

        # Parse key metrics from output (iterations and tests fixed)
        iter_count = tests_fixed = initial_failures = 0
        for line in result.stdout.splitlines():
            if "Iterations completed:" in line:
                match = re.search(r"Iterations completed: (\d+)", line)
                if match: 
                    iter_count = int(match.group(1))
            if "Initial failures:" in line:
                match = re.search(r"Initial failures: (\d+)", line)
                if match: 
                    initial_failures = int(match.group(1))
            if "Tests fixed:" in line:
                match = re.search(r"Tests fixed: (\d+)/", line)
                if match: 
                    tests_fixed = int(match.group(1))
        if success_flag and initial_failures and tests_fixed == 0:
            tests_fixed = initial_failures  # All fixed

        status_text = "✅ SUCCESS" if success_flag else "❌ FAILED"
        console.print(f"• [yellow]{name}[/yellow]: {status_text} after {int(elapsed)}s, {iter_count} iteration(s)")

        summary_table.add_row(name, "SUCCESS" if success_flag else "FAILED", f"{int(elapsed)}s", str(iter_count), str(tests_fixed))
        total_success += (1 if success_flag else 0)
        total_failed  += (0 if success_flag else 1)
        results.append({
            "name": name,
            "repo": str(repo_path),
            "success": success_flag,
            "duration": elapsed,
            "iterations": iter_count,
            "tests_fixed": tests_fixed,
            "initial_failures": initial_failures,
            "max_iterations": max_iters,
            "timeout": timeout
        })
    # Save results to JSON with timestamp
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    results_path = output_dir / f"{timestamp}.json"
    with open(results_path, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "total_repos": len(results),
            "successful": total_success,
            "failed": total_failed,
            "results": results
        }, f, indent=2)

    # Display final summary table and stats
    console.print("\n" + "="*60)
    console.print(summary_table)
    console.print("="*60)
    console.print(f"\n[bold]Evaluation Complete[/bold]")
    console.print(f"  Total repositories: {len(results)}")
    console.print(f"  [green]Successful: {total_success}[/green]")
    console.print(f"  [red]Failed: {total_failed}[/red]")
    if results:
        success_rate = 100 * total_success / len(results)
        console.print(f"  Success rate: {success_rate:.1f}%")
    console.print(f"\nResults saved to: [cyan]{results_path}[/cyan]")
    if total_failed > 0:
        raise typer.Exit(1)


@app.command()
def version():
    """Show Nova CI-Rescue version."""
    console.print("[green]Nova CI-Rescue Enhanced[/green] v1.0.0")


if __name__ == "__main__":
    app()
