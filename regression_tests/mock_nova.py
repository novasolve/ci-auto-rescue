#!/usr/bin/env python3
"""
Mock Nova implementation for testing the regression test framework
Simulates Nova v1.0 and v1.1 behavior for demonstration purposes
"""

import sys
import os
import time
import random
import json
from pathlib import Path
import argparse
import tempfile

def run_tests(repo_path):
    """Simulate running tests and getting results"""
    # Look for test files
    test_files = list(Path(repo_path).glob("tests/test_*.py"))
    
    # Simulate different failure scenarios based on repo name
    repo_name = Path(repo_path).name
    
    if "all_passing" in repo_name:
        return True, 0, "All tests passing"
    elif "slow_tests" in repo_name:
        time.sleep(2)  # Simulate slow tests
        return False, 1, "1 test failed"
    elif "one_line" in repo_name:
        return False, 1, "1 test failed (simple fix needed)"
    else:
        # Random failure count
        failures = random.randint(1, 3)
        return False, failures, f"{failures} tests failed"

def apply_fix(repo_path, iteration):
    """Simulate applying a fix"""
    # Create a dummy patch file
    nova_dir = Path(repo_path) / ".nova" / f"run_{int(time.time())}"
    nova_dir.mkdir(parents=True, exist_ok=True)
    
    diffs_dir = nova_dir / "diffs"
    diffs_dir.mkdir(exist_ok=True)
    
    patch_file = diffs_dir / f"step-{iteration}.patch"
    patch_file.write_text(f"""--- a/src/example.py
+++ b/src/example.py
@@ -1,5 +1,5 @@
 def example():
-    return "broken"
+    return "fixed"
""")
    
    # Write trace file
    trace_file = nova_dir / "trace.jsonl"
    with open(trace_file, 'a') as f:
        f.write(json.dumps({
            "timestamp": time.time(),
            "iteration": iteration,
            "action": "apply_patch",
            "status": "success"
        }) + "\n")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Mock Nova CI-Rescue")
    parser.add_argument("command", choices=["fix", "eval"], help="Command to run")
    parser.add_argument("repo", help="Repository path")
    parser.add_argument("--max-iters", "--max-iterations", type=int, default=6)
    parser.add_argument("--timeout", type=int, default=1200)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--use-deep-agent", action="store_true")
    parser.add_argument("--output", help="Output directory for eval mode")
    
    args = parser.parse_args()
    
    # Determine version from environment
    version = os.environ.get("NOVA_VERSION", "unknown")
    use_deep_agent = os.environ.get("NOVA_USE_DEEP_AGENT") == "true" or args.use_deep_agent
    
    if args.verbose:
        print(f"Nova CI-Rescue Mock - Version: {version}")
        if use_deep_agent:
            print("Using Deep Agent")
        print(f"Repository: {args.repo}")
        print(f"Max iterations: {args.max_iters}")
        print(f"Timeout: {args.timeout}s")
    
    if args.command == "fix":
        repo_path = Path(args.repo)
        if not repo_path.exists():
            print(f"Error: Repository path does not exist: {repo_path}")
            return 1
        
        # Simulate fix iterations
        for iteration in range(1, args.max_iters + 1):
            if args.verbose:
                print(f"\nIteration {iteration}/{args.max_iters}")
            
            # Run tests
            success, failures, message = run_tests(repo_path)
            
            if args.verbose:
                print(f"Test results: {message}")
            
            if success:
                print(f"✅ All tests passed after {iteration} iteration(s)")
                return 0
            
            # Apply fix
            if args.verbose:
                print(f"Applying fix...")
            
            apply_fix(repo_path, iteration)
            
            # Simulate success chance
            if use_deep_agent:
                # v1.1 with Deep Agent has higher success rate
                if random.random() < 0.8:
                    if args.verbose:
                        print("Fix applied successfully")
                    if iteration >= 2:  # Usually fixes by iteration 2-3
                        print(f"✅ All tests passed after {iteration} iteration(s)")
                        return 0
            else:
                # v1.0 legacy has lower success rate
                if random.random() < 0.6:
                    if args.verbose:
                        print("Fix applied")
                    if iteration >= 3:  # Usually needs more iterations
                        print(f"✅ All tests passed after {iteration} iteration(s)")
                        return 0
        
        print(f"❌ Max iterations reached. {failures} test(s) still failing")
        return 1
        
    elif args.command == "eval":
        print("Eval mode not implemented in mock")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
