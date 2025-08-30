#!/usr/bin/env python3
"""
Visual demo of the Nova CI-Rescue agent loop.
"""

import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()


def show_agent_loop():
    """Demonstrate the agent loop visually."""

    console.print("\n")
    console.print(
        Panel.fit(
            "[bold cyan]Nova CI-Rescue - Agent Loop Demonstration[/bold cyan]\n"
            "[dim]Showing the complete workflow in action[/dim]",
            border_style="cyan",
        )
    )

    # Show initial state
    console.print("\n[bold]📊 Initial State:[/bold]")
    table = Table(show_header=False, box=None)
    table.add_column(style="yellow")
    table.add_column()
    table.add_row("Repository:", "/path/to/repo")
    table.add_row("Branch:", "nova-fix/20250813_150000")
    table.add_row("Failing Tests:", "3")
    table.add_row("Max Iterations:", "6")
    console.print(table)

    time.sleep(1)

    # Simulate iterations
    for iteration in range(1, 3):
        console.print(f"\n[bold blue]━━━ Iteration {iteration}/6 ━━━[/bold blue]\n")

        # 1. PLANNER
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]🧠 PLANNER:[/cyan] Analyzing failing tests..."),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("planning", total=None)
            time.sleep(1)
        console.print("   [green]✓[/green] Generated fix plan for test failures")

        # 2. ACTOR
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]🎭 ACTOR:[/cyan] Generating patch diff..."),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("acting", total=None)
            time.sleep(1)
        console.print("   [green]✓[/green] Created patch with 15 lines changed")

        # 3. CRITIC
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]🔍 CRITIC:[/cyan] Reviewing patch safety..."),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("reviewing", total=None)
            time.sleep(1)
        console.print("   [green]✓[/green] Patch approved (safe, focused changes)")

        # 4. APPLY
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]📝 APPLY:[/cyan] Applying patch to files..."),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("applying", total=None)
            time.sleep(1)
        console.print(
            f"   [green]✓[/green] Committed as: [bold]nova: step {iteration}[/bold]"
        )

        # 5. TEST
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]🧪 TEST:[/cyan] Running test suite..."),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("testing", total=None)
            time.sleep(1)

        if iteration == 1:
            console.print("   [yellow]⚠[/yellow] 1 test still failing (fixed 2/3)")
        else:
            console.print("   [green]✓[/green] All tests passing!")

        # 6. REFLECT
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]🤔 REFLECT:[/cyan] Evaluating progress..."),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("reflecting", total=None)
            time.sleep(0.5)

        if iteration == 1:
            console.print("   [dim]→ Progress made, continuing to next iteration[/dim]")
        else:
            console.print("   [bold green]→ Success! All tests fixed.[/bold green]")
            break

    # Show final state
    console.print("\n[bold green]✅ Agent Loop Complete![/bold green]\n")

    # Git log visualization
    console.print("[bold]📜 Git History (nova-fix branch):[/bold]")
    git_log = Table(show_header=False, box=None)
    git_log.add_column(style="green")
    git_log.add_column(style="cyan")
    git_log.add_column()
    git_log.add_row("abc123", "nova: step 2", "Fixed remaining test failure")
    git_log.add_row("def456", "nova: step 1", "Fixed 2 test failures")
    git_log.add_row("789xyz", "Initial commit", "3 failing tests")
    console.print(git_log)

    # Summary
    console.print("\n[bold]📊 Summary:[/bold]")
    summary = Table(show_header=False, box=None)
    summary.add_column(style="cyan")
    summary.add_column()
    summary.add_row("Total Iterations:", "2")
    summary.add_row("Patches Applied:", "2")
    summary.add_row("Tests Fixed:", "3/3")
    summary.add_row("Final Status:", "[green]SUCCESS[/green]")
    summary.add_row("Branch:", "nova-fix/20250813_150000")
    console.print(summary)

    console.print(
        "\n"
        + Panel(
            "[bold]Key Features Demonstrated:[/bold]\n\n"
            "• Each iteration follows: Plan → Act → Critique → Apply → Test → Reflect\n"
            "• Patches are committed as 'nova: step N' for traceability\n"
            "• Tests are re-run after each patch to verify progress\n"
            "• The loop continues until all tests pass or limits are reached\n"
            "• Full telemetry logging captures every decision and action",
            border_style="dim",
        )
    )


if __name__ == "__main__":
    try:
        show_agent_loop()
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
