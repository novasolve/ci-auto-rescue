#!/usr/bin/env python3
"""Test PR generation functionality."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nova.tools.pr_generator import PRGenerator

def test_pr_generation():
    """Test the PR generation flow."""
    print("Testing PR Generation...")

    # Create PR generator
    pr_gen = PRGenerator(Path.cwd())

    # Test data
    fixed_tests = [
        {"name": "test_addition", "file": "tests/test_calculator.py"},
        {"name": "test_multiplication", "file": "tests/test_calculator.py"},
        {"name": "test_division_by_zero", "file": "tests/test_calculator.py"}
    ]

    patches_applied = ["Fixed calculator operations"]
    changed_files = ["src/calculator.py"]
    execution_time = "0m 17s"

    # Generate PR content
    print("\nGenerating PR content...")
    title, description = pr_gen.generate_pr_content(
        fixed_tests=fixed_tests,
        patches_applied=patches_applied,
        changed_files=changed_files,
        execution_time=execution_time
    )

    print(f"\nPR Title: {title}")
    print(f"\nPR Description:\n{description}")

    # Check create_pr functionality
    print("\nChecking PR creation requirements...")
    success, message = pr_gen.create_pr(
        branch_name="test-branch",
        title=title,
        description=description,
        draft=True  # Create as draft to avoid actual PR
    )

    if not success:
        print(f"Cannot create PR: {message}")
    else:
        print(f"PR could be created: {message}")

if __name__ == "__main__":
    test_pr_generation()
