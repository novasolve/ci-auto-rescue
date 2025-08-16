#!/usr/bin/env python3
"""
Nova CI-Rescue Test Suite - Single consolidated script for testing Nova Deep Agent
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

def run_command(cmd: List[str], cwd: Path = None, timeout: int = 300, capture: bool = True, 
                verbose: bool = False, env: dict = None) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, and stderr."""
    if verbose:
        print(f"Running: {' '.join(cmd)}")
    
    # Use provided env or current environment
    if env is None:
        env = os.environ.copy()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=capture,
            text=True,
            timeout=timeout,
            env=env
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return 1, "", str(e)

class NovaTestSuite:
    """Unified test suite for Nova CI-Rescue."""
    
    def __init__(self, workspace_dir: Path = None, verbose: bool = False, timeout: int = 300):
        """Initialize the test suite."""
        self.workspace_dir = workspace_dir or Path.cwd()
        self.verbose = verbose
        self.timeout = timeout
        self.test_dir = self.workspace_dir / "nova_test_run"
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
        
        # Get paths for venv python and pip
        if sys.platform == "win32":
            python_cmd = str(self.venv_dir / "Scripts" / "python.exe")
            pip_cmd = str(self.venv_dir / "Scripts" / "pip.exe")
        else:
            python_cmd = str(self.venv_dir / "bin" / "python")
            pip_cmd = str(self.venv_dir / "bin" / "pip")
        
        # Upgrade pip
        print("\nUpgrading pip...")
        cmd = [python_cmd, "-m", "pip", "install", "--upgrade", "pip", "--quiet"]
        code, _, err = run_command(cmd, verbose=self.verbose)
        if code != 0:
            print_status(f"Warning: Failed to upgrade pip: {err}", False)
        else:
            print_status("Pip upgraded")
        
        # Install Nova from current directory
        print("\nInstalling Nova CI-Rescue...")
        cmd = [pip_cmd, "install", "-e", str(self.workspace_dir), "--quiet"]
        code, out, err = run_command(cmd, verbose=self.verbose)
        if code != 0:
            print_status(f"Failed to install Nova: {err}", False)
            return False
        print_status("Nova installed")
        
        # Set nova command
        self.nova_cmd = python_cmd
        
        return True
    
    def create_test_repository(self, name: str, description: str, test_content: str, implementation: str) -> Path:
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
        
        # Create a simple pyproject.toml for pytest
        pyproject = repo_dir / "pyproject.toml"
        pyproject.write_text("""[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
""")
        
        return repo_dir
    
    def create_test_scenarios(self) -> List[Dict]:
        """Create various test scenarios for Nova."""
        print_header("Creating Test Scenarios")
        scenarios = []
        
        # Scenario 1: Simple Math Bugs
        test_content = '''import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.implementation import add, multiply, divide

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(-2, 3) == -6
    assert multiply(0, 5) == 0

def test_divide():
    assert divide(10, 2) == 5
    assert divide(7, 2) == 3.5
    assert divide(0, 5) == 0
'''
        
        implementation = '''def add(a, b):
    return a + b + 1  # Bug: adds extra 1

def multiply(a, b):
    return a * b + 1  # Bug: adds extra 1

def divide(a, b):
    if b == 0:
        return None
    return a // b  # Bug: integer division instead of float
'''
        
        repo = self.create_test_repository(
            "simple_math",
            "Simple arithmetic operations with bugs",
            test_content,
            implementation
        )
        scenarios.append({
            "name": "simple_math",
            "description": "Simple arithmetic bugs",
            "path": repo,
            "expected_difficulty": "easy"
        })
        print_status(f"Created scenario: simple_math")
        
        # Scenario 2: String Manipulation
        test_content = '''import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.implementation import reverse_string, capitalize_first, count_vowels

def test_reverse_string():
    assert reverse_string("hello") == "olleh"
    assert reverse_string("") == ""
    assert reverse_string("a") == "a"
    assert reverse_string("12345") == "54321"

def test_capitalize_first():
    assert capitalize_first("hello world") == "Hello world"
    assert capitalize_first("HELLO") == "HELLO"
    assert capitalize_first("") == ""
    assert capitalize_first("123") == "123"

def test_count_vowels():
    assert count_vowels("hello") == 2
    assert count_vowels("AEIOU") == 5
    assert count_vowels("xyz") == 0
    assert count_vowels("") == 0
'''
        
        implementation = '''def reverse_string(s):
    return s  # Bug: doesn't reverse

def capitalize_first(text):
    if not text:
        return text
    return text.upper()  # Bug: capitalizes everything

def count_vowels(text):
    vowels = "aeiou"
    return sum(1 for c in text if c in vowels)  # Bug: doesn't handle uppercase
'''
        
        repo = self.create_test_repository(
            "string_ops",
            "String manipulation functions with bugs",
            test_content,
            implementation
        )
        scenarios.append({
            "name": "string_ops",
            "description": "String manipulation bugs",
            "path": repo,
            "expected_difficulty": "easy"
        })
        print_status(f"Created scenario: string_ops")
        
        # Scenario 3: List Operations
        test_content = '''import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.implementation import find_max, remove_duplicates, list_average

def test_find_max():
    assert find_max([1, 5, 3, 9, 2]) == 9
    assert find_max([-1, -5, -3]) == -1
    assert find_max([42]) == 42
    assert find_max([]) is None

def test_remove_duplicates():
    assert remove_duplicates([1, 2, 2, 3, 1]) == [1, 2, 3]
    assert remove_duplicates([]) == []
    assert remove_duplicates([1, 1, 1]) == [1]
    assert remove_duplicates([1, 2, 3]) == [1, 2, 3]

def test_list_average():
    assert list_average([1, 2, 3, 4, 5]) == 3.0
    assert list_average([10]) == 10.0
    assert list_average([]) == 0
    assert list_average([1, 2]) == 1.5
'''
        
        implementation = '''def find_max(lst):
    if not lst:
        return None
    return lst[0]  # Bug: returns first element instead of max

def remove_duplicates(lst):
    return list(lst)  # Bug: doesn't remove duplicates

def list_average(lst):
    if not lst:
        return 0
    return sum(lst) // len(lst)  # Bug: integer division instead of float
'''
        
        repo = self.create_test_repository(
            "list_ops",
            "List operations with bugs",
            test_content,
            implementation
        )
        scenarios.append({
            "name": "list_ops",
            "description": "List operation bugs",
            "path": repo,
            "expected_difficulty": "easy"
        })
        print_status(f"Created scenario: list_ops")
        
        # Scenario 4: Edge Cases
        test_content = '''import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.implementation import safe_divide, validate_email, fibonacci

def test_safe_divide():
    assert safe_divide(10, 2) == 5.0
    assert safe_divide(10, 0) == float('inf')
    assert safe_divide(0, 10) == 0.0
    assert safe_divide(-10, 2) == -5.0

def test_validate_email():
    assert validate_email("user@example.com") == True
    assert validate_email("test.user@domain.co.uk") == True
    assert validate_email("invalid.email") == False
    assert validate_email("@example.com") == False
    assert validate_email("user@") == False
    assert validate_email("") == False

def test_fibonacci():
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    assert fibonacci(2) == 1
    assert fibonacci(5) == 5
    assert fibonacci(10) == 55
'''
        
        implementation = '''def safe_divide(a, b):
    if b == 0:
        return 0  # Bug: should return inf
    return a / b

def validate_email(email):
    return "@" in email and "." in email  # Bug: too simplistic

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2) - 1  # Bug: subtracts 1
'''
        
        repo = self.create_test_repository(
            "edge_cases",
            "Functions with edge case handling bugs",
            test_content,
            implementation
        )
        scenarios.append({
            "name": "edge_cases",
            "description": "Edge case handling bugs",
            "path": repo,
            "expected_difficulty": "medium"
        })
        print_status(f"Created scenario: edge_cases")
        
        return scenarios
    
    def run_nova_on_scenario(self, scenario: Dict) -> Dict:
        """Run Nova Deep Agent on a test scenario."""
        print(f"\n{Colors.YELLOW}Testing: {scenario['name']}{Colors.END}")
        print(f"Description: {scenario['description']}")
        
        repo_path = scenario['path']
        
        # First, run pytest to count initial failures
        print("Running initial tests...")
        pytest_cmd = [self.nova_cmd, "-m", "pytest", str(repo_path), "--tb=short", "--quiet"]
        code, stdout, stderr = run_command(pytest_cmd, cwd=repo_path, timeout=30, verbose=self.verbose)
        
        # Count failures from pytest output
        import re
        initial_failures = 0
        output = stdout + stderr
        if "failed" in output.lower():
            # Try to extract failure count
            match = re.search(r'(\d+) failed', output)
            if match:
                initial_failures = int(match.group(1))
            else:
                initial_failures = 1  # At least one failure
        
        print(f"Initial failing tests: {initial_failures}")
        
        if initial_failures == 0:
            print_status("No failing tests to fix!")
            return {
                "scenario": scenario['name'],
                "description": scenario['description'],
                "expected_difficulty": scenario['expected_difficulty'],
                "success": True,
                "initial_failures": 0,
                "final_failures": 0,
                "tests_fixed": 0,
                "iterations": 0,
                "time_seconds": 0,
                "exit_reason": "NO_FAILURES"
            }
        
        # Build Nova command
        cmd = [self.nova_cmd, "-m", "nova", "fix", str(repo_path)]
        cmd.extend(["--max-iters", "6"])
        
        if self.verbose:
            cmd.append("--verbose")
        
        # Check for API key
        env = os.environ.copy()
        if not env.get("OPENAI_API_KEY"):
            print_status("Warning: OPENAI_API_KEY not set - Nova will fail", False)
        
        # Run Nova
        print("Running Nova Deep Agent...")
        start_time = time.time()
        code, stdout, stderr = run_command(cmd, env=env, timeout=self.timeout, verbose=self.verbose)
        elapsed = time.time() - start_time
        
        # Parse results
        success = (code == 0)
        iterations = 0
        exit_reason = "SUCCESS" if success else "ERROR"
        output = stdout + stderr
        
        # Extract metrics from output
        for pattern in [
            r"Iterations completed:\s*(\d+)/",
            r"Iteration\s+(\d+)/",
            r"Fixed after\s+(\d+)\s+iteration"
        ]:
            matches = re.findall(pattern, output, re.IGNORECASE)
            if matches:
                iterations = max(int(m) for m in matches)
                break
        
        # Check for specific exit reasons
        if "timeout" in output.lower():
            exit_reason = "TIMEOUT"
        elif "max" in output.lower() and "iterations" in output.lower():
            exit_reason = "MAX_ITERATIONS"
        elif not env.get("OPENAI_API_KEY"):
            exit_reason = "NO_API_KEY"
        
        # Run final tests to count remaining failures
        final_failures = initial_failures
        if success:
            print("Running final tests...")
            code, stdout, stderr = run_command(pytest_cmd, cwd=repo_path, timeout=30)
            output = stdout + stderr
            if "failed" not in output.lower():
                final_failures = 0
            else:
                match = re.search(r'(\d+) failed', output)
                if match:
                    final_failures = int(match.group(1))
        
        result = {
            "scenario": scenario['name'],
            "description": scenario['description'],
            "expected_difficulty": scenario['expected_difficulty'],
            "success": success and final_failures == 0,
            "initial_failures": initial_failures,
            "final_failures": final_failures,
            "tests_fixed": initial_failures - final_failures,
            "iterations": iterations,
            "time_seconds": round(elapsed, 2),
            "exit_reason": exit_reason
        }
        
        # Print result
        if result["success"]:
            print_status(f"✅ Success! Fixed all {initial_failures} failing tests in {iterations} iterations ({elapsed:.1f}s)")
        else:
            print_status(f"❌ Failed. Fixed {result['tests_fixed']}/{initial_failures} tests. Exit: {exit_reason}", False)
        
        return result
    
    def generate_report(self, results: List[Dict]) -> str:
        """Generate a test report."""
        report = []
        report.append("# Nova CI-Rescue Deep Agent Test Report")
        report.append(f"\n**Date:** {datetime.now().isoformat()}")
        report.append(f"**Test Scenarios:** {len(results)}")
        
        # Calculate statistics
        total_scenarios = len(results)
        successful = sum(1 for r in results if r["success"])
        total_tests = sum(r["initial_failures"] for r in results)
        tests_fixed = sum(r["tests_fixed"] for r in results)
        avg_time = sum(r["time_seconds"] for r in results) / len(results) if results else 0
        avg_iterations = sum(r["iterations"] for r in results) / len(results) if results else 0
        
        report.append("\n## Summary Statistics")
        report.append(f"- **Success Rate:** {successful}/{total_scenarios} scenarios ({successful/total_scenarios*100:.1f}%)")
        fix_rate = (tests_fixed/total_tests*100) if total_tests else 0
        report.append(f"- **Tests Fixed:** {tests_fixed}/{total_tests} ({fix_rate:.1f}%)")
        report.append(f"- **Average Time:** {avg_time:.1f} seconds")
        report.append(f"- **Average Iterations:** {avg_iterations:.1f}")
        
        # Success criteria
        report.append("\n## Success Criteria")
        success_rate = successful / total_scenarios * 100 if total_scenarios else 0
        report.append(f"- {'✅' if success_rate >= 70 else '❌'} Fix success rate ≥ 70%: {success_rate:.1f}%")
        report.append(f"- {'✅' if tests_fixed == total_tests else '❌'} All tests fixed: {tests_fixed}/{total_tests}")
        
        # Detailed results
        report.append("\n## Detailed Results")
        report.append("\n| Scenario | Difficulty | Success | Tests Fixed | Iterations | Time | Exit Reason |")
        report.append("|----------|------------|---------|-------------|------------|------|-------------|")
        
        for r in results:
            success_icon = "✅" if r["success"] else "❌"
            report.append(f"| {r['scenario']} | {r['expected_difficulty']} | {success_icon} | {r['tests_fixed']}/{r['initial_failures']} | {r['iterations']} | {r['time_seconds']:.1f}s | {r['exit_reason']} |")
        
        # Recommendations
        report.append("\n## Analysis")
        if success_rate >= 90:
            report.append("- **Excellent Performance**: Deep Agent successfully fixed nearly all test scenarios.")
        elif success_rate >= 70:
            report.append("- **Good Performance**: Deep Agent meets success criteria but has room for improvement.")
        else:
            report.append("- **Needs Improvement**: Deep Agent struggles with some scenarios.")
        
        # Identify problem areas
        failures = [r for r in results if not r["success"]]
        if failures:
            report.append("\n### Failed Scenarios:")
            for f in failures:
                report.append(f"- **{f['scenario']}**: {f['exit_reason']} (fixed {f['tests_fixed']}/{f['initial_failures']} tests)")
        
        return "\n".join(report)
    
    def run_test_suite(self) -> bool:
        """Run the complete test suite."""
        print_header("Nova CI-Rescue Deep Agent Test Suite", Colors.GREEN)
        
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
        
        # Create test scenarios
        scenarios = self.create_test_scenarios()
        
        # Run tests
        print_header("Running Deep Agent Tests")
        all_results = []
        
        for scenario in scenarios:
            result = self.run_nova_on_scenario(scenario)
            all_results.append(result)
            
            # Save intermediate result
            result_file = self.results_dir / f"{scenario['name']}_result.json"
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2)
        
        # Generate and save report
        print_header("Test Results")
        report = self.generate_report(all_results)
        
        report_file = self.results_dir / "test_report.md"
        report_file.write_text(report)
        print_status(f"Report saved to: {report_file}")
        
        # Save all results as JSON
        all_results_file = self.results_dir / "all_results.json"
        with open(all_results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print_status(f"Results saved to: {all_results_file}")
        
        # Print report
        print(report)
        
        # Determine overall success
        success_rate = sum(1 for r in all_results if r["success"]) / len(all_results) * 100
        if success_rate >= 70:
            print_status(f"\n✅ Test suite PASSED! Success rate: {success_rate:.1f}%", True)
            return True
        else:
            print_status(f"\n❌ Test suite FAILED. Success rate: {success_rate:.1f}% (need ≥70%)", False)
            return False
    
    def cleanup(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            print(f"\nCleaning up {self.test_dir}...")
            shutil.rmtree(self.test_dir)
            print_status("Cleanup complete")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Nova CI-Rescue Test Suite - Tests the Deep Agent on various scenarios"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--keep-files",
        action="store_true",
        help="Keep test files after completion"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout for each Nova run in seconds (default: 300)"
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Path to Nova workspace (default: current directory)"
    )
    
    args = parser.parse_args()
    
    # Create and run tester
    tester = NovaTestSuite(
        workspace_dir=args.workspace,
        verbose=args.verbose,
        timeout=args.timeout
    )
    
    try:
        success = tester.run_test_suite()
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
