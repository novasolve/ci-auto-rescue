#!/usr/bin/env python3
"""
Demo script to show Nova CI Rescue fixing the calculator bugs.
This demonstrates the current implementation's approach.
"""

import json
import sys
from pathlib import Path

# Add Nova to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nova.agent.deep_agent import NovaDeepAgent
from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger
from nova.runner.test_runner import TestRunner

def run_demo():
    """Run Nova CI Rescue on the demo calculator project."""
    
    print("=" * 60)
    print("Nova CI Rescue Demo - Fixing Calculator Bugs")
    print("=" * 60)
    
    # Setup paths
    repo_path = Path(__file__).parent
    telemetry_path = repo_path / "telemetry"
    telemetry_path.mkdir(exist_ok=True)
    
    # Initialize components
    print("\n1. Initializing Nova components...")
    state = AgentState(repo_path=repo_path)
    telemetry = JSONLLogger(telemetry_path / "demo_run.jsonl")
    
    # Run initial test discovery
    print("\n2. Running initial test suite to find failures...")
    runner = TestRunner(repo_path)
    result = runner.run_tests(
        test_file="tests/test_calculator.py",
        verbose=True
    )
    
    if result["exit_code"] == 0:
        print("✅ All tests already passing! Nothing to fix.")
        return
    
    # Parse test failures
    failures = result.get("failures", [])
    print(f"\n❌ Found {len(failures)} failing test(s):")
    for i, failure in enumerate(failures, 1):
        print(f"   {i}. {failure.get('test_name', 'Unknown')}")
        if 'error_message' in failure:
            error_lines = failure['error_message'].split('\n')
            if error_lines:
                print(f"      Error: {error_lines[0][:60]}...")
    
    # Prepare failure information for the agent
    failures_summary = f"Total failing tests: {len(failures)}\n"
    for failure in failures[:3]:  # Show first 3 failures
        test_name = failure.get('test_name', 'unknown')
        error_msg = failure.get('error_message', 'No error message')
        failures_summary += f"- {test_name}: {error_msg[:100]}\n"
    
    error_details = ""
    for failure in failures[:2]:  # Detailed info for first 2
        error_details += f"\nTest: {failure.get('test_name')}\n"
        error_details += f"File: {failure.get('file')}\n"
        error_details += f"Error:\n{failure.get('error_message', '')[:200]}\n"
    
    # Read the buggy code for context
    calc_path = repo_path / "src" / "calculator.py"
    with open(calc_path, 'r') as f:
        calc_content = f.read()
    
    code_snippets = f"Current calculator.py:\n```python\n{calc_content}\n```"
    
    # Initialize and run the Deep Agent
    print("\n3. Initializing Nova Deep Agent...")
    agent = NovaDeepAgent(
        state=state,
        telemetry=telemetry,
        verbose=True
    )
    
    print("\n4. Running Deep Agent to fix the failures...")
    print("-" * 40)
    
    success = agent.run(
        failures_summary=failures_summary,
        error_details=error_details,
        code_snippets=code_snippets
    )
    
    print("-" * 40)
    
    # Report results
    print("\n5. Final Results:")
    if success:
        print("✅ SUCCESS: All tests are now passing!")
        
        # Show the fixed code
        print("\n6. Fixed calculator.py:")
        with open(calc_path, 'r') as f:
            fixed_content = f.read()
        print(fixed_content)
        
    else:
        print(f"❌ INCOMPLETE: Agent finished with status: {state.final_status}")
        print(f"   Iterations used: {state.current_iteration}")
        print(f"   Remaining failures: {state.total_failures}")
    
    # Show telemetry summary
    print("\n7. Telemetry Summary:")
    telemetry_file = telemetry_path / "demo_run.jsonl"
    if telemetry_file.exists():
        with open(telemetry_file, 'r') as f:
            events = [json.loads(line) for line in f if line.strip()]
        print(f"   Total events logged: {len(events)}")
        event_types = {}
        for event in events:
            event_type = event.get('event_type', 'unknown')
            event_types[event_type] = event_types.get(event_type, 0) + 1
        for event_type, count in sorted(event_types.items()):
            print(f"   - {event_type}: {count}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)

if __name__ == "__main__":
    run_demo()
