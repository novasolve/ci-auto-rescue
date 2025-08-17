#!/usr/bin/env python3
"""
Test script to demonstrate OS-1182 transparent error reporting functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from nova.github_integration import RunMetrics, OutcomeReporter


def test_max_iterations_exceeded():
    """Test error reporting for max iterations exceeded."""
    print("=== Testing MaxIterationsExceeded ===\n")
    
    metrics = RunMetrics(
        runtime_seconds=120,
        iterations=6,
        files_changed=3,
        status="failure",
        tests_fixed=8,
        tests_remaining=2,
        initial_failures=10,
        final_failures=2,
        branch_name="fix/test-failures",
        # Enhanced fields
        success=False,
        failure_type="MaxIterationsExceeded",
        failure_reason="Reached maximum 6 iterations with 2 tests still failing."
    )
    
    reporter = OutcomeReporter(metrics)
    
    print("CLI Summary:")
    print("-" * 50)
    print(reporter.generate_cli_summary())
    print("\n")
    
    print("PR Comment (excerpt):")
    print("-" * 50)
    pr_comment = reporter.generate_pr_comment()
    # Show just the first part
    print(pr_comment.split("---")[0])
    print("\n")
    
    print("API Response:")
    print("-" * 50)
    import json
    print(json.dumps(reporter.generate_api_response(), indent=2))
    print("\n")


def test_safety_guard_triggered():
    """Test error reporting for safety guard violations."""
    print("=== Testing SafetyGuardTriggered ===\n")
    
    metrics = RunMetrics(
        runtime_seconds=45,
        iterations=2,
        files_changed=0,
        status="failure",
        tests_fixed=0,
        tests_remaining=5,
        initial_failures=5,
        final_failures=5,
        branch_name="fix/test-failures",
        # Enhanced fields
        success=False,
        failure_type="SafetyGuardTriggered",
        failure_reason="All proposed patches were rejected by safety checks (attempted to modify test files)."
    )
    
    reporter = OutcomeReporter(metrics)
    
    print("CLI Summary:")
    print("-" * 50)
    print(reporter.generate_cli_summary())
    print("\n")


def test_success():
    """Test reporting for successful run."""
    print("=== Testing Success Case ===\n")
    
    metrics = RunMetrics(
        runtime_seconds=90,
        iterations=3,
        files_changed=2,
        status="success",
        tests_fixed=5,
        tests_remaining=0,
        initial_failures=5,
        final_failures=0,
        branch_name="fix/test-failures",
        # Enhanced fields
        success=True,
        failure_type=None,
        failure_reason=None
    )
    
    reporter = OutcomeReporter(metrics)
    
    print("CLI Summary:")
    print("-" * 50)
    print(reporter.generate_cli_summary())
    print("\n")


def test_test_execution_error():
    """Test error reporting for test execution errors."""
    print("=== Testing TestExecutionError ===\n")
    
    metrics = RunMetrics(
        runtime_seconds=30,
        iterations=1,
        files_changed=1,
        status="timeout",
        tests_fixed=0,
        tests_remaining=3,
        initial_failures=3,
        final_failures=3,
        branch_name="fix/test-failures",
        # Enhanced fields
        success=False,
        failure_type="TestExecutionError",
        failure_reason="Test runner timed out after 30s (Docker container unresponsive)."
    )
    
    reporter = OutcomeReporter(metrics)
    
    print("CLI Summary:")
    print("-" * 50)
    print(reporter.generate_cli_summary())
    print("\n")


if __name__ == "__main__":
    print("OS-1182 Transparent Error Reporting Test\n")
    print("This demonstrates the unified error reporting across different failure scenarios.\n")
    
    test_success()
    test_max_iterations_exceeded()
    test_safety_guard_triggered()
    test_test_execution_error()
    
    print("✅ All test scenarios completed!")
    print("\nKey Benefits Demonstrated:")
    print("- Clear failure reasons in all outputs")
    print("- Actionable next steps based on failure type")
    print("- Consistent messaging across CLI, PR comments, and API")
    print("- Trust-building transparency about what Nova attempted")
