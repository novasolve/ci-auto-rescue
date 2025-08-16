#!/usr/bin/env python3
"""
Test script to demonstrate the updated nova_runner_wrapper.py
Can be used with either real Nova or mock implementation
"""

import subprocess
import json
import sys
from pathlib import Path

def test_nova_wrapper():
    """Test the nova_runner_wrapper with a sample repository"""
    
    # Path to test repository
    test_repo = "test_repos/simple_math"
    
    # Run the wrapper
    cmd = [sys.executable, "nova_runner_wrapper.py", test_repo, "--version", "both"]
    
    print("Running Nova regression test...")
    print(f"Command: {' '.join(cmd)}")
    print("="*60)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Print output
    print(result.stdout)
    
    if result.stderr:
        print("Errors:", result.stderr)
    
    # Try to parse JSON from output
    try:
        # Find JSON in output
        lines = result.stdout.split('\n')
        json_start = -1
        json_end = -1
        
        for i, line in enumerate(lines):
            if line.strip() == '{':
                json_start = i
            elif line.strip() == '}' and json_start >= 0:
                json_end = i
                break
        
        if json_start >= 0 and json_end >= 0:
            json_text = '\n'.join(lines[json_start:json_end+1])
            data = json.loads(json_text)
            
            print("\n" + "="*60)
            print("PARSED RESULTS:")
            print("="*60)
            
            if "results" in data:
                for version, results in data["results"].items():
                    print(f"\n{version}:")
                    print(f"  Success: {results.get('success', False)}")
                    print(f"  Iterations: {results.get('iterations', 0)}")
                    print(f"  Time: {results.get('time', 0):.2f}s")
                    print(f"  Tests Fixed: {results.get('tests_fixed', 0)}")
            
            print(f"\nWinner: {data.get('winner', 'Unknown')}")
            
            if data.get('regression'):
                print("\n⚠️  REGRESSION DETECTED!")
                
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Could not parse JSON results: {e}")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(test_nova_wrapper())
