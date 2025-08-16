#!/usr/bin/env python3
"""
Nova CI-Rescue Regression Test Suite - All-in-One Script
Tests Nova's Deep Agent (v1.1) against Legacy Agent (v1.0) using the same codebase.
"""

import os
import sys
import json
import time
import shutil
import tempfile
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str, color: str = Colors.BLUE):
    """Print a formatted header."""
    print(f"\n{color}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{color}{Colors.BOLD}{text}{Colors.END}")
    print(f"{color}{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_status(text: str, success: bool = True):
    """Print a status message with appropriate color."""
    color = Colors.GREEN if success else Colors.RED
    symbol = "✅" if success else "❌"
    print(f"{color}{symbol} {text}{Colors.END}")

def run_command(cmd: List[str], cwd: Path = None, capture: bool = True, verbose: bool = False) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, and stderr."""
    if verbose:
        print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=capture,
            text=True,
            timeout=300  # 5 minute timeout for individual commands
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)

class NovaRegressionTester:
    """Main class for running Nova regression tests."""
    
    def __init__(self, workspace_dir: Path = None, verbose: bool = False):
        """Initialize the regression tester."""
        self.workspace_dir = workspace_dir or Path.cwd()
        self.verbose = verbose
        self.test_dir = self.workspace_dir / "regression_test_run"
        self.venv_dir = self.test_dir / "venv"
        self.test_repos_dir = self.test_dir / "test_repos"
        self.results_dir = self.test_dir / "results"
        self.nova_cmd = None
        
    def setup_environment(self) -> bool:
        """Set up the test environment."""
        print_header("Setting Up Test Environment")
        
        # Create directories
        print("Creating test directories...")
        self.test_dir.mkdir(exist_ok=True)
        self.test_repos_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)
        print_status("Directories created")
        
        # Create virtual environment
        print("\nCreating virtual environment...")
        cmd = [sys.executable, "-m", "venv", str(self.venv_dir)]
        code, _, err = run_command(cmd, verbose=self.verbose)
        if code != 0:
            print_status(f"Failed to create venv: {err}", False)
            return False
        print_status("Virtual environment created")
        
        # Upgrade pip
        print("\nUpgrading pip...")
        pip_cmd = str(self.venv_dir / "bin" / "pip")
        python_cmd = str(self.venv_dir / "bin" / "python")
        cmd = [python_cmd, "-m", "pip", "install", "--upgrade", "pip"]
        code, _, err = run_command(cmd, verbose=self.verbose)
        if code != 0:
            print_status(f"Failed to upgrade pip: {err}", False)
        else:
            print_status("Pip upgraded")
        
        # Install Nova from current directory
        print("\nInstalling Nova...")
        cmd = [pip_cmd, "install", "-e", str(self.workspace_dir)]
        code, out, err = run_command(cmd, verbose=self.verbose)
        if code != 0:
            print_status(f"Failed to install Nova: {err}", False)
            return False
        print_status("Nova installed")
        
        # Set nova command
        self.nova_cmd = str(self.venv_dir / "bin" / "python")
        
        return True
    
    def create_test_repository(self, name: str, test_content: str, implementation: str) -> Path:
        """Create a test repository with failing tests."""
        repo_dir = self.test_repos_dir / name
        repo_dir.mkdir(exist_ok=True)
        
        # Create src directory and implementation
        src_dir = repo_dir / "src"
        src_dir.mkdir(exist_ok=True)
        
        impl_file = src_dir / "implementation.py"
        impl_file.write_text(implementation)
        
        # Create tests directory and test file
        tests_dir = repo_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        test_file = tests_dir / "test_implementation.py"
        test_file.write_text(test_content)
        
        # Create __init__ files
        (src_dir / "__init__.py").touch()
        (tests_dir / "__init__.py").touch()
        
        return repo_dir
    
    def create_test_repositories(self) -> List[Path]:
        """Create various test repositories for regression testing."""
        print_header("Creating Test Repositories")
        repos = []
        
        # Test Case 1: Simple Math Fixes
        test_content = '''import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.implementation import add, multiply, factorial

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(-2, 3) == -6
    assert multiply(0, 5) == 0

def test_factorial():
    assert factorial(0) == 1
    assert factorial(1) == 1
    assert factorial(5) == 120
    assert factorial(6) == 720
'''
        
        implementation = '''def add(a, b):
    return a + b + 1  # Bug: adds extra 1

def multiply(a, b):
    return a * b + 1  # Bug: adds extra 1

def factorial(n):
    if n == 0:
        return 0  # Bug: should return 1
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result
'''
        
        repo = self.create_test_repository("simple_math", test_content, implementation)
        repos.append(repo)
        print_status(f"Created test repository: {repo.name}")
        
        # Test Case 2: String Operations
        test_content = '''import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.implementation import reverse_string, is_palindrome, capitalize_words

def test_reverse_string():
    assert reverse_string("hello") == "olleh"
    assert reverse_string("") == ""
    assert reverse_string("a") == "a"

def test_is_palindrome():
    assert is_palindrome("racecar") == True
    assert is_palindrome("hello") == False
    assert is_palindrome("") == True

def test_capitalize_words():
    assert capitalize_words("hello world") == "Hello World"
    assert capitalize_words("python programming") == "Python Programming"
'''
        
        implementation = '''def reverse_string(s):
    return s  # Bug: doesn't reverse

def is_palindrome(s):
    return s == reverse_string(s)  # Will fail due to reverse_string bug

def capitalize_words(text):
    return text.upper()  # Bug: capitalizes everything instead of title case
'''
        
        repo = self.create_test_repository("string_ops", test_content, implementation)
        repos.append(repo)
        print_status(f"Created test repository: {repo.name}")
        
        # Test Case 3: List Operations
        test_content = '''import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.implementation import find_max, remove_duplicates, list_sum

def test_find_max():
    assert find_max([1, 5, 3, 9, 2]) == 9
    assert find_max([-1, -5, -3]) == -1
    assert find_max([42]) == 42

def test_remove_duplicates():
    assert remove_duplicates([1, 2, 2, 3, 1]) == [1, 2, 3]
    assert remove_duplicates([]) == []
    assert remove_duplicates([1, 1, 1]) == [1]

def test_list_sum():
    assert list_sum([1, 2, 3, 4]) == 10
    assert list_sum([]) == 0
    assert list_sum([-1, 1]) == 0
'''
        
        implementation = '''def find_max(lst):
    if not lst:
        return None
    return lst[0]  # Bug: returns first element instead of max

def remove_duplicates(lst):
    return lst  # Bug: doesn't remove duplicates

def list_sum(lst):
    total = 1  # Bug: starts from 1 instead of 0
    for num in lst:
        total += num
    return total
'''
        
        repo = self.create_test_repository("list_ops", test_content, implementation)
        repos.append(repo)
        print_status(f"Created test repository: {repo.name}")
        
        return repos
    
    def run_nova_fix(self, repo_path: Path, use_legacy: bool = False, max_iters: int = 6) -> Dict:
        """Run Nova fix on a repository."""
        agent_type = "Legacy Agent (v1.0)" if use_legacy else "Deep Agent (v1.1)"
        print(f"\n{Colors.YELLOW}Running {agent_type} on {repo_path.name}...{Colors.END}")
        
        # Build command
        cmd = [self.nova_cmd, "-m", "nova", "fix", str(repo_path)]
        if use_legacy:
            cmd.append("--legacy-agent")
        cmd.extend(["--max-iters", str(max_iters)])
        
        # Set environment variable for API key check
        env = os.environ.copy()
        if not env.get("OPENAI_API_KEY"):
            print_status("Warning: OPENAI_API_KEY not set - Nova will fail", False)
        
        # Run Nova
        start_time = time.time()
        code, stdout, stderr = run_command(cmd, env=env, verbose=self.verbose)
        elapsed = time.time() - start_time
        
        # Parse results
        success = (code == 0)
        iterations = 0
        
        # Try to extract iteration count from output
        import re
        for pattern in [
            r"Iterations completed:\s*(\d+)/",
            r"Iteration\s+(\d+)/",
            r"Fixed after\s+(\d+)\s+iteration"
        ]:
            matches = re.findall(pattern, stdout + stderr, re.IGNORECASE)
            if matches:
                iterations = max(int(m) for m in matches)
                break
        
        result = {
            "agent_type": agent_type,
            "success": success,
            "iterations": iterations,
            "time": elapsed,
            "exit_code": code
        }
        
        # Print summary
        status_text = f"{agent_type}: {'✅ Success' if success else '❌ Failed'} | Iterations: {iterations} | Time: {elapsed:.2f}s"
        print_status(status_text, success)
        
        return result
    
    def run_comparison(self, repo_path: Path, max_iters: int = 6) -> Dict:
        """Run both agents on a repository and compare results."""
        print_header(f"Testing: {repo_path.name}", Colors.BOLD)
        
        results = {}
        
        # Run Legacy Agent (v1.0)
        results["v1_0"] = self.run_nova_fix(repo_path, use_legacy=True, max_iters=max_iters)
        
        # Run Deep Agent (v1.1)
        results["v1_1"] = self.run_nova_fix(repo_path, use_legacy=False, max_iters=max_iters)
        
        # Determine winner
        v1_0 = results["v1_0"]
        v1_1 = results["v1_1"]
        
        if v1_0["success"] and not v1_1["success"]:
            winner = "v1_0"
            regression = True
        elif v1_1["success"] and not v1_0["success"]:
            winner = "v1_1"
            regression = False
        elif v1_0["success"] and v1_1["success"]:
            # Both succeeded - compare efficiency
            if v1_0["iterations"] < v1_1["iterations"]:
                winner = "v1_0_more_efficient"
            elif v1_1["iterations"] < v1_0["iterations"]:
                winner = "v1_1_more_efficient"
            elif v1_0["time"] < v1_1["time"]:
                winner = "v1_0_faster"
            elif v1_1["time"] < v1_0["time"]:
                winner = "v1_1_faster"
            else:
                winner = "tie"
            regression = False
        else:
            winner = "both_failed"
            regression = False
        
        return {
            "repository": repo_path.name,
            "results": results,
            "winner": winner,
            "regression": regression
        }
    
    def generate_report(self, all_results: List[Dict]) -> str:
        """Generate a comprehensive report from test results."""
        report = []
        report.append("# Nova CI-Rescue Regression Test Report")
        report.append(f"\n**Date:** {datetime.now().isoformat()}")
        report.append(f"**Test Count:** {len(all_results)}")
        
        # Calculate statistics
        v1_0_successes = sum(1 for r in all_results if r["results"]["v1_0"]["success"])
        v1_1_successes = sum(1 for r in all_results if r["results"]["v1_1"]["success"])
        regressions = sum(1 for r in all_results if r.get("regression", False))
        
        report.append("\n## Summary Statistics")
        report.append(f"- **Legacy Agent (v1.0) Success Rate:** {v1_0_successes}/{len(all_results)} ({v1_0_successes/len(all_results)*100:.1f}%)")
        report.append(f"- **Deep Agent (v1.1) Success Rate:** {v1_1_successes}/{len(all_results)} ({v1_1_successes/len(all_results)*100:.1f}%)")
        report.append(f"- **Regressions Detected:** {regressions}")
        
        # Success criteria check
        report.append("\n## Success Criteria")
        success_rate = v1_1_successes / len(all_results) * 100 if all_results else 0
        no_regression = regressions == 0
        
        report.append(f"- ✅ Fix success rate ≥ 70%: {'✅ PASS' if success_rate >= 70 else '❌ FAIL'} ({success_rate:.1f}%)")
        report.append(f"- ✅ No regressions vs v1.0: {'✅ PASS' if no_regression else '❌ FAIL'} ({regressions} regressions)")
        
        # Detailed results
        report.append("\n## Detailed Results")
        
        for result in all_results:
            report.append(f"\n### {result['repository']}")
            
            v1_0 = result["results"]["v1_0"]
            v1_1 = result["results"]["v1_1"]
            
            report.append("\n| Metric | Legacy Agent (v1.0) | Deep Agent (v1.1) |")
            report.append("|--------|---------------------|-------------------|")
            report.append(f"| Success | {'✅' if v1_0['success'] else '❌'} | {'✅' if v1_1['success'] else '❌'} |")
            report.append(f"| Iterations | {v1_0['iterations']} | {v1_1['iterations']} |")
            report.append(f"| Time (s) | {v1_0['time']:.2f} | {v1_1['time']:.2f} |")
            
            report.append(f"\n**Winner:** {result['winner']}")
            if result.get("regression"):
                report.append("**⚠️ REGRESSION DETECTED**")
        
        return "\n".join(report)
    
    def run_full_test_suite(self) -> bool:
        """Run the complete regression test suite."""
        print_header("Nova CI-Rescue Regression Test Suite", Colors.GREEN)
        
        # Check for API key
        if not os.environ.get("OPENAI_API_KEY"):
            print_status("ERROR: OPENAI_API_KEY environment variable not set!", False)
            print("\nPlease set your OpenAI API key:")
            print("  export OPENAI_API_KEY='your-key-here'")
            return False
        
        # Setup environment
        if not self.setup_environment():
            print_status("Environment setup failed", False)
            return False
        
        # Create test repositories
        test_repos = self.create_test_repositories()
        
        # Run comparisons
        print_header("Running Regression Tests")
        all_results = []
        
        for repo in test_repos:
            result = self.run_comparison(repo)
            all_results.append(result)
            
            # Save intermediate results
            result_file = self.results_dir / f"{repo.name}_results.json"
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2)
        
        # Generate and save report
        print_header("Generating Report")
        report = self.generate_report(all_results)
        
        report_file = self.results_dir / "regression_report.md"
        report_file.write_text(report)
        print_status(f"Report saved to: {report_file}")
        
        # Save all results as JSON
        all_results_file = self.results_dir / "all_results.json"
        with open(all_results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print_status(f"Results saved to: {all_results_file}")
        
        # Print summary
        print_header("Test Suite Complete!", Colors.GREEN)
        print(report)
        
        # Check for regressions
        regressions = sum(1 for r in all_results if r.get("regression", False))
        if regressions > 0:
            print_status(f"\n⚠️  {regressions} regression(s) detected!", False)
            return False
        else:
            print_status("\n✅ No regressions detected!", True)
            return True
    
    def cleanup(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            print(f"\nCleaning up {self.test_dir}...")
            shutil.rmtree(self.test_dir)
            print_status("Cleanup complete")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Nova CI-Rescue Regression Test Suite - Tests Deep Agent vs Legacy Agent"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--keep-files",
        action="store_true",
        help="Keep test files after completion (don't cleanup)"
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Path to Nova workspace (default: current directory)"
    )
    
    args = parser.parse_args()
    
    # Create and run tester
    tester = NovaRegressionTester(
        workspace_dir=args.workspace,
        verbose=args.verbose
    )
    
    try:
        success = tester.run_full_test_suite()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted by user")
        sys.exit(130)
    except Exception as e:
        print_status(f"Unexpected error: {e}", False)
        import traceback
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)
    finally:
        if not args.keep_files:
            tester.cleanup()

if __name__ == "__main__":
    main()
