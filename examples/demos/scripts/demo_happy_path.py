#!/usr/bin/env python3
"""
Demo script to test the complete Nova CI-Rescue Happy Path implementation.
This demonstrates the full Planner → Actor → Critic → Apply → RunTests → Reflect loop.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nova.agent.llm_agent_enhanced import EnhancedLLMAgent
from nova.agent.state import AgentState
from nova.config import get_settings
from nova.telemetry.logger import JSONLLogger
from nova.tools.git import GitBranchManager
from nova.runner import TestRunner
from nova.nodes.apply_patch import apply_patch
from rich.console import Console

console = Console()


def main():
    """Run a complete happy path demo of Nova CI-Rescue."""

    console.print("[bold cyan]Nova CI-Rescue Happy Path Demo[/bold cyan]")
    console.print("=" * 60)

    # Configuration
    repo_path = Path("./nova_demo_workspace")
    max_iterations = 3
    timeout_seconds = 300
    verbose = True

    # Initialize settings
    settings = get_settings()
    console.print(f"[dim]Model: {settings.default_llm_model}[/dim]")

    # Initialize components
    try:
        # Initialize enhanced LLM agent
        console.print("\n[yellow]Initializing LLM Agent...[/yellow]")
        llm_agent = EnhancedLLMAgent(repo_path)
        console.print("[green]✓ LLM Agent initialized[/green]")

        # Initialize Git manager
        console.print("[yellow]Setting up Git branch...[/yellow]")
        git_manager = GitBranchManager(repo_path, verbose=verbose)
        branch_name = git_manager.create_fix_branch()
        console.print(f"[green]✓ Created branch: {branch_name}[/green]")

        # Initialize telemetry
        telemetry = JSONLLogger(settings, enabled=True)
        telemetry.start_run(repo_path)

        # Initialize agent state
        state = AgentState(
            repo_path=repo_path,
            max_iterations=max_iterations,
            timeout_seconds=timeout_seconds,
            branch_name=branch_name,
        )

        # Run initial tests
        console.print("\n[yellow]Running initial tests...[/yellow]")
        runner = TestRunner(repo_path, verbose=verbose)
        failing_tests = runner.run_tests(max_failures=5)

        if not failing_tests:
            console.print("[green]✅ No failing tests found![/green]")
            return

        state.add_failing_tests(failing_tests)
        console.print(f"[red]Found {len(failing_tests)} failing test(s)[/red]")

        # Agent loop
        console.print("\n[bold]Starting Agent Loop[/bold]")
        console.print("-" * 40)

        success = False
        while state.increment_iteration():
            iteration = state.current_iteration
            console.print(f"\n[bold blue]Iteration {iteration}[/bold blue]")

            # 1. PLANNER
            console.print(
                "\n[cyan]1. PLANNER - Analyzing failures and creating plan...[/cyan]"
            )
            plan = llm_agent.create_plan(state.failing_tests, iteration)
            state.plan = plan

            console.print(f"   Plan: {plan.get('approach', 'Unknown')}")
            if plan.get("steps"):
                for i, step in enumerate(plan["steps"][:3], 1):
                    console.print(f"   Step {i}: {step}")

            telemetry.log_event(
                "planner_complete", {"iteration": iteration, "plan": plan}
            )

            # 2. ACTOR
            console.print("\n[cyan]2. ACTOR - Generating patch...[/cyan]")
            patch_diff = llm_agent.generate_patch(
                state.failing_tests, iteration, plan=plan
            )

            if not patch_diff:
                console.print("[red]   ✗ Failed to generate patch[/red]")
                state.final_status = "no_patch"
                break

            patch_lines = patch_diff.split("\n")
            console.print(f"   ✓ Generated {len(patch_lines)} line patch")

            telemetry.log_event(
                "actor_complete",
                {"iteration": iteration, "patch_size": len(patch_lines)},
            )

            # 3. CRITIC
            console.print("\n[cyan]3. CRITIC - Reviewing patch...[/cyan]")
            approved, reason = llm_agent.review_patch(patch_diff, state.failing_tests)

            console.print(f"   Review: {reason}")

            if not approved:
                console.print("[red]   ✗ Patch rejected[/red]")
                state.final_status = "patch_rejected"
                telemetry.log_event(
                    "critic_rejected", {"iteration": iteration, "reason": reason}
                )
                break

            console.print("[green]   ✓ Patch approved[/green]")
            telemetry.log_event("critic_approved", {"iteration": iteration})

            # 4. APPLY
            console.print("\n[cyan]4. APPLY - Applying patch...[/cyan]")
            result = apply_patch(state, patch_diff, git_manager, verbose=False)

            if not result["success"]:
                console.print("[red]   ✗ Failed to apply patch[/red]")
                state.final_status = "patch_error"
                break

            console.print(f"   ✓ Applied patch (step {result['step_number']})")
            console.print(f"   Changed files: {', '.join(result['changed_files'])}")

            telemetry.log_event(
                "patch_applied",
                {
                    "iteration": iteration,
                    "step": result["step_number"],
                    "files": result["changed_files"],
                },
            )

            # 5. RUN TESTS
            console.print("\n[cyan]5. RUN TESTS - Testing changes...[/cyan]")
            previous_failures = state.total_failures
            new_failures = runner.run_tests(max_failures=5)
            state.add_failing_tests(new_failures)

            fixed_count = previous_failures - state.total_failures
            console.print(f"   Previous failures: {previous_failures}")
            console.print(f"   Current failures: {state.total_failures}")
            if fixed_count > 0:
                console.print(f"   [green]✓ Fixed {fixed_count} test(s)[/green]")

            telemetry.log_event(
                "test_results",
                {
                    "iteration": iteration,
                    "fixed": fixed_count,
                    "remaining": state.total_failures,
                },
            )

            # 6. REFLECT
            console.print("\n[cyan]6. REFLECT - Evaluating progress...[/cyan]")

            if state.total_failures == 0:
                console.print(
                    "[bold green]   ✅ All tests passing! Success![/bold green]"
                )
                state.final_status = "success"
                success = True
                break

            if state.check_timeout():
                console.print("[red]   ⏰ Timeout reached[/red]")
                state.final_status = "timeout"
                break

            if iteration >= state.max_iterations:
                console.print("[red]   🔄 Max iterations reached[/red]")
                state.final_status = "max_iters"
                break

            console.print(
                f"   Continuing with {state.total_failures} failures remaining..."
            )

        # Summary
        console.print("\n" + "=" * 60)
        console.print("[bold]EXECUTION SUMMARY[/bold]")
        console.print(f"Final Status: {state.final_status}")
        console.print(f"Iterations: {state.current_iteration}/{state.max_iterations}")
        console.print(f"Patches Applied: {len(state.patches_applied)}")
        console.print(f"Final Failures: {state.total_failures}")

        if success:
            console.print(
                "\n[bold green]✅ HAPPY PATH COMPLETE - All tests fixed![/bold green]"
            )
        else:
            console.print(f"\n[yellow]⚠️ Process ended: {state.final_status}[/yellow]")

        # Cleanup
        telemetry.log_event(
            "completion", {"status": state.final_status, "success": success}
        )
        telemetry.end_run(success=success)

        if git_manager:
            git_manager.cleanup(success=success)

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback

        if verbose:
            traceback.print_exc()
        return 1

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
