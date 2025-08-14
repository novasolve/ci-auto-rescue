#!/usr/bin/env python3
"""
Quick demo of Nova CI-Rescue components without requiring API keys.
Shows the workflow and architecture.
"""

import time
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def simulate_test_discovery():
    """Simulate test discovery phase."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Running pytest to discover failures...", total=None)
        time.sleep(2)
    
    failures = [
        {"name": "test_addition", "file": "test_math.py", "line": 5, "error": "assert 2 + 2 == 5"},
        {"name": "test_string_concat", "file": "test_string.py", "line": 10, "error": "assert 'hello' + 'world' == 'hello world'"},
        {"name": "test_list_sum", "file": "test_lists.py", "line": 15, "error": "assert sum([1,2,3]) == 10"}
    ]
    
    table = Table(title="Failing Tests Detected", show_header=True, header_style="bold red")
    table.add_column("Test", style="cyan")
    table.add_column("File", style="yellow")
    table.add_column("Error", style="red")
    
    for test in failures:
        table.add_row(test["name"], f"{test['file']}:{test['line']}", test["error"])
    
    console.print(table)
    return failures

def simulate_planner(failures):
    """Simulate the Planner component."""
    console.print("\n[bold cyan]🧠 PLANNER: Analyzing failures and creating strategy...[/bold cyan]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[dim]Calling GPT-5 to analyze test failures...", total=None)
        time.sleep(1.5)
    
    plan = {
        "approach": "Fix arithmetic operations and string concatenation",
        "priority": ["test_addition", "test_string_concat"],
        "strategy": {
            "test_addition": "Change arithmetic to make 2+2=5 (or fix test expectation)",
            "test_string_concat": "Add space between concatenated strings",
            "test_list_sum": "Adjust list values or expected sum"
        }
    }
    
    console.print(Panel(
        f"[bold]Generated Plan:[/bold]\n\n" +
        f"[yellow]Approach:[/yellow] {plan['approach']}\n" +
        f"[yellow]Priority:[/yellow] {', '.join(plan['priority'])}\n\n" +
        "[yellow]Fix Strategy:[/yellow]\n" +
        "\n".join([f"  • {k}: {v}" for k, v in plan['strategy'].items()]),
        title="🧠 Planner Output",
        border_style="cyan"
    ))
    
    return plan

def simulate_actor(plan, failures):
    """Simulate the Actor component generating a patch."""
    console.print("\n[bold yellow]🎭 ACTOR: Generating patch based on plan...[/bold yellow]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[dim]Calling GPT-5 to generate fix patch...", total=None)
        time.sleep(2)
    
    patch = """--- a/math_ops.py
+++ b/math_ops.py
@@ -1,5 +1,5 @@
 def add(a, b):
-    return a + b - 1  # Bug here
+    return a + b  # Fixed
 
 def concat_strings(s1, s2):
-    return s1 + s2
+    return s1 + ' ' + s2  # Added space
 
--- a/list_ops.py
+++ b/list_ops.py
@@ -1,3 +1,3 @@
 def sum_list(lst):
-    return sum(lst) * 2 - 6  # Wrong calculation
+    return sum(lst) + 4  # Adjusted for test"""
    
    console.print(Panel(
        Syntax(patch, "diff", theme="monokai"),
        title="🎭 Generated Patch",
        border_style="yellow"
    ))
    
    return patch

def simulate_critic(patch):
    """Simulate the Critic component reviewing the patch."""
    console.print("\n[bold magenta]🔍 CRITIC: Reviewing patch for safety and correctness...[/bold magenta]")
    
    checks = [
        ("Patch size check", "✅ 15 lines (under 1000 limit)", True),
        ("Files modified", "✅ 2 files (under 5 limit)", True),
        ("Protected files", "✅ No CI/config files modified", True),
        ("Code quality", "✅ Changes look reasonable", True),
        ("Test alignment", "✅ Fixes match test expectations", True)
    ]
    
    table = Table(title="Critic Review", show_header=True, header_style="bold magenta")
    table.add_column("Check", style="cyan")
    table.add_column("Result", style="green")
    
    for check, result, passed in checks:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"[dim]Checking: {check}...", total=None)
            time.sleep(0.5)
        table.add_row(check, result)
    
    console.print(table)
    console.print("\n[green]✅ Patch APPROVED by Critic[/green]")
    
    return True

def simulate_apply_and_test(patch):
    """Simulate applying the patch and running tests."""
    console.print("\n[bold]📝 Applying patch and running tests...[/bold]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[dim]Applying patch with git apply...", total=None)
        time.sleep(1)
        progress.update(task, description="[dim]Running pytest to verify fix...")
        time.sleep(1.5)
    
    results = {
        "test_addition": "PASSED",
        "test_string_concat": "PASSED",
        "test_list_sum": "PASSED"
    }
    
    table = Table(title="Test Results After Fix", show_header=True, header_style="bold green")
    table.add_column("Test", style="cyan")
    table.add_column("Status", style="green")
    
    for test, status in results.items():
        table.add_row(test, f"✅ {status}")
    
    console.print(table)
    
    return all(s == "PASSED" for s in results.values())

def main():
    """Run the architecture demo."""
    console.print("\n" + "="*80)
    console.print(Panel.fit(
        "[bold cyan]NOVA CI-RESCUE ARCHITECTURE DEMO[/bold cyan]\n" +
        "Demonstrating the Planner → Actor → Critic workflow\n" +
        "\n" +
        "[dim]This demo simulates the components without requiring API keys[/dim]",
        border_style="cyan"
    ))
    console.print("="*80)
    
    # Step 1: Test Discovery
    console.print("\n[bold]📊 PHASE 1: Test Discovery[/bold]")
    console.print("[dim]Nova detects failing tests in the repository...[/dim]\n")
    failures = simulate_test_discovery()
    
    # Step 2: Planning
    console.print("\n[bold]🧠 PHASE 2: Planning[/bold]")
    console.print("[dim]The Planner analyzes failures and creates a fix strategy...[/dim]")
    plan = simulate_planner(failures)
    
    # Step 3: Patch Generation
    console.print("\n[bold]🎭 PHASE 3: Patch Generation[/bold]")
    console.print("[dim]The Actor generates code changes based on the plan...[/dim]")
    patch = simulate_actor(plan, failures)
    
    # Step 4: Review
    console.print("\n[bold]🔍 PHASE 4: Patch Review[/bold]")
    console.print("[dim]The Critic reviews the patch for safety and correctness...[/dim]")
    approved = simulate_critic(patch)
    
    if not approved:
        console.print("[red]❌ Patch rejected by Critic[/red]")
        return 1
    
    # Step 5: Apply and Verify
    console.print("\n[bold]✅ PHASE 5: Apply and Verify[/bold]")
    console.print("[dim]Apply the approved patch and run tests...[/dim]")
    success = simulate_apply_and_test(patch)
    
    # Summary
    console.print("\n" + "="*80)
    console.print(Panel.fit(
        "[bold green]✨ WORKFLOW COMPLETE![/bold green]\n" +
        "\n" +
        "The Nova CI-Rescue workflow:\n" +
        "1. 📊 Discovered 3 failing tests\n" +
        "2. 🧠 Planner created fix strategy\n" +
        "3. 🎭 Actor generated patch (15 lines)\n" +
        "4. 🔍 Critic approved the patch\n" +
        "5. ✅ All tests now passing!\n" +
        "\n" +
        "[dim]Time: ~8 seconds (with actual LLM: 30-60 seconds)[/dim]",
        border_style="green"
    ))
    console.print("="*80)
    
    console.print("\n[bold]Key Features Demonstrated:[/bold]")
    features = [
        ("Autonomous Operation", "No human intervention required"),
        ("Safety Guardrails", "File limits, size limits, protected files"),
        ("Iterative Fixes", "Can retry if tests still fail"),
        ("LLM Integration", "Uses GPT-5 for intelligent fixes"),
        ("Git Integration", "Creates branches, commits patches")
    ]
    
    for feature, description in features:
        console.print(f"  • [cyan]{feature}:[/cyan] {description}")
    
    console.print("\n[dim]This was a simulation. Run 'nova fix' on a real repository to see it in action![/dim]\n")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
