#!/usr/bin/env python3
"""Debug script to understand test detection issue."""

import sys
import os
import json
import tempfile
import subprocess
from pathlib import Path

# Add parent dir to path to import Nova modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.nova.runner.test_runner import TestRunner

def main():
    """Debug test detection."""
    # Change to demo_broken_project directory
    demo_dir = Path(__file__).parent / "examples/demos/demo_broken_project"
    
    print(f"Working directory: {demo_dir}")
    print(f"Exists: {demo_dir.exists()}")
    
    # Create test runner
    runner = TestRunner(demo_dir, verbose=True)
    
    # Run tests and see what happens
    print("\n=== Running test detection ===")
    failing_tests, junit_xml = runner.run_tests()
    
    print(f"\nNumber of failing tests detected: {len(failing_tests)}")
    
    for i, test in enumerate(failing_tests):
        print(f"\nTest {i+1}:")
        print(f"  Name: {test.name}")
        print(f"  File: {test.file}")
        print(f"  Line: {test.line}")
        print(f"  Error: {test.short_traceback[:100]}...")
    
    # Also run pytest directly to compare
    print("\n\n=== Running pytest directly ===")
    result = subprocess.run(
        ["python", "-m", "pytest", "-v", "--tb=short"],
        cwd=demo_dir,
        capture_output=True,
        text=True
    )
    
    print(f"Return code: {result.returncode}")
    print(f"Number of test results in output: {result.stdout.count('FAILED')}")
    
    # Count actual failures in output
    lines = result.stdout.split('\n')
    failed_tests = [line for line in lines if 'FAILED' in line]
    print(f"\nFailed test lines:")
    for line in failed_tests[:5]:  # Show first 5
        print(f"  {line}")
    
    if len(failed_tests) > 5:
        print(f"  ... and {len(failed_tests) - 5} more")

if __name__ == "__main__":
    main()
