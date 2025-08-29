#!/usr/bin/env python3
"""
Demo script showing the enhanced telemetry with your improved planner node.
"""

import json
import tempfile
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

# Import Nova components
from src.nova.config import NovaSettings
from src.nova.telemetry.logger import JSONLLogger
from src.nova.agent.state import AgentState
from src.nova.nodes.planner import PlannerNode

console = Console()


class MockLLMAgent:
    """Mock LLM agent for demonstration."""

    def create_plan(self, failing_tests, iteration, critic_feedback=None):
        """Generate a mock plan."""
        if critic_feedback:
            # Adjust plan based on critic feedback
            return {
                "approach": "Revised approach based on critic feedback",
                "steps": [
                    "Re-analyze the issue from feedback",
                    "Generate more conservative fix",
                    "Add additional validation",
                    "Test thoroughly",
                ],
                "target_tests": failing_tests[:1],  # Focus on one test
                "strategy": "Conservative incremental fix",
            }
        else:
            return {
                "approach": "Fix failing assertions and import errors",
                "steps": [
                    "Fix missing imports in module.py",
                    "Correct assertion logic in calculate function",
                    "Update expected values in tests",
                ],
                "target_tests": failing_tests[:2],
                "strategy": "Direct fixes to source code",
            }


def demo_enhanced_telemetry():
    """Demonstrate the enhanced telemetry system with detailed logging."""

    console.print(
        Panel.fit(
            "[bold cyan]Nova CI-Rescue Enhanced Telemetry Demo[/bold cyan]\n"
            "Showing improved planner node with detailed event logging",
            border_style="cyan",
        )
    )

    # Create temporary telemetry directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup
        settings = NovaSettings()
        settings.telemetry_dir = temp_dir
        logger = JSONLLogger(settings, enabled=True)

        # Start run
        run_id = logger.start_run(repo_path="/demo/repo")
        console.print(f"\n📁 Telemetry run: [green]{run_id}[/green]")
        console.print(f"📂 Output directory: {logger.run_dir}\n")

        # Create test state with realistic failing tests
        state = AgentState(repo_path=Path("/demo/repo"))
        state.current_iteration = 1
        state.failing_tests = [
            {
                "name": "test_calculate_sum",
                "file": "tests/test_calculator.py",
                "line": 42,
                "short_traceback": "AssertionError: assert 15 == 10\n  where 15 = calculate_sum([1, 2, 3, 4, 5])\n  and   10 = expected",
            },
            {
                "name": "test_import_module",
                "file": "tests/test_imports.py",
                "line": 5,
                "short_traceback": "ImportError: cannot import name 'helper' from 'utils'\n  (module 'utils' has no attribute 'helper')",
            },
            {
                "name": "test_edge_cases",
                "file": "tests/test_edge.py",
                "line": 78,
                "short_traceback": "ValueError: invalid literal for int() with base 10: 'abc'\n  in process_input('abc')",
            },
        ]

        # Create mock LLM agent
        llm_agent = MockLLMAgent()

        console.print("[bold]═══ Iteration 1: Initial Planning ═══[/bold]\n")

        # Execute planner node (first attempt)
        planner = PlannerNode(verbose=True)
        plan1 = planner.execute(state, llm_agent, logger, critic_feedback=None)

        console.print("\n[dim]Plan generated:[/dim]")
        console.print(
            Panel(
                json.dumps(plan1, indent=2, default=str),
                title="Initial Plan",
                border_style="blue",
            )
        )

        # Simulate critic feedback
        critic_feedback = (
            "The proposed fix is too aggressive and might break other tests. "
            "Focus on fixing one test at a time and ensure backward compatibility. "
            "The import error should be addressed first as it blocks other tests."
        )

        console.print(
            "\n[bold]═══ Iteration 2: Planning with Critic Feedback ═══[/bold]\n"
        )

        # Update state for next iteration
        state.current_iteration = 2
        state.patches_applied = [
            "--- a/utils.py\n+++ b/utils.py\n@@ -1,0 +1,1 @@\n+def helper(): pass"
        ]

        # Execute planner with critic feedback
        plan2 = planner.execute(
            state, llm_agent, logger, critic_feedback=critic_feedback
        )

        console.print("\n[dim]Revised plan generated:[/dim]")
        console.print(
            Panel(
                json.dumps(plan2, indent=2, default=str),
                title="Revised Plan",
                border_style="green",
            )
        )

        # End the run
        logger.end_run(
            success=False, summary={"demo": True, "iterations": 2, "plans_generated": 2}
        )

        # Display the trace.jsonl contents
        console.print("\n[bold]═══ Telemetry Trace Log ═══[/bold]\n")

        trace_file = logger.run_dir / "trace.jsonl"
        events = []
        with open(trace_file, "r") as f:
            for line in f:
                events.append(json.loads(line))

        # Show key events with enhanced details
        for event in events:
            event_type = event.get("event")

            if event_type == "planner_start":
                data = event.get("data", {})
                console.print(
                    f"[cyan]📋 PLANNER START[/cyan] (Iteration {data.get('iteration')})"
                )
                console.print(f"  • Failing tests: {data.get('failing_tests_count')}")
                console.print(
                    f"  • Has critic feedback: {data.get('has_critic_feedback')}"
                )
                if data.get("critic_feedback"):
                    console.print(
                        f"  • Feedback: [yellow]{data['critic_feedback'][:100]}...[/yellow]"
                    )
                console.print(
                    f"  • Patches applied: {data.get('patches_applied_count')}"
                )

                # Show failing test details
                for i, test in enumerate(data.get("failing_tests", [])[:2], 1):
                    console.print(f"\n  Test {i}: [red]{test['name']}[/red]")
                    console.print(f"    File: {test['file']}:{test['line']}")
                    console.print(
                        f"    Error: [dim]{test['error_preview'][:80]}...[/dim]"
                    )
                console.print()

            elif event_type == "planner_complete":
                data = event.get("data", {})
                plan_info = data.get("plan", {})
                console.print(
                    f"[green]✅ PLANNER COMPLETE[/green] (Iteration {data.get('iteration')})"
                )
                console.print(f"  • Approach: {plan_info.get('approach')}")
                console.print(f"  • Strategy: {plan_info.get('strategy')}")
                console.print(
                    f"  • Target tests: {plan_info.get('target_tests_count')}"
                )
                console.print(f"  • Steps: {len(plan_info.get('steps', []))}")
                for i, step in enumerate(plan_info.get("steps", [])[:3], 1):
                    console.print(f"    {i}. {step}")
                console.print()

        # Summary statistics
        console.print("\n[bold]═══ Telemetry Summary ═══[/bold]\n")
        console.print(f"📊 Total events logged: {len(events)}")

        event_counts = {}
        for event in events:
            event_type = event.get("event")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        console.print("\nEvent type breakdown:")
        for event_type, count in sorted(event_counts.items()):
            console.print(f"  • {event_type}: {count}")

        # Show example of enhanced planner_start event
        console.print("\n[bold]═══ Example Enhanced Event (planner_start) ═══[/bold]\n")

        planner_events = [e for e in events if e.get("event") == "planner_start"]
        if planner_events and len(planner_events) > 1:
            # Show the second planner_start (with critic feedback)
            example_event = planner_events[1]

            # Pretty print the JSON
            json_str = json.dumps(example_event, indent=2, default=str)
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
            console.print(syntax)

        console.print("\n✅ [green]Enhanced telemetry demo complete![/green]")
        console.print(f"📁 Full trace saved to: {trace_file}")


if __name__ == "__main__":
    demo_enhanced_telemetry()
