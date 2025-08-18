#!/usr/bin/env python3
"""
Test script to verify deterministic multi-failure fix strategy.
Tests that Nova fixes all failing tests in demo_exceptions in one cycle.
"""

import sys
import os
import shutil
import subprocess
import json
from pathlib import Path
from datetime import datetime

def run_nova_on_demo(demo_path: Path, verbose: bool = True):
    """Run Nova on a demo project and analyze the results."""
    
    print(f"\n{'='*60}")
    print(f"Testing Nova on: {demo_path.name}")
    print(f"{'='*60}\n")
    
    # Change to demo directory
    original_dir = os.getcwd()
    os.chdir(demo_path)
    
    try:
        # Clean up any previous Nova runs
        nova_dir = demo_path / ".nova"
        if nova_dir.exists():
            shutil.rmtree(nova_dir)
        
        # Run initial tests to see failures
        print("1. Running initial tests to see failures...")
        result = subprocess.run(
            ["python", "-m", "pytest", "-v", "--tb=short"],
            capture_output=True,
            text=True
        )
        
        print(f"Initial test result: {len(result.stdout.splitlines())} lines of output")
        failing_count = result.stdout.count("FAILED")
        print(f"Found {failing_count} failing tests\n")
        
        # Run Nova with our enhanced settings
        print("2. Running Nova CI-Rescue...")
        nova_cmd = [
            sys.executable, "-m", "nova", "fix",
            "--verbose" if verbose else "",
            "--model", os.getenv("NOVA_MODEL", "gpt-4")
        ]
        nova_cmd = [c for c in nova_cmd if c]  # Remove empty strings
        
        start_time = datetime.now()
        result = subprocess.run(
            nova_cmd,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "NOVA_DETERMINISTIC_FIX": "true",
                "NOVA_AGENT_MAX_ITERATIONS": "20",
                "NOVA_ALLOW_TEST_READ": "true"
            }
        )
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"Nova completed in {duration:.1f} seconds")
        print(f"Exit code: {result.returncode}")
        
        # Analyze Nova output
        output_lines = result.stdout.splitlines()
        
        # Count how many times tests were run
        test_runs = result.stdout.count("Running tests...")
        print(f"\n3. Analysis:")
        print(f"   - Tests were run {test_runs} times")
        
        # Look for planning output
        if "DETERMINISTIC MULTI-FAILURE FIX STRATEGY" in result.stdout:
            print("   - ✅ Deterministic strategy was used")
        else:
            print("   - ❌ Old strategy might have been used")
        
        # Check if all tests pass now
        print("\n4. Running final tests to verify fixes...")
        final_result = subprocess.run(
            ["python", "-m", "pytest", "-v"],
            capture_output=True,
            text=True
        )
        
        final_failing = final_result.stdout.count("FAILED")
        final_passing = final_result.stdout.count("passed")
        
        print(f"   - Final result: {final_passing} passed, {final_failing} failed")
        
        # Check telemetry for iteration count
        telemetry_files = list((demo_path / ".nova" / "telemetry").rglob("*.jsonl"))
        if telemetry_files:
            latest_telemetry = max(telemetry_files, key=lambda p: p.stat().st_mtime)
            print(f"\n5. Checking telemetry: {latest_telemetry.name}")
            
            iterations = 0
            tool_calls = 0
            with open(latest_telemetry) as f:
                for line in f:
                    event = json.loads(line)
                    if event.get("event") == "iteration_start":
                        iterations += 1
                    if event.get("event") == "tool_call":
                        tool_calls += 1
            
            print(f"   - Iterations: {iterations}")
            print(f"   - Tool calls: {tool_calls}")
        
        # Summary
        print(f"\n{'='*60}")
        print("SUMMARY:")
        print(f"   - Initial failures: {failing_count}")
        print(f"   - Final failures: {final_failing}")
        print(f"   - Test runs: {test_runs}")
        print(f"   - Duration: {duration:.1f}s")
        
        if final_failing == 0 and test_runs <= 3:
            print("   - ✅ SUCCESS: All tests fixed efficiently!")
        elif final_failing == 0:
            print("   - ⚠️  PARTIAL: Tests fixed but took multiple cycles")
        else:
            print("   - ❌ FAILED: Some tests still failing")
        
        print(f"{'='*60}\n")
        
        return {
            "demo": demo_path.name,
            "initial_failures": failing_count,
            "final_failures": final_failing,
            "test_runs": test_runs,
            "duration": duration,
            "success": final_failing == 0
        }
        
    finally:
        os.chdir(original_dir)


def main():
    """Test the deterministic fix on demo_exceptions."""
    
    print("Testing Deterministic Multi-Failure Fix Strategy")
    print("=" * 60)
    
    # Test on demo_exceptions which has multiple failing functions
    demo_path = Path("examples/demos/demo_exceptions")
    
    if not demo_path.exists():
        print(f"Error: {demo_path} not found!")
        return 1
    
    # Run the test
    result = run_nova_on_demo(demo_path, verbose=True)
    
    # Print final verdict
    if result["success"] and result["test_runs"] <= 3:
        print("\n🎉 Deterministic fix strategy is working correctly!")
        return 0
    else:
        print("\n⚠️  Deterministic fix strategy needs improvement")
        return 1


if __name__ == "__main__":
    sys.exit(main())
