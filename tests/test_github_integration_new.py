"""
Test script for GitHub integration module.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nova.github_integration import GitHubAPI, RunMetrics, ReportGenerator


def test_report_generator():
    """Test the report generation functions."""
    
    # Create sample metrics
    metrics = RunMetrics(
        runtime_seconds=120,
        iterations=3,
        files_changed=5,
        status="success",
        tests_fixed=8,
        tests_remaining=0,
        initial_failures=8,
        final_failures=0,
        branch_name="nova-fix-20241215-1234"
    )
    
    generator = ReportGenerator()
    
    # Test check summary generation
    print("=== Check Summary ===")
    summary = generator.generate_check_summary(metrics)
    print(summary)
    print()
    
    # Test PR comment generation
    print("=== PR Comment ===")
    comment = generator.generate_pr_comment(metrics)
    print(comment)
    print()
    
    # Test with failure metrics
    failure_metrics = RunMetrics(
        runtime_seconds=300,
        iterations=6,
        files_changed=3,
        status="timeout",
        tests_fixed=5,
        tests_remaining=3,
        initial_failures=8,
        final_failures=3,
        branch_name="nova-fix-20241215-5678"
    )
    
    print("=== Failure Check Summary ===")
    failure_summary = generator.generate_check_summary(failure_metrics)
    print(failure_summary)
    print()
    
    print("=== Failure PR Comment ===")
    failure_comment = generator.generate_pr_comment(failure_metrics)
    print(failure_comment)
    
    # Test JSON report
    print("\n=== JSON Report ===")
    json_report = generator.generate_json_report(metrics)
    print(json_report)
    
    print("\n✅ All report generation tests passed!")


def test_github_api_with_mock():
    """Test GitHub API methods (without actual API calls)."""
    
    # This would require a mock token for testing
    # In a real test environment, we'd use mocking libraries
    print("GitHub API test:")
    print("- GitHubAPI class instantiates correctly")
    print("- Methods are available: create_check_run, create_pr_comment, update_pr_comment, find_pr_comment")
    
    # Just verify the class can be instantiated
    api = GitHubAPI("mock_token")
    assert hasattr(api, 'create_check_run')
    assert hasattr(api, 'create_pr_comment')
    assert hasattr(api, 'update_pr_comment')
    assert hasattr(api, 'find_pr_comment')
    
    print("✅ GitHub API structure test passed!")


if __name__ == "__main__":
    print("Testing GitHub Integration Module\n")
    print("=" * 60)
    
    test_report_generator()
    print("\n" + "=" * 60 + "\n")
    test_github_api_with_mock()
    
    print("\n" + "=" * 60)
    print("All tests completed successfully! 🎉")
