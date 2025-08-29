#!/usr/bin/env python3
"""
Simple Demo: Nova CI-Rescue with Real OpenAI LLM Calls
This shows exactly how the LLM generates patches to fix tests.
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax
from nova.config import get_settings
from nova.agent.llm_agent import LLMAgent

console = Console()


def main():
    console.print("\n" + "=" * 70)
    console.print("[bold green]🤖 Nova CI-Rescue - Real OpenAI LLM Demo[/bold green]")
    console.print("=" * 70)

    # Check configuration
    settings = get_settings()
    if not settings.openai_api_key:
        console.print("[red]❌ OpenAI API key not configured![/red]")
        return 1

    console.print(
        f"✅ Using OpenAI Model: [bold cyan]{settings.default_llm_model}[/bold cyan]\n"
    )

    # Example failing test
    failing_test = {
        "name": "test_calculator",
        "file": "test_calc.py",
        "line": 5,
        "short_traceback": """test_calc.py:5: in test_calculator
    assert add(2, 3) == 6, f"Expected 6 but got {add(2, 3)}"
E   AssertionError: Expected 6 but got 5
E   assert 5 == 6""",
    }

    # Show the failing test
    console.print("[bold]📋 Failing Test:[/bold]")
    console.print(f"  Name: {failing_test['name']}")
    console.print(f"  File: {failing_test['file']}")
    console.print("  Error: AssertionError - Expected 6 but got 5\n")

    # Show the test code
    test_code = """def add(a, b):
    return a + b

def test_calculator():
    assert add(2, 3) == 6, f"Expected 6 but got {add(2, 3)}"
"""

    console.print("[bold]📝 Test File Content:[/bold]")
    syntax = Syntax(test_code, "python", theme="monokai", line_numbers=True)
    console.print(syntax)
    console.print()

    # Initialize LLM agent
    try:
        agent = LLMAgent(Path.cwd())
        console.print("[green]✅ LLM Agent initialized[/green]\n")
    except Exception as e:
        console.print(f"[red]❌ Failed to initialize LLM: {e}[/red]")
        return 1

    # Step 1: Ask LLM to analyze and plan
    console.print("=" * 70)
    console.print("[bold cyan]Step 1: LLM Analysis & Planning[/bold cyan]")
    console.print("=" * 70)
    console.print("[dim]Sending test failure to OpenAI for analysis...[/dim]\n")

    try:
        plan = agent.create_plan([failing_test], iteration=1)
        console.print("[bold]🧠 LLM's Analysis:[/bold]")
        console.print(f"  • Approach: {plan.get('approach', 'N/A')}")
        if "strategy" in plan:
            console.print(f"  • Strategy: {plan.get('strategy', 'N/A')}")
        console.print()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1

    # Step 2: Generate patch
    console.print("=" * 70)
    console.print("[bold cyan]Step 2: LLM Patch Generation[/bold cyan]")
    console.print("=" * 70)
    console.print("[dim]Asking OpenAI to generate a fix...[/dim]\n")

    # Create temporary test file for the agent to read
    temp_file = Path("test_calc.py")
    temp_file.write_text(test_code)

    try:
        patch = agent.generate_patch([failing_test], iteration=1)

        if patch:
            console.print("[bold]🔧 Generated Patch:[/bold]")
            syntax = Syntax(patch, "diff", theme="monokai")
            console.print(syntax)
            console.print()

            # Show what the fix does
            if "== 6" in patch and "== 5" in patch:
                console.print("[green]✅ LLM correctly identified the issue:[/green]")
                console.print("   The test expects 6 but add(2,3) returns 5.")
                console.print("   The patch fixes the assertion to expect 5.\n")
            elif "return a + b" in patch:
                console.print("[green]✅ LLM found an alternative fix:[/green]")
                console.print("   Modified the add function to make the test pass.\n")
        else:
            console.print("[yellow]No patch generated[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        # Clean up temp file
        if temp_file.exists():
            temp_file.unlink()

    # Step 3: Review
    if patch:
        console.print("=" * 70)
        console.print("[bold cyan]Step 3: LLM Code Review[/bold cyan]")
        console.print("=" * 70)
        console.print("[dim]Asking OpenAI to review the patch...[/dim]\n")

        try:
            approved, reason = agent.review_patch(patch, [failing_test])

            if approved:
                console.print("[green]✅ Patch Approved[/green]")
            else:
                console.print("[yellow]⚠️ Patch Rejected[/yellow]")
            console.print(f"   Reason: {reason}\n")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    # Summary
    console.print("=" * 70)
    console.print("[bold green]✨ Demo Complete![/bold green]")
    console.print("=" * 70)
    console.print("\n[bold]This demonstration showed:[/bold]")
    console.print("  1️⃣  Real OpenAI API calls to analyze test failures")
    console.print("  2️⃣  Intelligent patch generation to fix the issues")
    console.print("  3️⃣  Automated code review before applying changes")
    console.print("\n[dim]Nova CI-Rescue uses this same process to automatically[/dim]")
    console.print("[dim]fix all failing tests in your repository.[/dim]\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
