#!/usr/bin/env python3
"""
Nova Runner Wrapper - Runs real Nova CLI for regression testing
Provides unified interface for v1.0 and v1.1 using actual Nova commands
"""

import argparse
import subprocess
import time
import re
import json
from pathlib import Path

def run_nova_fix(wrapper_script: Path, repo_path: str, verbose: bool = False) -> dict:
    """
    Run 'nova fix' using the specified Nova wrapper script (v1_0 or v1_1) on the given repository.
    Returns a dictionary with success status, iterations count, and elapsed time.
    """
    # Build the command to run Nova
    command = [str(wrapper_script), "fix", repo_path]
    if verbose:
        command.append("--verbose")
    
    # Run the Nova process (capture output; stream if verbose)
    start_time = time.time()
    if verbose:
        # Stream output to console while capturing it
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        output_lines = []
        for line in process.stdout:  # Stream stdout line by line
            print(line, end="")      # Print Nova output in real-time for debugging
            output_lines.append(line)
        process.wait()
        full_output = "".join(output_lines)
        exit_code = process.returncode
    else:
        # Run quietly and capture all output
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        full_output = result.stdout
        exit_code = result.returncode
    elapsed = time.time() - start_time

    # Determine success from Nova's exit code (0 = success, 1 = failure)
    success = (exit_code == 0)
    
    # Parse the number of iterations completed from Nova's output
    iterations = 0
    
    # Try multiple patterns to extract iteration count
    patterns = [
        r"Iterations completed:\s*(\d+)/",
        r"Iteration\s+(\d+)/",
        r"iteration\s+(\d+)",
        r"Step\s+(\d+)/",
        r"Round\s+(\d+)/",
        r"Fixed after\s+(\d+)\s+iteration",
        r"All tests passed after\s+(\d+)\s+iteration"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, full_output, re.IGNORECASE)
        if matches:
            try:
                # Get the highest iteration number found
                iterations = max(int(m) for m in matches)
                break
            except ValueError:
                continue
    
    # Also check for max iterations reached
    max_iterations_reached = False
    if "max iterations reached" in full_output.lower():
        max_iterations_reached = True
        # Try to extract the max iteration count
        match = re.search(r"max.{0,20}iterations?.{0,20}(\d+)", full_output, re.IGNORECASE)
        if match:
            iterations = int(match.group(1))
    
    # Check for test fix statistics
    tests_fixed = 0
    match = re.search(r"(\d+)\s+tests?\s+fixed", full_output, re.IGNORECASE)
    if match:
        tests_fixed = int(match.group(1))
    
    # Check for timeout
    timeout_occurred = "timeout" in full_output.lower()
    
    return {
        "success": success,
        "iterations": iterations,
        "time": elapsed,
        "tests_fixed": tests_fixed,
        "max_iterations_reached": max_iterations_reached,
        "timeout_occurred": timeout_occurred,
        "exit_code": exit_code
    }

def main():
    parser = argparse.ArgumentParser(
        description="Run Nova CI-Rescue on a repository with both v1.0 and v1.1, and report results."
    )
    parser.add_argument("repo", metavar="repo", 
                        help="Path to the repository to run regression tests on.")
    parser.add_argument("--version", choices=["v1_0", "v1_1", "both"], default="both",
                        help="Which Nova version(s) to run: v1_0, v1_1, or both (default: both).")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose output (shows Nova logs in real-time).")
    parser.add_argument("--max-iters", type=int, default=6,
                        help="Maximum iterations for Nova (default: 6).")
    parser.add_argument("--timeout", type=int, default=1200,
                        help="Timeout in seconds (default: 1200).")
    args = parser.parse_args()

    repo_path = str(Path(args.repo).resolve())
    run_versions = args.version
    verbose = args.verbose

    # Determine the location of the Nova wrapper scripts (relative to this script)
    script_dir = Path(__file__).resolve().parent
    nova_v1_0 = script_dir / "nova_v1_0"
    nova_v1_1 = script_dir / "nova_v1_1"
    
    # Check if wrapper scripts exist
    if run_versions in ("v1_0", "both") and not nova_v1_0.exists():
        print(f"Error: Nova v1.0 wrapper not found at {nova_v1_0}")
        return 1
    if run_versions in ("v1_1", "both") and not nova_v1_1.exists():
        print(f"Error: Nova v1.1 wrapper not found at {nova_v1_1}")
        return 1

    results = {}
    
    # Run Nova v1.0 if requested (or if running both)
    if run_versions in ("v1_0", "both"):
        print(f"Running Nova v1.0 on {repo_path}...")
        results["v1_0"] = run_nova_fix(nova_v1_0, repo_path, verbose)
        if not verbose:
            print(f"  v1.0 Result: {'✅ Success' if results['v1_0']['success'] else '❌ Failed'}")
            print(f"  Iterations: {results['v1_0']['iterations']}")
            print(f"  Time: {results['v1_0']['time']:.2f}s")
    
    # Run Nova v1.1 if requested (or if running both)
    if run_versions in ("v1_1", "both"):
        print(f"\nRunning Nova v1.1 on {repo_path}...")
        results["v1_1"] = run_nova_fix(nova_v1_1, repo_path, verbose)
        if not verbose:
            print(f"  v1.1 Result: {'✅ Success' if results['v1_1']['success'] else '❌ Failed'}")
            print(f"  Iterations: {results['v1_1']['iterations']}")
            print(f"  Time: {results['v1_1']['time']:.2f}s")

    # Determine the "winner" based on success and efficiency
    winner = None
    regression = False
    
    if "v1_0" in results and "v1_1" in results:
        v1_0_res = results["v1_0"]
        v1_1_res = results["v1_1"]
        
        if v1_0_res["success"] and not v1_1_res["success"]:
            winner = "v1_0"
            regression = True  # v1.1 failed where v1.0 succeeded
        elif v1_1_res["success"] and not v1_0_res["success"]:
            winner = "v1_1"
        elif v1_0_res["success"] and v1_1_res["success"]:
            # Both succeeded – compare iterations (primary) and time (secondary)
            if v1_0_res["iterations"] < v1_1_res["iterations"]:
                winner = "v1_0_more_efficient"
            elif v1_1_res["iterations"] < v1_0_res["iterations"]:
                winner = "v1_1_more_efficient"
            else:
                # If iterations are equal, compare elapsed time
                if v1_0_res["time"] < v1_1_res["time"]:
                    winner = "v1_0_faster"
                elif v1_1_res["time"] < v1_0_res["time"]:
                    winner = "v1_1_faster"
                else:
                    winner = "tie"
        else:
            # Both failed or both did not succeed
            winner = "both_failed"
    elif "v1_0" in results:
        # Only v1_0 was run
        winner = "v1_0" if results["v1_0"]["success"] else "v1_0_failed"
    elif "v1_1" in results:
        # Only v1_1 was run
        winner = "v1_1" if results["v1_1"]["success"] else "v1_1_failed"

    # Prepare output data
    output = {
        "repository": repo_path,
        "results": results,
        "winner": winner,
        "regression": regression
    }
    
    # Print summary
    print("\n" + "="*60)
    print("REGRESSION TEST RESULTS")
    print("="*60)
    
    # Print the JSON results
    print("\nJSON Output:")
    print(json.dumps(output, indent=2))
    
    # Print human-readable summary
    if "v1_0" in results and "v1_1" in results:
        print("\n" + "="*60)
        print("COMPARISON SUMMARY")
        print("="*60)
        
        print(f"Winner: {winner}")
        if regression:
            print("⚠️ REGRESSION DETECTED: v1.1 failed where v1.0 succeeded!")
        
        # Success rate comparison
        v1_0_success = results["v1_0"]["success"]
        v1_1_success = results["v1_1"]["success"]
        print(f"\nSuccess:")
        print(f"  v1.0: {'✅' if v1_0_success else '❌'}")
        print(f"  v1.1: {'✅' if v1_1_success else '❌'}")
        
        # Efficiency comparison
        if v1_0_success and v1_1_success:
            print(f"\nEfficiency:")
            print(f"  v1.0: {results['v1_0']['iterations']} iterations, {results['v1_0']['time']:.2f}s")
            print(f"  v1.1: {results['v1_1']['iterations']} iterations, {results['v1_1']['time']:.2f}s")
            
            iter_diff = results['v1_1']['iterations'] - results['v1_0']['iterations']
            time_diff = results['v1_1']['time'] - results['v1_0']['time']
            
            if iter_diff < 0:
                print(f"  v1.1 used {abs(iter_diff)} fewer iterations ✨")
            elif iter_diff > 0:
                print(f"  v1.1 used {iter_diff} more iterations")
                
            if time_diff < 0:
                print(f"  v1.1 was {abs(time_diff):.2f}s faster ⚡")
            elif time_diff > 0:
                print(f"  v1.1 was {time_diff:.2f}s slower")
    
    return 0 if not regression else 1

if __name__ == "__main__":
    exit(main())