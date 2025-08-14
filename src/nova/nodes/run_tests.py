"""
RunTests node for Nova CI-Rescue agent workflow.
Executes tests and captures results with detailed telemetry.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime
from rich.console import Console

from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger
from nova.runner.test_runner import TestRunner, FailingTest

console = Console()


class RunTestsNode:
    """Node responsible for running tests and capturing results."""
    
    def __init__(self, repo_path: Path, verbose: bool = False):
        self.repo_path = repo_path
        self.verbose = verbose
        self.runner = TestRunner(repo_path, verbose=verbose)
        
    def execute(
        self,
        state: AgentState,
        logger: JSONLLogger,
        step_number: Optional[int] = None,
        max_failures: int = 5
    ) -> Dict[str, Any]:
        """
        Run tests and capture results with telemetry.
        
        Args:
            state: Current agent state
            logger: Telemetry logger
            step_number: Optional step number for artifact naming
            max_failures: Maximum number of failures to capture
            
        Returns:
            Dictionary with test results and metrics
        """
        iteration = state.current_iteration
        step_number = step_number or state.current_step
        
        # Log test run start
        logger.log_event("run_tests_start", {
            "iteration": iteration,
            "step_number": step_number,
            "previous_failures": len(state.failing_tests),
            "max_failures": max_failures,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        if self.verbose:
            console.print(f"[cyan]🧪 Running tests (step {step_number})...[/cyan]")
        
        start_time = datetime.utcnow()
        
        try:
            # Run the tests
            failing_tests, junit_xml = self.runner.run_tests(max_failures=max_failures)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Save test report artifact if available
            report_saved = False
            if junit_xml:
                report_path = logger.save_test_report(step_number, junit_xml, report_type="junit")
                report_saved = report_path is not None
            
            # Calculate test metrics
            previous_failures = state.failing_tests
            tests_fixed = []
            tests_still_failing = []
            new_failures = []
            
            # Compare with previous failures
            previous_test_names = {test.get("name") for test in previous_failures}
            current_test_names = {test.name for test in failing_tests}
            
            # Categorize test results
            for prev_test in previous_failures:
                if prev_test.get("name") not in current_test_names:
                    tests_fixed.append(prev_test.get("name"))
                else:
                    tests_still_failing.append(prev_test.get("name"))
            
            for test in failing_tests:
                if test.name not in previous_test_names:
                    new_failures.append(test.name)
            
            # Update state with new failures
            state.add_failing_tests(failing_tests)
            
            # Build result dictionary
            result = {
                "success": len(failing_tests) == 0,
                "step_number": step_number,
                "failing_tests": [test.to_dict() for test in failing_tests],
                "failure_count": len(failing_tests),
                "previous_failure_count": len(previous_failures),
                "tests_fixed": tests_fixed,
                "tests_still_failing": tests_still_failing,
                "new_failures": new_failures,
                "junit_report_saved": report_saved,
                "execution_time_seconds": execution_time
            }
            
            # Log test run completion with detailed metrics
            logger.log_event("run_tests_complete", {
                "iteration": iteration,
                "step_number": step_number,
                "metrics": {
                    "total_failures": len(failing_tests),
                    "previous_failures": len(previous_failures),
                    "tests_fixed_count": len(tests_fixed),
                    "tests_still_failing_count": len(tests_still_failing),
                    "new_failures_count": len(new_failures),
                    "execution_time_seconds": execution_time
                },
                "tests_fixed": tests_fixed[:10],  # Log first 10 fixed tests
                "tests_still_failing": tests_still_failing[:10],  # Log first 10 still failing
                "new_failures": new_failures[:10],  # Log first 10 new failures
                "junit_report_saved": report_saved,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Display results
            if self.verbose:
                if len(failing_tests) == 0:
                    console.print(f"[green]✅ All tests passing![/green]")
                else:
                    console.print(f"[yellow]Found {len(failing_tests)} failing test(s)[/yellow]")
                    
                    if tests_fixed:
                        console.print(f"[green]  ✓ Fixed {len(tests_fixed)} test(s):[/green]")
                        for test_name in tests_fixed[:3]:
                            console.print(f"    • {test_name}")
                        if len(tests_fixed) > 3:
                            console.print(f"    ... and {len(tests_fixed) - 3} more")
                    
                    if tests_still_failing:
                        console.print(f"[red]  ✗ Still failing: {len(tests_still_failing)} test(s)[/red]")
                        for test_name in tests_still_failing[:3]:
                            console.print(f"    • {test_name}")
                        if len(tests_still_failing) > 3:
                            console.print(f"    ... and {len(tests_still_failing) - 3} more")
                    
                    if new_failures:
                        console.print(f"[red]  ⚠ New failures: {len(new_failures)} test(s)[/red]")
                        for test_name in new_failures[:3]:
                            console.print(f"    • {test_name}")
                        if len(new_failures) > 3:
                            console.print(f"    ... and {len(new_failures) - 3} more")
            
            return result
            
        except Exception as e:
            # Log test run error
            logger.log_event("run_tests_error", {
                "iteration": iteration,
                "step_number": step_number,
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            if self.verbose:
                console.print(f"[red]❌ Test run failed: {e}[/red]")
            
            # Return error result
            return {
                "success": False,
                "step_number": step_number,
                "error": str(e),
                "failing_tests": state.failing_tests,  # Keep previous failures
                "failure_count": len(state.failing_tests)
            }


def run_tests(
    state: AgentState,
    logger: JSONLLogger,
    repo_path: Path,
    step_number: Optional[int] = None,
    max_failures: int = 5,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to run tests using the RunTestsNode.
    
    Args:
        state: Current agent state
        logger: Telemetry logger
        repo_path: Path to repository
        step_number: Optional step number for artifact naming
        max_failures: Maximum number of failures to capture
        verbose: Enable verbose output
        
    Returns:
        Dictionary with test results and metrics
    """
    node = RunTestsNode(repo_path, verbose=verbose)
    return node.execute(state, logger, step_number, max_failures)