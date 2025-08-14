#!/usr/bin/env python3
"""
Demo script for Nova CI-Rescue telemetry system.
Shows how the enhanced telemetry captures the full agent loop.
"""

import json
from pathlib import Path
from datetime import datetime
from rich.console import Console

from src.nova.config import NovaSettings
from src.nova.telemetry.logger import JSONLLogger
from src.nova.agent.state import AgentState
from src.nova.nodes import (
    PlannerNode,
    ActorNode, 
    CriticNode,
    ApplyPatchNode,
    RunTestsNode,
    ReflectNode
)

console = Console()


def demo_telemetry():
    """Demonstrate the telemetry system with a simulated agent loop."""
    
    console.print("[bold green]Nova CI-Rescue Telemetry Demo[/bold green]\n")
    
    # Initialize telemetry
    settings = NovaSettings()
    logger = JSONLLogger(settings, enabled=True)
    
    # Create a test repository path
    repo_path = Path("./demo_test_repo")
    
    # Start telemetry run
    run_id = logger.start_run(repo_path)
    console.print(f"[cyan]Started telemetry run: {run_id}[/cyan]")
    console.print(f"[cyan]Telemetry directory: {logger.run_dir}[/cyan]\n")
    
    # Initialize agent state
    state = AgentState(
        repo_path=repo_path,
        max_iterations=3,
        timeout_seconds=600
    )
    
    # Simulate test discovery
    console.print("[bold]Phase 1: Test Discovery[/bold]")
    logger.log_event("test_discovery", {
        "total_failures": 3,
        "failing_tests": [
            {"name": "test_addition", "file": "test_math.py", "line": 10},
            {"name": "test_subtraction", "file": "test_math.py", "line": 20},
            {"name": "test_multiplication", "file": "test_math.py", "line": 30}
        ]
    })
    console.print("  ✓ Found 3 failing tests\n")
    
    # Add failing tests to state
    state.add_failing_tests([
        {"name": "test_addition", "file": "test_math.py", "line": 10, "short_traceback": "AssertionError: 2 + 2 != 5"},
        {"name": "test_subtraction", "file": "test_math.py", "line": 20, "short_traceback": "AssertionError: 5 - 3 != 1"},
        {"name": "test_multiplication", "file": "test_math.py", "line": 30, "short_traceback": "AssertionError: 3 * 3 != 10"}
    ])
    
    # Simulate 2 iterations of the agent loop
    console.print("[bold]Phase 2: Agent Loop[/bold]")
    
    for iteration in range(1, 3):
        state.current_iteration = iteration
        console.print(f"\n[blue]━━━ Iteration {iteration} ━━━[/blue]")
        
        # 1. PLANNER
        console.print("  🧠 Planning...")
        logger.log_event("planner_start", {
            "iteration": iteration,
            "failing_tests_count": len(state.failing_tests)
        })
        
        logger.log_event("planner_complete", {
            "iteration": iteration,
            "plan": {
                "approach": "Fix mathematical operations",
                "steps": ["Fix addition", "Fix subtraction", "Fix multiplication"]
            }
        })
        
        # 2. ACTOR
        console.print("  🎭 Generating patch...")
        logger.log_event("actor_start", {"iteration": iteration})
        
        # Simulate patch generation
        patch_diff = """--- a/math_ops.py
+++ b/math_ops.py
@@ -1,5 +1,5 @@
 def add(a, b):
-    return a + b + 1  # Bug here
+    return a + b  # Fixed
 
 def subtract(a, b):
     return a - b"""
        
        logger.log_event("actor_complete", {
            "iteration": iteration,
            "patch_metrics": {
                "total_lines": 10,
                "added_lines": 1,
                "removed_lines": 1,
                "affected_files": ["math_ops.py"],
                "affected_files_count": 1
            }
        })
        
        # Save patch artifact
        logger.save_patch(iteration, patch_diff)
        
        # 3. CRITIC
        console.print("  🔍 Reviewing patch...")
        logger.log_event("critic_start", {"iteration": iteration})
        
        logger.log_event("critic_approved", {
            "iteration": iteration,
            "approved": True,
            "reason": "Patch correctly fixes the addition bug"
        })
        
        # 4. APPLY
        console.print("  📝 Applying patch...")
        logger.log_event("patch_applied", {
            "iteration": iteration,
            "step": iteration,
            "files_changed": ["math_ops.py"]
        })
        
        # 5. RUN TESTS
        console.print("  🧪 Running tests...")
        logger.log_event("run_tests_start", {
            "iteration": iteration,
            "step_number": iteration
        })
        
        # Simulate test results
        if iteration == 1:
            # First iteration fixes 1 test
            remaining_failures = 2
            tests_fixed = ["test_addition"]
            tests_still_failing = ["test_subtraction", "test_multiplication"]
        else:
            # Second iteration fixes remaining tests
            remaining_failures = 0
            tests_fixed = ["test_subtraction", "test_multiplication"]
            tests_still_failing = []
        
        # Save test report
        junit_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="pytest" tests="3" failures="{remaining_failures}">
  <testcase name="test_addition" time="0.01"/>
  <testcase name="test_subtraction" time="0.01"/>
  <testcase name="test_multiplication" time="0.01"/>
</testsuite>"""
        logger.save_test_report(iteration, junit_xml)
        
        logger.log_event("run_tests_complete", {
            "iteration": iteration,
            "metrics": {
                "total_failures": remaining_failures,
                "tests_fixed_count": len(tests_fixed),
                "tests_still_failing_count": len(tests_still_failing)
            },
            "tests_fixed": tests_fixed,
            "tests_still_failing": tests_still_failing
        })
        
        # Update state
        if remaining_failures == 0:
            state.failing_tests = []
        else:
            state.failing_tests = [t for t in state.failing_tests if t["name"] in tests_still_failing]
        
        # 6. REFLECT
        console.print("  🤔 Reflecting...")
        logger.log_event("reflect_start", {
            "iteration": iteration,
            "current_failures": remaining_failures
        })
        
        if remaining_failures == 0:
            logger.log_event("reflect_complete", {
                "iteration": iteration,
                "decision": "success",
                "reason": "all_tests_passing"
            })
            console.print("  [green]✅ All tests passing![/green]")
            break
        else:
            logger.log_event("reflect_complete", {
                "iteration": iteration,
                "decision": "continue",
                "reason": "more_failures_to_fix"
            })
            console.print(f"  [yellow]→ {remaining_failures} tests still failing, continuing...[/yellow]")
    
    # Log completion
    console.print("\n[bold]Phase 3: Completion[/bold]")
    logger.log_event("completion", {
        "status": "success",
        "iterations": iteration,
        "total_patches": iteration
    })
    
    # End telemetry run
    logger.end_run(success=True, summary={
        "run_id": run_id,
        "repo": str(repo_path),
        "status": "success",
        "iterations": iteration,
        "patches_applied": iteration,
        "duration_seconds": 10.5
    })
    
    console.print(f"\n[green]✨ Telemetry demo completed successfully![/green]")
    console.print(f"[dim]Telemetry saved to: {logger.run_dir}[/dim]\n")
    
    # Show how to view the telemetry
    console.print("[bold]To view the telemetry, run:[/bold]")
    console.print(f"  python -m src.nova.telemetry.viewer view {logger.run_dir}/trace.jsonl --all")
    console.print("\n[bold]Or to see just the timeline:[/bold]")
    console.print(f"  python -m src.nova.telemetry.viewer view {logger.run_dir}/trace.jsonl --timeline")
    console.print("\n[bold]To list all telemetry runs:[/bold]")
    console.print("  python -m src.nova.telemetry.viewer list-runs")


if __name__ == "__main__":
    demo_telemetry()
