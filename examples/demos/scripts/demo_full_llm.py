#!/usr/bin/env python3
"""
Complete E2E Demo of Nova CI-Rescue with Real LLM Integration
Shows the full workflow of automatically fixing failing tests using OpenAI.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from rich.console import Console
from rich.table import Table
import time

console = Console()


def run_command(cmd, cwd=None, capture=True):
    """Run a shell command and return the result."""
    if capture:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True
        )
        return result.returncode, result.stdout, result.stderr
    else:
        return subprocess.run(cmd, shell=True, cwd=cwd).returncode, "", ""


def setup_demo_repo():
    """Create a demo repository with failing tests."""
    console.print("\n[bold cyan]📁 Setting Up Demo Repository[/bold cyan]")
    console.print("=" * 60)

    demo_dir = Path("demo_llm_repo")

    # Clean up if exists
    if demo_dir.exists():
        shutil.rmtree(demo_dir)

    demo_dir.mkdir()
    console.print(f"✅ Created demo directory: {demo_dir}")

    # Create a test file with various failures
    test_file = demo_dir / "test_failures.py"
    test_content = '''"""
Tests with intentional failures for Nova CI-Rescue LLM demo.
"""

def test_passing():
    """This test passes."""
    assert True

def test_math_error():
    """Math calculation test that fails."""
    def calculate_area(length, width):
        return length + width  # Bug: should be multiplication

    area = calculate_area(5, 3)
    assert area == 15, f"Expected 15 but got {area}"

def test_string_operation():
    """String operation test that fails."""
    def format_greeting(name):
        return f"Hello {name}"

    greeting = format_greeting("World")
    assert greeting == "Hi World", f"Expected 'Hi World' but got '{greeting}'"

def test_list_sum():
    """List operation test that fails."""
    numbers = [1, 2, 3, 4, 5]
    total = sum(numbers)
    assert total == 20, f"Expected 20 but got {total}"

def test_division():
    """Division test that fails."""
    def safe_divide(a, b):
        return a / b  # No zero check

    result = safe_divide(10, 0)
    assert result == 0, "Should handle division by zero"
'''

    test_file.write_text(test_content)
    console.print("✅ Created test file with 4 failing tests")

    # Initialize git repo
    run_command("git init", cwd=demo_dir)
    run_command("git add .", cwd=demo_dir)
    run_command('git commit -m "Initial commit with failing tests"', cwd=demo_dir)
    console.print("✅ Initialized git repository")

    return demo_dir


def show_test_status(demo_dir):
    """Show current test status."""
    console.print("\n[bold cyan]🧪 Current Test Status[/bold cyan]")
    console.print("=" * 60)

    code, stdout, stderr = run_command(
        "python -m pytest test_failures.py -v --tb=no", cwd=demo_dir
    )

    # Parse results
    output = stdout + stderr
    passed = failed = 0
    for line in output.split("\n"):
        if "passed" in line and "failed" in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if "failed" in part and i > 0:
                    failed = int(parts[i - 1])
                if "passed" in part and i > 0:
                    passed = int(parts[i - 1])

    # Create status table
    table = Table(title="Test Results")
    table.add_column("Status", style="bold")
    table.add_column("Count", justify="right")
    table.add_row("[green]Passed[/green]", str(passed))
    table.add_row("[red]Failed[/red]", str(failed))
    table.add_row("[bold]Total[/bold]", str(passed + failed))

    console.print(table)
    return failed > 0


def run_nova_fix_with_llm(demo_dir):
    """Run nova fix with real LLM integration."""
    console.print("\n[bold cyan]🤖 Running Nova Fix with OpenAI LLM[/bold cyan]")
    console.print("=" * 60)

    os.chdir(demo_dir)

    # Show the command we're running
    console.print("[dim]Command: nova fix . --max-iters 3 --timeout 300[/dim]")
    console.print()

    # Run nova fix (this will use real LLM if available)
    code, stdout, stderr = run_command(
        f"cd {demo_dir} && python -m nova.cli fix . --max-iters 3 --timeout 300",
        capture=True,
    )

    # Parse and display output
    lines = stdout.split("\n")
    for line in lines:
        if "Planning fix" in line:
            console.print(f"[cyan]{line}[/cyan]")
        elif "Generating patch" in line:
            console.print(f"[yellow]{line}[/yellow]")
        elif "Reviewing patch" in line:
            console.print(f"[magenta]{line}[/magenta]")
        elif "Patch approved" in line:
            console.print(f"[green]{line}[/green]")
        elif "All tests passing" in line:
            console.print(f"[bold green]{line}[/bold green]")
        elif "iteration" in line.lower():
            console.print(f"[blue]{line}[/blue]")

    return code == 0


def show_git_history(demo_dir):
    """Show what changes were made."""
    console.print("\n[bold cyan]📝 Git History - Changes Made by Nova[/bold cyan]")
    console.print("=" * 60)

    code, stdout, stderr = run_command("git log --oneline --graph -5", cwd=demo_dir)

    console.print(stdout)

    # Show the actual patch
    console.print("\n[bold]Last Patch Applied:[/bold]")
    code, stdout, stderr = run_command(
        "git diff HEAD~1 test_failures.py | head -30", cwd=demo_dir
    )

    for line in stdout.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            console.print(f"[green]{line}[/green]")
        elif line.startswith("-") and not line.startswith("---"):
            console.print(f"[red]{line}[/red]")
        else:
            console.print(f"[dim]{line}[/dim]")


def main():
    """Main demo flow."""
    console.print("\n" + "=" * 60)
    console.print(
        "[bold green]🚀 Nova CI-Rescue with Real LLM - Complete Demo[/bold green]"
    )
    console.print("=" * 60)

    # Check OpenAI configuration
    from nova.config import get_settings

    settings = get_settings()

    if not settings.openai_api_key:
        console.print("[red]❌ OpenAI API key not configured![/red]")
        console.print("Please set OPENAI_API_KEY in your .env file")
        return 1

    console.print(
        f"✅ Using OpenAI GPT Model: [bold]{settings.default_llm_model}[/bold]"
    )
    console.print()

    try:
        # Step 1: Setup demo repo
        demo_dir = setup_demo_repo()

        # Step 2: Show initial failing tests
        console.print("\n[bold]BEFORE: Initial State[/bold]")
        has_failures = show_test_status(demo_dir)
        if not has_failures:
            console.print("[yellow]⚠️ No failures to fix![/yellow]")
            return 1

        # Step 3: Run Nova Fix with LLM
        time.sleep(1)  # Pause for effect
        success = run_nova_fix_with_llm(demo_dir)

        if success:
            # Step 4: Show final passing tests
            console.print("\n[bold]AFTER: Final State[/bold]")
            show_test_status(demo_dir)

            # Step 5: Show git history
            show_git_history(demo_dir)

            console.print("\n" + "=" * 60)
            console.print(
                "[bold green]✅ SUCCESS![/bold green] Nova CI-Rescue with LLM fixed all tests!"
            )
            console.print("=" * 60)
            console.print()
            console.print("[bold]Key Achievements:[/bold]")
            console.print("  • Used real OpenAI API calls for intelligent analysis")
            console.print("  • Automatically generated patches to fix test failures")
            console.print("  • Applied critic review before accepting patches")
            console.print("  • Successfully turned red tests green")
            console.print()
            console.print(f"[dim]Demo repository: {demo_dir}[/dim]")
        else:
            console.print("[red]❌ Nova fix did not complete successfully[/red]")
            return 1

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
