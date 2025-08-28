#!/usr/bin/env python3
"""
Demo script showing Nova CI-Rescue with real LLM calls.
"""

import sys
from pathlib import Path
from rich.console import Console
from nova.config import get_settings
from nova.agent.llm_agent import LLMAgent

console = Console()

def main():
    console.print("\n[bold green]Nova CI-Rescue - Real LLM Demo[/bold green] 🤖")
    console.print("=" * 60)
    
    # Check configuration
    settings = get_settings()
    if not settings.openai_api_key:
        console.print("[red]❌ OpenAI API key not configured![/red]")
        console.print("Please set OPENAI_API_KEY in your .env file")
        return 1
    
    console.print(f"✅ OpenAI API configured")
    console.print(f"📊 Using model: {settings.default_llm_model}")
    console.print()
    
    # Create sample failing tests
    failing_tests = [
        {
            "name": "test_simple_assertion_failure",
            "file": "tests/test_sample.py",
            "line": 12,
            "short_traceback": """tests/test_sample.py:12: in test_simple_assertion_failure
    assert result == 5, f"Expected 5 but got {result}"
E   AssertionError: Expected 5 but got 4
E   assert 4 == 5"""
        },
        {
            "name": "test_division_by_zero",
            "file": "tests/test_sample.py",
            "line": 18,
            "short_traceback": """tests/test_sample.py:18: in test_division_by_zero
    result = numerator / denominator  # This will raise ZeroDivisionError
             ^^^^^^^^^^^^^^^^^^^^^^^
E   ZeroDivisionError: division by zero"""
        }
    ]
    
    # Initialize LLM agent
    try:
        console.print("[cyan]Initializing LLM agent...[/cyan]")
        agent = LLMAgent(Path.cwd())
        console.print("[green]✓ LLM agent initialized[/green]")
    except Exception as e:
        console.print(f"[red]❌ Failed to initialize LLM agent: {e}[/red]")
        return 1
    
    console.print()
    console.print("[bold]Step 1: Planning[/bold]")
    console.print("-" * 40)
    
    # Create a plan using LLM
    try:
        console.print("[cyan]🧠 Asking LLM to create a plan...[/cyan]")
        plan = agent.create_plan(failing_tests, iteration=1)
        console.print("[green]✓ Plan created:[/green]")
        console.print(f"  Approach: {plan.get('approach', 'N/A')}")
        if 'strategy' in plan:
            console.print(f"  Strategy: {plan.get('strategy', 'N/A')}")
    except Exception as e:
        console.print(f"[red]❌ Error creating plan: {e}[/red]")
    
    console.print()
    console.print("[bold]Step 2: Generate Patch[/bold]")
    console.print("-" * 40)
    
    # Generate patch using LLM
    try:
        console.print("[cyan]🎭 Asking LLM to generate a patch...[/cyan]")
        patch = agent.generate_patch(failing_tests, iteration=1)
        
        if patch:
            console.print("[green]✓ Patch generated:[/green]")
            console.print()
            console.print("[dim]--- Patch Preview ---[/dim]")
            # Show first 20 lines of patch
            lines = patch.split('\n')[:20]
            for line in lines:
                if line.startswith('+'):
                    console.print(f"[green]{line}[/green]")
                elif line.startswith('-'):
                    console.print(f"[red]{line}[/red]")
                else:
                    console.print(f"[dim]{line}[/dim]")
            if len(patch.split('\n')) > 20:
                console.print("[dim]... (truncated)[/dim]")
        else:
            console.print("[yellow]⚠️ No patch generated[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error generating patch: {e}[/red]")
        import traceback
        traceback.print_exc()
    
    console.print()
    console.print("[bold]Step 3: Review Patch[/bold]")
    console.print("-" * 40)
    
    # Review patch using LLM
    if patch:
        try:
            console.print("[cyan]🔍 Asking LLM to review the patch...[/cyan]")
            approved, reason = agent.review_patch(patch, failing_tests)
            
            if approved:
                console.print(f"[green]✅ Patch approved: {reason}[/green]")
            else:
                console.print(f"[yellow]⚠️ Patch rejected: {reason}[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Error reviewing patch: {e}[/red]")
    
    console.print()
    console.print("=" * 60)
    console.print("[bold green]Demo complete![/bold green]")
    console.print()
    console.print("This demonstrates how Nova CI-Rescue uses real LLM calls to:")
    console.print("  1. Plan the fix approach")
    console.print("  2. Generate patches to fix failing tests")
    console.print("  3. Review patches before applying them")
    console.print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
