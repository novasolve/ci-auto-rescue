"""
Nova Deep Agent CLI
====================

Command-line interface for the Nova CI-Rescue Deep Agent.

⚠️  DEPRECATED: This CLI is deprecated and will be removed in v2.0.
Please use 'nova fix' instead of 'nova-deep fix'.
"""

import os
import sys
import json
import warnings
from pathlib import Path
from typing import Optional

# Show deprecation warning when this module is imported
warnings.warn(
    "The nova-deep CLI is deprecated and will be removed in v2.0. "
    "Please use 'nova fix' instead.",
    DeprecationWarning,
    stacklevel=2
)

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from .agent.deep_agent import DeepAgent
from .agent.agent_config import AgentConfig
from .pipeline.ci_rescue_integration import CIRescuePipeline
from .tools.agent_tools import run_tests_tool


app = typer.Typer(
    name="nova-deep",
    help="Nova CI-Rescue Deep Agent - Automated test fixing with LangChain",
    add_completion=False
)
console = Console()


@app.command()
def fix(
    repo_path: Path = typer.Option(
        Path("."),
        "--repo", "-r",
        help="Path to the repository"
    ),
    model: str = typer.Option(
        "gpt-4",
        "--model", "-m",
        help="OpenAI model to use"
    ),
    max_iterations: int = typer.Option(
        5,
        "--max-iterations", "-i",
        help="Maximum fix iterations"
    ),
    auto_commit: bool = typer.Option(
        False,
        "--auto-commit", "-c",
        help="Automatically commit successful fixes"
    ),
    verbose: bool = typer.Option(
        True,
        "--verbose", "-v",
        help="Enable verbose output"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Run without making changes"
    )
):
    """
    Fix failing tests in a repository using the Deep Agent.
    """
    console.print(Panel.fit(
        "[bold cyan]Nova CI-Rescue Deep Agent[/bold cyan]\n"
        "Powered by LangChain",
        border_style="cyan"
    ))
    
    # Change to repo directory
    os.chdir(repo_path)
    
    # Update REPO_ROOT in agent tools after changing directory
    from .tools import agent_tools
    agent_tools.REPO_ROOT = Path(".").resolve()
    
    # Check for OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        console.print("[red]Error: OPENAI_API_KEY environment variable not set[/red]")
        console.print("Please set your OpenAI API key:")
        console.print("  export OPENAI_API_KEY='your-key-here'")
        raise typer.Exit(1)
    
    # Create agent config
    config = AgentConfig(
        model_name=model,
        verbose=verbose,
        max_iterations=max_iterations
    )
    
    # Create and run pipeline
    console.print(f"\n[cyan]Repository:[/cyan] {repo_path.resolve()}")
    console.print(f"[cyan]Model:[/cyan] {model}")
    console.print(f"[cyan]Max iterations:[/cyan] {max_iterations}")
    console.print(f"[cyan]Auto-commit:[/cyan] {auto_commit}")
    
    if dry_run:
        console.print("\n[yellow]DRY RUN MODE - No changes will be made[/yellow]")
    
    console.print("\n[cyan]Running initial tests...[/cyan]")
    
    try:
        # Create pipeline
        pipeline = CIRescuePipeline(
            agent_config=config,
            max_iterations=max_iterations,
            auto_commit=auto_commit and not dry_run,
            verbose=verbose
        )
        
        # Run the pipeline
        results = pipeline.run()
        
        # Display results
        _display_results(results)
        
        # Exit with appropriate code
        if results["status"] == "success":
            raise typer.Exit(0)
        else:
            raise typer.Exit(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def test(
    repo_path: Path = typer.Option(
        Path("."),
        "--repo", "-r",
        help="Path to the repository"
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output results as JSON"
    )
):
    """
    Run tests in the sandbox and display results.
    """
    os.chdir(repo_path)
    
    # Update REPO_ROOT in agent tools after changing directory
    from .tools import agent_tools
    agent_tools.REPO_ROOT = Path(".").resolve()
    
    if not json_output:
        console.print("[cyan]Running tests in sandbox...[/cyan]\n")
    
    # Run tests
    result_json = run_tests_tool()
    results = json.loads(result_json)
    
    if json_output:
        print(json.dumps(results, indent=2))
    else:
        _display_test_results(results)
    
    # Exit with test exit code
    raise typer.Exit(results.get("exit_code", 1))


@app.command()
def build_sandbox():
    """
    Build the Docker sandbox image for test execution.
    """
    console.print("[cyan]Building sandbox Docker image...[/cyan]\n")
    
    # Get the sandbox directory
    sandbox_dir = Path(__file__).parent / "sandbox"
    
    if not sandbox_dir.exists():
        console.print(f"[red]Error: Sandbox directory not found: {sandbox_dir}[/red]")
        raise typer.Exit(1)
    
    # Run the build script
    build_script = sandbox_dir / "build.sh"
    if build_script.exists():
        import subprocess
        result = subprocess.run(
            ["bash", str(build_script)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            console.print("[green]✅ Sandbox image built successfully[/green]")
        else:
            console.print(f"[red]Error building sandbox:[/red]")
            console.print(result.stderr)
            raise typer.Exit(1)
    else:
        console.print(f"[red]Build script not found: {build_script}[/red]")
        raise typer.Exit(1)


@app.command()
def version():
    """
    Show version information.
    """
    from . import __version__
    console.print(f"Nova CI-Rescue Deep Agent v{__version__}")
    console.print("Powered by LangChain")


def _display_results(results: dict):
    """Display pipeline results."""
    status = results["status"]
    
    if status == "success":
        console.print(f"\n[green bold]✅ SUCCESS[/green bold]")
        console.print(f"[green]{results['message']}[/green]")
        
        if "iterations" in results and results["iterations"] > 0:
            console.print(f"\n[cyan]Iterations:[/cyan] {results['iterations']}")
            
        if "initial_failing" in results:
            console.print(f"[cyan]Fixed:[/cyan] {results['initial_failing']} failing tests")
            
        if "patch_diff" in results and results["patch_diff"]:
            console.print("\n[cyan]Applied changes:[/cyan]")
            syntax = Syntax(
                results["patch_diff"][:1000],  # Limit display
                "diff",
                theme="monokai",
                line_numbers=False
            )
            console.print(syntax)
            
            if len(results["patch_diff"]) > 1000:
                console.print("[dim]... (truncated)[/dim]")
    else:
        console.print(f"\n[red bold]❌ FAILURE[/red bold]")
        console.print(f"[red]{results['message']}[/red]")
        
        if "remaining_failures" in results:
            console.print(f"\n[yellow]Remaining failures:[/yellow] {results['remaining_failures']}")


def _display_test_results(results: dict):
    """Display test results."""
    exit_code = results.get("exit_code", 1)
    
    if exit_code == 0:
        console.print("[green bold]✅ All tests passed![/green bold]\n")
    else:
        console.print("[red bold]❌ Tests failed[/red bold]\n")
    
    # Display summary if available
    if "test_summary" in results:
        summary = results["test_summary"]
        
        table = Table(title="Test Summary")
        table.add_column("Status", style="cyan")
        table.add_column("Count", justify="right")
        
        table.add_row("Total", str(summary.get("total", 0)))
        table.add_row("Passed", str(summary.get("passed", 0)), style="green")
        table.add_row("Failed", str(summary.get("failed", 0)), style="red")
        table.add_row("Skipped", str(summary.get("skipped", 0)), style="yellow")
        
        if summary.get("errors", 0) > 0:
            table.add_row("Errors", str(summary["errors"]), style="red bold")
        
        console.print(table)
    
    # Display failing tests if any
    if "failing_tests" in results and results["failing_tests"]:
        console.print("\n[red]Failing tests:[/red]")
        for test in results["failing_tests"]:
            console.print(f"  • {test['nodeid']}")
            if test.get("message"):
                # Show first line of error
                first_line = test["message"].split("\n")[0]
                if len(first_line) > 80:
                    first_line = first_line[:77] + "..."
                console.print(f"    [dim]{first_line}[/dim]")


if __name__ == "__main__":
    app()
