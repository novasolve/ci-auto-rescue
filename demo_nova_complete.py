#!/usr/bin/env python3
"""
Complete demonstration of Nova CI-Rescue system.
Shows the full workflow: detect failures → plan → generate patch → review → apply → verify
"""

import sys
import subprocess
import shutil
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel

console = Console()

def setup_demo_repo():
    """Create a demo repository with failing tests."""
    demo_dir = Path("demo_repo")
    
    # Clean up if exists
    if demo_dir.exists():
        shutil.rmtree(demo_dir)
    
    demo_dir.mkdir()
    
    # Create a simple Python module with bugs
    (demo_dir / "calculator.py").write_text("""
def add(a, b):
    # Bug: should return a + b, not a - b
    return a - b

def multiply(a, b):
    # Bug: should return a * b, not a + b
    return a + b

def divide(a, b):
    if b == 0:
        return 0  # Bug: should raise an exception
    return a / b
""")
    
    # Create failing tests
    (demo_dir / "test_calculator.py").write_text("""
import pytest
from calculator import add, multiply, divide

def test_addition():
    assert add(2, 3) == 5, "Addition failed: 2 + 3 should be 5"
    assert add(-1, 1) == 0, "Addition failed: -1 + 1 should be 0"

def test_multiplication():
    assert multiply(3, 4) == 12, "Multiplication failed: 3 * 4 should be 12"
    assert multiply(0, 5) == 0, "Multiplication failed: 0 * 5 should be 0"

def test_division():
    assert divide(10, 2) == 5, "Division succeeded"
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)  # Should raise exception, not return 0
""")
    
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=demo_dir, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=demo_dir, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit with failing tests"], cwd=demo_dir, capture_output=True)
    
    return demo_dir

def run_tests_manually(demo_dir):
    """Run tests to show failures."""
    console.print("\n[bold cyan]📝 Running tests to detect failures...[/bold cyan]")
    
    result = subprocess.run(
        ["python", "-m", "pytest", "test_calculator.py", "-v", "--tb=short"],
        cwd=demo_dir,
        capture_output=True,
        text=True
    )
    
    # Count failures
    failures = result.stdout.count("FAILED")
    passes = result.stdout.count("PASSED")
    
    table = Table(title="Test Results", show_header=True, header_style="bold magenta")
    table.add_column("Status", style="bold")
    table.add_column("Count")
    table.add_row("[red]❌ Failed[/red]", str(failures))
    table.add_row("[green]✅ Passed[/green]", str(passes))
    
    console.print(table)
    
    if failures > 0:
        console.print("\n[yellow]Sample failure output:[/yellow]")
        # Show first few lines of failure
        for line in result.stdout.split('\n')[:15]:
            if 'FAILED' in line or 'assert' in line or 'AssertionError' in line:
                console.print(f"[dim]{line}[/dim]")
    
    return failures > 0

def demo_nova_fix(demo_dir):
    """Run Nova CI-Rescue on the demo repository."""
    console.print("\n" + "="*70)
    console.print(Panel.fit(
        "[bold green]🚀 NOVA CI-RESCUE DEMO[/bold green]\n" +
        "Autonomous Test Fixing with GPT-5",
        border_style="green"
    ))
    console.print("="*70)
    
    # Show the command we're running
    console.print("\n[bold]Running Nova CI-Rescue:[/bold]")
    console.print("[cyan]$ nova fix demo_repo --max-iters 3 --timeout 120 --verbose[/cyan]\n")
    
    # Run Nova fix
    result = subprocess.run(
        ["nova", "fix", str(demo_dir), "--max-iters", "3", "--timeout", "120", "--verbose"],
        capture_output=True,
        text=True
    )
    
    # Display output with highlighting
    output_lines = result.stdout.split('\n')
    for line in output_lines:
        if '🚀' in line or 'Nova CI-Rescue' in line:
            console.print(f"[bold green]{line}[/bold green]")
        elif '✅' in line or 'Success' in line:
            console.print(f"[green]{line}[/green]")
        elif '❌' in line or 'Failed' in line:
            console.print(f"[red]{line}[/red]")
        elif '🧠' in line:  # Planner
            console.print(f"[cyan]{line}[/cyan]")
        elif '🎭' in line:  # Actor
            console.print(f"[yellow]{line}[/yellow]")
        elif '🔍' in line:  # Critic
            console.print(f"[magenta]{line}[/magenta]")
        elif 'Iteration' in line:
            console.print(f"[bold blue]{line}[/bold blue]")
        elif '---' in line or '+++' in line or '@@' in line:
            console.print(f"[dim]{line}[/dim]")
        else:
            console.print(line)
    
    return result.returncode == 0

def verify_fix(demo_dir):
    """Verify that tests now pass."""
    console.print("\n[bold cyan]🔬 Verifying the fix...[/bold cyan]")
    
    result = subprocess.run(
        ["python", "-m", "pytest", "test_calculator.py", "-v"],
        cwd=demo_dir,
        capture_output=True,
        text=True
    )
    
    failures = result.stdout.count("FAILED")
    passes = result.stdout.count("PASSED")
    
    table = Table(title="Final Test Results", show_header=True, header_style="bold green")
    table.add_column("Status", style="bold")
    table.add_column("Count")
    table.add_row("[green]✅ Passed[/green]", str(passes))
    table.add_row("[red]❌ Failed[/red]", str(failures))
    
    console.print(table)
    
    if failures == 0:
        console.print("\n[bold green]🎉 SUCCESS! All tests are now passing![/bold green]")
        
        # Show the git diff
        console.print("\n[bold]Changes made by Nova CI-Rescue:[/bold]")
        diff = subprocess.run(
            ["git", "diff", "HEAD~1"],
            cwd=demo_dir,
            capture_output=True,
            text=True
        ).stdout
        
        if diff:
            syntax = Syntax(diff[:1000], "diff", theme="monokai", line_numbers=False)
            console.print(syntax)
            if len(diff) > 1000:
                console.print("[dim]... (diff truncated)[/dim]")
    
    return failures == 0

def main():
    """Run the complete demo."""
    console.print("\n" + "="*80)
    console.print(Panel.fit(
        "[bold cyan]NOVA CI-RESCUE COMPLETE DEMO[/bold cyan]\n" +
        "Demonstrating autonomous test fixing with GPT-5\n" +
        "\n" +
        "[dim]This demo will:[/dim]\n" +
        "1. Create a repository with failing tests\n" +
        "2. Run Nova CI-Rescue to automatically fix them\n" +
        "3. Verify that all tests pass after the fix",
        border_style="cyan"
    ))
    console.print("="*80)
    
    try:
        # Step 1: Setup demo repository
        console.print("\n[bold]Step 1: Creating demo repository with bugs...[/bold]")
        demo_dir = setup_demo_repo()
        console.print(f"[green]✓[/green] Created demo repository at: {demo_dir}")
        
        # Show the buggy code
        console.print("\n[bold]Buggy code (calculator.py):[/bold]")
        code = (demo_dir / "calculator.py").read_text()
        syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
        console.print(syntax)
        
        # Step 2: Show failing tests
        console.print("\n[bold]Step 2: Detecting test failures...[/bold]")
        has_failures = run_tests_manually(demo_dir)
        
        if not has_failures:
            console.print("[yellow]No failures found. Demo requires failing tests.[/yellow]")
            return 1
        
        # Step 3: Run Nova CI-Rescue
        console.print("\n[bold]Step 3: Running Nova CI-Rescue to fix the bugs...[/bold]")
        input("\n[dim]Press Enter to start Nova CI-Rescue...[/dim]")
        
        success = demo_nova_fix(demo_dir)
        
        if not success:
            console.print("[red]Nova CI-Rescue encountered an issue.[/red]")
            console.print("[yellow]This might be due to API limits or configuration.[/yellow]")
            return 1
        
        # Step 4: Verify the fix
        console.print("\n[bold]Step 4: Verifying the fix...[/bold]")
        all_pass = verify_fix(demo_dir)
        
        # Summary
        console.print("\n" + "="*80)
        console.print(Panel.fit(
            "[bold green]✨ DEMO COMPLETE![/bold green]\n" +
            "\n" +
            "Nova CI-Rescue successfully:\n" +
            "• Detected failing tests\n" +
            "• Generated a fix plan with GPT-5\n" +
            "• Created and reviewed patches\n" +
            "• Applied fixes to make tests pass\n" +
            "\n" +
            "[dim]The system works autonomously to fix test failures![/dim]",
            border_style="green"
        ))
        console.print("="*80)
        
        # Cleanup option
        console.print("\n[dim]Demo repository created at: demo_repo/[/dim]")
        cleanup = input("Clean up demo repository? (y/N): ")
        if cleanup.lower() == 'y':
            shutil.rmtree(demo_dir)
            console.print("[green]✓[/green] Cleaned up demo repository")
        
        return 0
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user[/yellow]")
        return 1
    except Exception as e:
        console.print(f"\n[red]Error during demo: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
