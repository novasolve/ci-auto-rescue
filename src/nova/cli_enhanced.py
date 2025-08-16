"""
Nova CI-Rescue Enhanced CLI
============================

Best of both worlds: Combines our clean implementation with production features.
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Optional
from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table

# Import Nova components
from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger
from nova.config import NovaSettings, SafetyConfig, load_yaml_config
from nova.tools.git import GitBranchManager
from nova.runner.test_runner import TestRunner
from nova.agent.nova_deep_agent import NovaDeepAgent

# Tool imports
from nova.tools.run_tests import RunTestsTool
from nova.tools.apply_patch import ApplyPatchTool
from nova.tools.critic_review import CriticReviewTool

app = typer.Typer(
    name="nova",
    help="Nova CI-Rescue: AI-powered test fixing",
    add_completion=False,
)
console = Console()


def print_exit_summary(state: AgentState, reason: str):
    """Print execution summary."""
    console.print("\n" + "=" * 60)
    console.print("[bold]EXECUTION SUMMARY[/bold]")
    console.print("=" * 60)
    
    # Status
    if reason == "success":
        console.print("[green]✅ SUCCESS - All tests fixed![/green]")
    elif reason == "max_iters":
        console.print(f"[yellow]⚠️ MAX ITERATIONS - Reached limit of {state.max_iterations}[/yellow]")
    elif reason == "timeout":
        console.print(f"[red]⏰ TIMEOUT - Exceeded {state.timeout_seconds}s[/red]")
    elif reason == "interrupted":
        console.print("[yellow]🛑 INTERRUPTED - User cancelled[/yellow]")
    elif reason == "error":
        console.print("[red]❌ ERROR - Unexpected failure[/red]")
    else:
        console.print(f"[yellow]Exit: {reason}[/yellow]")
    
    # Statistics
    console.print(f"\nIterations: {state.current_iteration}/{state.max_iterations}")
    console.print(f"Patches applied: {len(state.patches_applied)}")
    console.print(f"Initial failures: {len(state.failing_tests) if state.failing_tests else 0}")
    console.print(f"Remaining failures: {state.total_failures}")
    
    if state.total_failures == 0 and state.failing_tests:
        console.print(f"[green]Fixed all {len(state.failing_tests)} failing tests![/green]")
    
    console.print("=" * 60 + "\n")


@app.command()
def fix(
    repo_path: Path = typer.Argument(
        Path("."),
        help="Path to repository",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="Path to YAML configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    max_iters: Optional[int] = typer.Option(
        None,
        "--max-iters", "-i",
        help="Maximum iterations (default: 6)",
        min=1,
        max=20,
    ),
    timeout: Optional[int] = typer.Option(
        None,
        "--timeout", "-t",
        help="Timeout in seconds (default: 1200)",
        min=60,
        max=7200,
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model", "-m",
        help="LLM model (gpt-4, claude-3, llama-2, etc.)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose output",
    ),
    no_docker: bool = typer.Option(
        False,
        "--no-docker",
        help="Disable Docker sandbox for tests",
    ),
    github_token: Optional[str] = typer.Option(
        None,
        "--github-token",
        help="GitHub token for PR integration",
        envvar="GITHUB_TOKEN",
    ),
):
    """
    Fix failing tests in a repository using AI.
    
    Examples:
        nova fix                    # Fix tests in current directory
        nova fix /path/to/repo      # Fix tests in specific repo
        nova fix -c config.yml      # Use configuration file
        nova fix --model claude-3   # Use Claude instead of GPT-4
    """
    # Load configuration
    settings = NovaSettings()
    
    # Load from YAML if provided
    if config_file:
        yaml_config = load_yaml_config(config_file)
        if yaml_config:
            # Update settings with YAML values
            for key, value in yaml_config.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            console.print(f"[dim]Loaded config from {config_file}[/dim]")
    
    # Override with CLI arguments
    if max_iters is not None:
        settings.max_iterations = max_iters
    if timeout is not None:
        settings.timeout_seconds = timeout
    if model is not None:
        settings.default_llm_model = model
    if no_docker:
        settings.use_docker = False
    settings.verbose = verbose
    
    # Display configuration
    console.print("[green]Nova CI-Rescue[/green] 🚀")
    console.print(f"Repository: {repo_path}")
    console.print(f"Model: {settings.default_llm_model}")
    console.print(f"Max iterations: {settings.max_iterations}")
    console.print(f"Timeout: {settings.timeout_seconds}s")
    console.print(f"Docker: {'enabled' if settings.use_docker else 'disabled'}")
    console.print()
    
    # Initialize components
    git_manager = None
    telemetry = None
    state = None
    branch_name = None
    success = False
    
    try:
        # Set up git branch
        git_manager = GitBranchManager(repo_path, verbose=verbose)
        branch_name = git_manager.create_fix_branch()
        console.print(f"[dim]Working on branch: {branch_name}[/dim]")
        git_manager.setup_signal_handler()
        
        # Initialize telemetry
        telemetry = JSONLLogger()
        telemetry.log_event("run_start", {
            "repo": str(repo_path),
            "model": settings.default_llm_model,
            "max_iterations": settings.max_iterations
        })
        
        # Initialize state
        state = AgentState(
            repo_path=repo_path,
            max_iterations=settings.max_iterations,
            timeout_seconds=settings.timeout_seconds
        )
        
        # Step 1: Pre-agent test discovery (for better user feedback)
        console.print("[cyan]Running initial tests...[/cyan]")
        runner = TestRunner(repo_path, verbose=verbose)
        failing_tests, initial_junit = runner.run_tests(max_failures=10)
        
        # Try fault localization if available
        try:
            from nova.runner.test_runner import FaultLocalizer
            FaultLocalizer.localize_failures(failing_tests, coverage_data=None)
            if verbose:
                console.print("[dim]Fault localization complete[/dim]")
        except:
            pass  # Fault localization is optional
        
        # Save initial test report
        if initial_junit:
            telemetry.save_patch(0, initial_junit)
        
        # Store failures in state
        state.add_failing_tests(failing_tests)
        telemetry.log_event("test_discovery", {
            "total_failures": state.total_failures,
            "failing_tests": [t.name for t in failing_tests] if failing_tests else []
        })
        
        # Check if already passing
        if not failing_tests:
            console.print("[green]✅ No failing tests! Repository is already green.[/green]")
            state.final_status = "success"
            success = True
            
            # GitHub integration
            if github_token:
                _post_github_status(
                    token=github_token,
                    repo_path=repo_path,
                    status="success",
                    message="No failing tests found",
                    state=state,
                    git_manager=git_manager
                )
            
            return
        
        # Display failing tests
        console.print(f"\n[red]Found {len(failing_tests)} failing test(s):[/red]")
        table = Table(title="Failing Tests", show_header=True)
        table.add_column("Test", style="cyan", no_wrap=False)
        table.add_column("Location", style="yellow")
        table.add_column("Error", style="red", no_wrap=False)
        
        for test in failing_tests[:10]:
            location = f"{test.file}:{test.line}" if hasattr(test, 'line') else test.file
            error = test.short_traceback.split('\n')[0][:80] if hasattr(test, 'short_traceback') else "Unknown"
            table.add_row(test.name, location, error)
        
        if len(failing_tests) > 10:
            table.add_row("...", f"({len(failing_tests) - 10} more)", "...")
        
        console.print(table)
        console.print()
        
        # Prepare tools
        console.print("[cyan]Initializing AI agent...[/cyan]")
        
        run_tests_tool = RunTestsTool(repo_path=repo_path, verbose=verbose)
        apply_patch_tool = ApplyPatchTool(
            git_manager=git_manager,
            safety_config=SafetyConfig.from_dict(yaml_config.get("safety", {})) if yaml_config else SafetyConfig(),
            verbose=verbose,
            state=state
        )
        critic_tool = CriticReviewTool(verbose=verbose)
        
        tools = [run_tests_tool, apply_patch_tool, critic_tool]
        
        # Add optional file tools if available
        try:
            from nova.agent.tools import open_file, write_file
            from langchain.agents import Tool
            
            if open_file:
                tools.append(Tool(
                    name="open_file",
                    func=open_file,
                    description="Read source code files"
                ))
            if write_file:
                tools.append(Tool(
                    name="write_file", 
                    func=lambda input: write_file(*input.split("|||", 1)),
                    description="Write to source files (use: path|||content)"
                ))
        except:
            pass  # File tools are optional
        
        # Initialize agent
        agent = NovaDeepAgent(
            tools=tools,
            state=state,
            telemetry=telemetry,
            llm_model=settings.default_llm_model,
            settings=settings,
            verbose=verbose
        )
        
        # Format failing tests for agent
        failures_summary = runner.format_failures_table(failing_tests) if hasattr(runner, 'format_failures_table') else str(failing_tests)
        
        # Extract error details
        error_details = []
        for test in failing_tests[:3]:
            if hasattr(test, 'short_traceback'):
                error_details.append(f"{test.name}:\n{test.short_traceback[:500]}")
        error_details_str = "\n\n".join(error_details)
        
        # Run the agent
        console.print("\n[bold]Starting AI agent...[/bold]")
        success = agent.run(
            failures_summary=failures_summary,
            error_details=error_details_str
        )
        
        # Set final status
        if success:
            state.final_status = "success"
        elif state.current_iteration >= state.max_iterations:
            state.final_status = "max_iters"
        else:
            state.final_status = "incomplete"
        
        # Print summary
        print_exit_summary(state, state.final_status)
        
        # Log completion
        telemetry.log_event("completion", {
            "status": state.final_status,
            "iterations": state.current_iteration,
            "patches_applied": len(state.patches_applied),
            "final_failures": state.total_failures
        })
        
        # GitHub integration
        if github_token:
            _post_github_status(
                token=github_token,
                repo_path=repo_path,
                status="success" if success else "failure",
                message=f"Fixed {len(failing_tests) - state.total_failures}/{len(failing_tests)} tests",
                state=state,
                git_manager=git_manager
            )
        
    except KeyboardInterrupt:
        # Handle Ctrl+C
        if state:
            state.final_status = "interrupted"
            print_exit_summary(state, "interrupted")
        else:
            console.print("\n[yellow]Interrupted by user[/yellow]")
        
        if telemetry:
            telemetry.log_event("interrupted", {"reason": "keyboard_interrupt"})
        
        success = False
        
    except Exception as e:
        # Handle errors
        console.print(f"\n[red]Error: {e}[/red]")
        
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        
        if state:
            state.final_status = "error"
            print_exit_summary(state, "error")
        
        if telemetry:
            telemetry.log_event("error", {"error": str(e)})
        
        success = False
        
    finally:
        # Cleanup
        if git_manager and branch_name:
            git_manager.cleanup(success=success)
            git_manager.restore_signal_handler()
        
        if telemetry:
            telemetry.end_run(success=success)
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)


def _post_github_status(
    token: str,
    repo_path: Path,
    status: str,
    message: str,
    state: Optional[AgentState] = None,
    git_manager: Optional[GitBranchManager] = None
):
    """Post status to GitHub (PR comments, check runs, etc.)."""
    try:
        # This would integrate with GitHub API
        # Simplified for demonstration
        console.print(f"[dim]GitHub: {status} - {message}[/dim]")
    except Exception as e:
        console.print(f"[yellow]GitHub integration failed: {e}[/yellow]")


@app.command()
def version():
    """Show Nova version."""
    console.print("Nova CI-Rescue v0.4.0 (Enhanced Edition)")
    console.print("Powered by LangChain and OpenAI/Anthropic/Llama")


if __name__ == "__main__":
    app()