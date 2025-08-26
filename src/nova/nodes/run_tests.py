"""
Run Tests node for Nova CI-Rescue agent workflow.
"""

from typing import Tuple, List, Optional, Any
from rich.console import Console

from nova.agent.state import AgentState
from nova.runner.test_runner import TestRunner, FailingTest
from nova.telemetry.logger import JSONLLogger

console = Console()


class RunTestsNode:
    """Node responsible for running tests and capturing results."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def execute(
        self,
        state: AgentState,
        runner: TestRunner,
        telemetry: Optional[JSONLLogger] = None,
        step_number: Optional[int] = None
    ) -> Tuple[List[FailingTest], Optional[str]]:
        """
        Run tests after applying a patch.
        
        Args:
            state: Current agent state
            runner: TestRunner instance
            telemetry: Optional telemetry logger
            step_number: Optional step number for test report
            
        Returns:
            Tuple of (failing tests list, junit xml report)
        """
        iteration = state.current_iteration
        
        # Log test run start
        if telemetry:
            telemetry.log_event("run_tests_start", {
                "iteration": iteration,
                "step": step_number,
                "previous_failures": state.total_failures
            })
        
        if self.verbose:
            console.print(f"[cyan]🧪 Running tests after patch...[/cyan]")
        
        # Run tests
        new_failures, junit_xml = runner.run_tests()
        
        # Save test report artifact
        if telemetry and junit_xml and step_number is not None:
            telemetry.save_test_report(step_number, junit_xml, report_type="junit")
        
        # Update state with new test results
        previous_failures = state.total_failures
        state.add_failing_tests(new_failures)
        state.test_results.append({
            "iteration": iteration,
            "step": step_number,
            "failures_before": previous_failures,
            "failures_after": state.total_failures
        })
        
        # Calculate progress
        fixed_count = previous_failures - state.total_failures
        
        # Display results
        if state.total_failures == 0:
            console.print(f"[bold green]✅ All tests passing![/bold green]")
        elif fixed_count > 0:
            console.print(f"[green]✓ Progress: Fixed {fixed_count} test(s), {state.total_failures} remaining[/green]")
        else:
            console.print(f"[yellow]⚠ No progress: {state.total_failures} test(s) still failing[/yellow]")
        
        # Log test results
        if telemetry:
            telemetry.log_event("run_tests_complete", {
                "iteration": iteration,
                "step": step_number,
                "failures_before": previous_failures,
                "failures_after": state.total_failures,
                "fixed": fixed_count,
                "report_saved": junit_xml is not None
            })
        
        return new_failures, junit_xml


def run_tests_node(
    state: AgentState,
    runner: TestRunner,
    telemetry: Optional[JSONLLogger] = None,
    step_number: Optional[int] = None,
    verbose: bool = False
) -> Tuple[List[FailingTest], Optional[str]]:
    """
    Convenience function to execute the run tests node.
    
    Args:
        state: Current agent state
        runner: TestRunner instance
        telemetry: Optional telemetry logger
        step_number: Optional step number
        verbose: Enable verbose output
        
    Returns:
        Tuple of (failing tests, junit xml)
    """
    node = RunTestsNode(verbose=verbose)
    return node.execute(state, runner, telemetry, step_number)
