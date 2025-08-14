#!/usr/bin/env python3
"""
Direct demonstration of GPT-5 fixing tests.
Shows the actual LLM calls and patches generated.
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax
from nova.config import get_settings
from nova.agent.llm_agent import LLMAgent
import subprocess

console = Console()

def main():
    console.print("\n" + "="*70)
    console.print("[bold green]🚀 Nova CI-Rescue with GPT-5 - Live Demo[/bold green]")
    console.print("="*70)
    
    # Check configuration
    settings = get_settings()
    if not settings.openai_api_key:
        console.print("[red]❌ OpenAI API key not configured![/red]")
        return 1
    
    console.print(f"✅ Using Model: [bold cyan]{settings.default_llm_model}[/bold cyan]")
    console.print()
    
    # Show current failing tests
    console.print("[bold]📋 Current Test Status:[/bold]")
    result = subprocess.run(
        ["python", "-m", "pytest", "test_gpt5_demo.py", "-v", "--tb=no"],
        capture_output=True,
        text=True
    )
    
    # Count failures
    failures = result.stdout.count("FAILED")
    console.print(f"  • Tests found: 3")
    console.print(f"  • [red]Failing: {failures}[/red]")
    console.print()
    
    # Get the failing test details
    failing_tests = [
        {
            "name": "test_basic_math",
            "file": "test_gpt5_demo.py",
            "line": 8,
            "short_traceback": "AssertionError: Expected 15 but got 12\nassert 12 == 15"
        },
        {
            "name": "test_string_concat",
            "file": "test_gpt5_demo.py",
            "line": 15,
            "short_traceback": "AssertionError: Expected 'Hi GPT-5' but got 'Hello GPT-5'"
        },
        {
            "name": "test_list_operations",
            "file": "test_gpt5_demo.py",
            "line": 21,
            "short_traceback": "AssertionError: Expected 100 but got 60\nassert 60 == 100"
        }
    ]
    
    # Initialize LLM agent
    try:
        agent = LLMAgent(Path.cwd())
        console.print("[green]✅ GPT-5 Agent initialized[/green]\n")
    except Exception as e:
        console.print(f"[red]❌ Failed to initialize: {e}[/red]")
        return 1
    
    console.print("="*70)
    console.print("[bold cyan]🧠 Step 1: GPT-5 Analysis[/bold cyan]")
    console.print("="*70)
    
    try:
        plan = agent.create_plan(failing_tests, iteration=1)
        console.print("[bold]GPT-5's Analysis:[/bold]")
        for key, value in plan.items():
            console.print(f"  • {key}: {value}")
        console.print()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    
    console.print("="*70)
    console.print("[bold cyan]🔧 Step 2: GPT-5 Patch Generation[/bold cyan]")
    console.print("="*70)
    
    try:
        console.print("[dim]GPT-5 is analyzing the code and generating fixes...[/dim]\n")
        patch = agent.generate_patch(failing_tests, iteration=1)
        
        if patch:
            console.print("[bold]Generated Patch:[/bold]")
            # Show the patch with syntax highlighting
            syntax = Syntax(patch[:800], "diff", theme="monokai")
            console.print(syntax)
            if len(patch) > 800:
                console.print("[dim]... (truncated)[/dim]")
            console.print()
            
            # Apply the patch
            console.print("[cyan]📝 Applying patch...[/cyan]")
            # Save the patch to a file
            patch_file = Path("gpt5_fix.patch")
            patch_file.write_text(patch)
            
            # Try to apply with git apply
            result = subprocess.run(
                ["git", "apply", "--check", "gpt5_fix.patch"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                subprocess.run(["git", "apply", "gpt5_fix.patch"])
                console.print("[green]✅ Patch applied successfully![/green]\n")
                
                # Run tests again
                console.print("[bold]📊 Test Status After GPT-5 Fix:[/bold]")
                result = subprocess.run(
                    ["python", "-m", "pytest", "test_gpt5_demo.py", "-v", "--tb=no"],
                    capture_output=True,
                    text=True
                )
                
                failures_after = result.stdout.count("FAILED")
                passed_after = result.stdout.count("PASSED")
                
                console.print(f"  • [green]Passing: {passed_after}[/green]")
                console.print(f"  • [red]Failing: {failures_after}[/red]")
                
                if failures_after == 0:
                    console.print("\n[bold green]🎉 SUCCESS! All tests fixed by GPT-5![/bold green]")
                else:
                    console.print(f"\n[yellow]Partial success: Fixed {failures - failures_after} tests[/yellow]")
                
                # Clean up
                subprocess.run(["git", "checkout", "--", "test_gpt5_demo.py"], capture_output=True)
                patch_file.unlink(missing_ok=True)
            else:
                console.print(f"[yellow]Could not apply patch: {result.stderr}[/yellow]")
                patch_file.unlink(missing_ok=True)
        else:
            console.print("[yellow]No patch generated[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    
    console.print()
    console.print("="*70)
    console.print("[bold green]✨ GPT-5 Demo Complete![/bold green]")
    console.print("="*70)
    console.print("\n[bold]Key Takeaways:[/bold]")
    console.print("  • GPT-5 provides sophisticated code analysis")
    console.print("  • Generates context-aware patches")
    console.print("  • Can fix multiple test failures in one iteration")
    console.print("  • Understands complex test expectations\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
