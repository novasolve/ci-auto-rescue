#!/usr/bin/env python3
"""
Nova CI-Rescue Unified Test Suite - Best of All Worlds
Combines features from all three test suites into one comprehensive solution.

Features:
- Self-contained with automatic environment setup
- Supports both version comparison (v1.0 vs v1.1) and single version testing
- YAML configuration optional (has built-in tests)
- Comprehensive edge case coverage (unfixable bugs, no-op patches, etc.)
- Advanced result analysis and professional reporting
- CI/CD ready with proper exit codes
"""

import argparse
import os
import sys
import subprocess
import time
import yaml
import json
import re
import shutil
import tempfile
import traceback
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

# ============================================================================
# ANSI Color Codes for Beautiful Terminal Output
# ============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'
    
    @staticmethod
    def disable():
        """Disable colors for non-TTY outputs."""
        Colors.GREEN = Colors.YELLOW = Colors.RED = ''
        Colors.BLUE = Colors.CYAN = Colors.MAGENTA = ''
        Colors.BOLD = Colors.END = ''

# ============================================================================
# Test Scenario Generator
# ============================================================================

class SyntheticRepoGenerator:
    """Generates synthetic test repositories for various scenarios."""
    
    def __init__(self, base_path: Path = Path("test_repos")):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    def generate_all(self) -> List[Dict[str, Any]]:
        """Generate all test repositories and return their configurations."""
        repos = []
        
        # Generate each type of test repo
        generators = [
            ("simple_math", self.generate_simple_math_repo, "easy", 
             "Simple mathematical operations with basic bugs"),
            ("string_ops", self.generate_string_ops_repo, "easy",
             "String manipulation with encoding issues"),
            ("list_ops", self.generate_list_ops_repo, "easy",
             "List operations with logic errors"),
            ("off_by_one", self.generate_off_by_one_repo, "easy",
             "Classic off-by-one error"),
            ("edge_cases", self.generate_edge_cases_repo, "medium",
             "Edge case handling bugs"),
            ("unfixable_bug", self.generate_unfixable_repo, "hard",
             "Test with incorrect expectation (unfixable)"),
            ("no_op_patch", self.generate_no_op_patch_repo, "hard",
             "Test that always fails (no-op patch)"),
            ("import_issues", self.generate_import_issues_repo, "medium",
             "Import and module resolution problems"),
            ("type_hints", self.generate_type_hints_repo, "medium",
             "Type hint related failures"),
            ("exception_handling", self.generate_exception_handling_repo, "medium",
             "Exception handling errors"),
        ]
        
        for name, generator, difficulty, description in generators:
            repo_path = generator()
            repos.append({
                "name": name,
                "path": str(repo_path),
                "difficulty": difficulty,
                "description": description,
                "max_iters": 6,
                "timeout": 600
            })
            
        return repos
    
    def generate_simple_math_repo(self) -> Path:
        """Generate a simple math repository with basic bugs."""
        repo_path = self.base_path / "simple_math"
        if repo_path.exists():
            shutil.rmtree(repo_path)
        repo_path.mkdir()
        
        # Source file with bugs
        src_path = repo_path / "src"
        src_path.mkdir()
        with open(src_path / "__init__.py", 'w') as f:
            f.write("")
        with open(src_path / "math_ops.py", 'w') as f:
            f.write("""def add(a, b):
    return a + b + 1  # Bug: adds extra 1

def multiply(a, b):
    return a * b + 1  # Bug: adds extra 1

def factorial(n):
    if n < 0:
        raise ValueError("Negative not allowed")
    if n == 0:
        return 1
    result = 1
    for i in range(1, n):  # Bug: should be range(1, n+1)
        result *= i
    return result

def divide(a, b):
    if b == 0:
        return float('inf')
    return a // b  # Bug: integer division instead of float
""")
        
        # Test file
        tests_path = repo_path / "tests"
        tests_path.mkdir()
        with open(tests_path / "__init__.py", 'w') as f:
            f.write("")
        with open(tests_path / "test_math_ops.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.math_ops import add, multiply, factorial, divide

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
    assert factorial(5) == 120
    assert factorial(3) == 6

def test_divide():
    assert divide(10, 2) == 5.0
    assert divide(7, 2) == 3.5
    assert divide(0, 5) == 0.0
""")
        
        # Pytest config
        with open(repo_path / "pyproject.toml", 'w') as f:
            f.write("""[tool.pytest.ini_options]
python_files = ["test_*.py"]
pythonpath = ["."]
""")
        
        return repo_path
    
    def generate_string_ops_repo(self) -> Path:
        """Generate string operations repository with bugs."""
        repo_path = self.base_path / "string_ops"
        if repo_path.exists():
            shutil.rmtree(repo_path)
        repo_path.mkdir()
        
        src_path = repo_path / "src"
        src_path.mkdir()
        with open(src_path / "__init__.py", 'w') as f:
            f.write("")
        with open(src_path / "string_utils.py", 'w') as f:
            f.write("""def reverse_string(s):
    # Bug: uses reversed incorrectly
    return ''.join(reversed(s))[::-1]

def count_vowels(s):
    vowels = 'aeiou'  # Bug: missing uppercase
    count = 0
    for char in s:
        if char in vowels:
            count += 2  # Bug: counts each vowel twice
    return count

def capitalize_first(text):
    if not text:
        return text
    return text.upper()  # Bug: capitalizes everything

def remove_duplicates(text):
    # Bug: doesn't actually remove duplicates
    return text
""")
        
        tests_path = repo_path / "tests"
        tests_path.mkdir()
        with open(tests_path / "__init__.py", 'w') as f:
            f.write("")
        with open(tests_path / "test_string_utils.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.string_utils import reverse_string, count_vowels, capitalize_first, remove_duplicates

def test_reverse_string():
    assert reverse_string("hello") == "olleh"
    assert reverse_string("") == ""
    assert reverse_string("a") == "a"

def test_count_vowels():
    assert count_vowels("hello") == 2
    assert count_vowels("AEIOU") == 5
    assert count_vowels("xyz") == 0

def test_capitalize_first():
    assert capitalize_first("hello world") == "Hello world"
    assert capitalize_first("") == ""
    
def test_remove_duplicates():
    assert remove_duplicates("aabbcc") == "abc"
    assert remove_duplicates("hello") == "helo"
""")
        
        with open(repo_path / "pyproject.toml", 'w') as f:
            f.write("""[tool.pytest.ini_options]
python_files = ["test_*.py"]
pythonpath = ["."]
""")
        
        return repo_path
    
    def generate_list_ops_repo(self) -> Path:
        """Generate list operations repository with bugs."""
        repo_path = self.base_path / "list_ops"
        if repo_path.exists():
            shutil.rmtree(repo_path)
        repo_path.mkdir()
        
        src_path = repo_path / "src"
        src_path.mkdir()
        with open(src_path / "__init__.py", 'w') as f:
            f.write("")
        with open(src_path / "list_utils.py", 'w') as f:
            f.write("""def sort_list(lst):
    # Bug: sorts in place and returns None
    lst.sort()
    
def filter_positive(lst):
    # Bug: treats 0 as positive
    return [x for x in lst if x >= 0]

def find_max(lst):
    if not lst:
        return None
    return lst[0]  # Bug: returns first element

def remove_duplicates(lst):
    return list(lst)  # Bug: doesn't remove duplicates

def list_average(lst):
    if not lst:
        return 0
    return sum(lst) // len(lst)  # Bug: integer division
""")
        
        tests_path = repo_path / "tests"
        tests_path.mkdir()
        with open(tests_path / "__init__.py", 'w') as f:
            f.write("")
        with open(tests_path / "test_list_utils.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.list_utils import sort_list, filter_positive, find_max, remove_duplicates, list_average

def test_sort_list():
    data = [3, 1, 2]
    result = sort_list(data.copy())
    assert result == [1, 2, 3]

def test_filter_positive():
    assert filter_positive([-1, 0, 5, 2]) == [5, 2]
    
def test_find_max():
    assert find_max([1, 5, 3, 9, 2]) == 9
    assert find_max([-1, -5, -3]) == -1
    
def test_remove_duplicates():
    assert remove_duplicates([1, 2, 2, 3, 1]) == [1, 2, 3]
    
def test_list_average():
    assert list_average([1, 2, 3, 4, 5]) == 3.0
    assert list_average([1, 2]) == 1.5
""")
        
        with open(repo_path / "pyproject.toml", 'w') as f:
            f.write("""[tool.pytest.ini_options]
python_files = ["test_*.py"]
pythonpath = ["."]
""")
        
        return repo_path
    
    def generate_off_by_one_repo(self) -> Path:
        """Generate repository with off-by-one bug."""
        repo_path = self.base_path / "off_by_one"
        if repo_path.exists():
            shutil.rmtree(repo_path)
        repo_path.mkdir()
        
        src_path = repo_path / "src"
        src_path.mkdir()
        with open(src_path / "__init__.py", 'w') as f:
            f.write("")
        with open(src_path / "math_utils.py", 'w') as f:
            f.write("""def sum_list(numbers):
    # Bug: Does not include the last element
    if not numbers:
        return 0
    return sum(numbers[:-1])

def get_nth_element(lst, n):
    # Bug: off-by-one in index
    if n <= 0 or n > len(lst):
        return None
    return lst[n]  # Should be lst[n-1]
""")
        
        tests_path = repo_path / "tests"
        tests_path.mkdir()
        with open(tests_path / "__init__.py", 'w') as f:
            f.write("")
        with open(tests_path / "test_math_utils.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.math_utils import sum_list, get_nth_element

def test_sum_list():
    assert sum_list([1, 2, 3, 4]) == 10
    assert sum_list([5]) == 5
    assert sum_list([]) == 0

def test_get_nth_element():
    assert get_nth_element([10, 20, 30], 1) == 10
    assert get_nth_element([10, 20, 30], 3) == 30
    assert get_nth_element([10], 1) == 10
""")
        
        with open(repo_path / "pyproject.toml", 'w') as f:
            f.write("""[tool.pytest.ini_options]
python_files = ["test_*.py"]
pythonpath = ["."]
""")
        
        return repo_path
    
    def generate_edge_cases_repo(self) -> Path:
        """Generate repository with edge case bugs."""
        repo_path = self.base_path / "edge_cases"
        if repo_path.exists():
            shutil.rmtree(repo_path)
        repo_path.mkdir()
        
        src_path = repo_path / "src"
        src_path.mkdir()
        with open(src_path / "__init__.py", 'w') as f:
            f.write("")
        with open(src_path / "edge_handlers.py", 'w') as f:
            f.write("""def safe_divide(a, b):
    if b == 0:
        return 0  # Bug: should return inf
    return a / b

def validate_email(email):
    # Bug: too simplistic
    return "@" in email and "." in email

def fibonacci(n):
    if n <= 1:
        return n
    # Bug: subtracts 1
    return fibonacci(n-1) + fibonacci(n-2) - 1

def parse_number(s):
    try:
        return int(s)  # Bug: should handle floats too
    except:
        return None
""")
        
        tests_path = repo_path / "tests"
        tests_path.mkdir()
        with open(tests_path / "__init__.py", 'w') as f:
            f.write("")
        with open(tests_path / "test_edge_handlers.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.edge_handlers import safe_divide, validate_email, fibonacci, parse_number

def test_safe_divide():
    assert safe_divide(10, 2) == 5.0
    assert safe_divide(10, 0) == float('inf')
    assert safe_divide(0, 10) == 0.0

def test_validate_email():
    assert validate_email("user@example.com") == True
    assert validate_email("test.user@domain.co.uk") == True
    assert validate_email("invalid.email") == False
    assert validate_email("@example.com") == False
    assert validate_email("user@") == False

def test_fibonacci():
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    assert fibonacci(2) == 1
    assert fibonacci(5) == 5

def test_parse_number():
    assert parse_number("42") == 42
    assert parse_number("3.14") == 3.14
    assert parse_number("invalid") == None
""")
        
        with open(repo_path / "pyproject.toml", 'w') as f:
            f.write("""[tool.pytest.ini_options]
python_files = ["test_*.py"]
pythonpath = ["."]
""")
        
        return repo_path
    
    def generate_unfixable_repo(self) -> Path:
        """Generate repository with unfixable bug (test expectation is wrong)."""
        repo_path = self.base_path / "unfixable_bug"
        if repo_path.exists():
            shutil.rmtree(repo_path)
        repo_path.mkdir()
        
        src_path = repo_path / "src"
        src_path.mkdir()
        with open(src_path / "__init__.py", 'w') as f:
            f.write("")
        with open(src_path / "solver.py", 'w') as f:
            f.write("""# Code is actually correct
def get_answer():
    \"\"\"Return the ultimate answer to life, universe, and everything.\"\"\"
    return 42

def calculate_tax(amount, rate=0.10):
    \"\"\"Calculate tax correctly.\"\"\"
    return amount * rate
""")
        
        tests_path = repo_path / "tests"
        tests_path.mkdir()
        with open(tests_path / "__init__.py", 'w') as f:
            f.write("")
        with open(tests_path / "test_solver.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.solver import get_answer, calculate_tax

def test_get_answer():
    # Test expectation is wrong (should be 42)
    assert get_answer() == 43

def test_calculate_tax():
    # Test expectation is wrong (should be 10.0)
    assert calculate_tax(100) == 15.0
""")
        
        with open(repo_path / "pyproject.toml", 'w') as f:
            f.write("""[tool.pytest.ini_options]
python_files = ["test_*.py"]
pythonpath = ["."]
""")
        
        return repo_path
    
    def generate_no_op_patch_repo(self) -> Path:
        """Generate repository with test that always fails (no code fix possible)."""
        repo_path = self.base_path / "no_op_patch"
        if repo_path.exists():
            shutil.rmtree(repo_path)
        repo_path.mkdir()
        
        src_path = repo_path / "src"
        src_path.mkdir()
        with open(src_path / "__init__.py", 'w') as f:
            f.write("")
        with open(src_path / "dummy.py", 'w') as f:
            f.write("""def always_true():
    return True

def always_false():
    return False
""")
        
        tests_path = repo_path / "tests"
        tests_path.mkdir()
        with open(tests_path / "__init__.py", 'w') as f:
            f.write("")
        with open(tests_path / "test_dummy.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_always_fails():
    # This test will always fail regardless of code changes
    assert False, "This test is designed to always fail"

def test_random_failure():
    import random
    # This test randomly fails
    random.seed(42)
    assert random.random() > 0.5, "Random failure"
""")
        
        with open(repo_path / "pyproject.toml", 'w') as f:
            f.write("""[tool.pytest.ini_options]
python_files = ["test_*.py"]
pythonpath = ["."]
""")
        
        return repo_path
    
    def generate_import_issues_repo(self) -> Path:
        """Generate repository with import issues."""
        repo_path = self.base_path / "import_issues"
        if repo_path.exists():
            shutil.rmtree(repo_path)
        repo_path.mkdir()
        
        src_path = repo_path / "src"
        src_path.mkdir()
        with open(src_path / "__init__.py", 'w') as f:
            f.write("")
        with open(src_path / "module_a.py", 'w') as f:
            f.write("""# Bug: circular import when used with module_b
from src.module_b import helper_b

def function_a():
    return "A"

def combined():
    return function_a() + helper_b()
""")
        with open(src_path / "module_b.py", 'w') as f:
            f.write("""# Bug: missing import
def helper_b():
    return function_a() + "B"  # Bug: function_a not imported
""")
        
        tests_path = repo_path / "tests"
        tests_path.mkdir()
        with open(tests_path / "__init__.py", 'w') as f:
            f.write("")
        with open(tests_path / "test_modules.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.module_a import function_a, combined

def test_function_a():
    assert function_a() == "A"

def test_combined():
    assert combined() == "AAB"
""")
        
        with open(repo_path / "pyproject.toml", 'w') as f:
            f.write("""[tool.pytest.ini_options]
python_files = ["test_*.py"]
pythonpath = ["."]
""")
        
        return repo_path
    
    def generate_type_hints_repo(self) -> Path:
        """Generate repository with type hint issues."""
        repo_path = self.base_path / "type_hints"
        if repo_path.exists():
            shutil.rmtree(repo_path)
        repo_path.mkdir()
        
        src_path = repo_path / "src"
        src_path.mkdir()
        with open(src_path / "__init__.py", 'w') as f:
            f.write("")
        with open(src_path / "typed_functions.py", 'w') as f:
            f.write("""from typing import List, Optional

def process_list(items: List[int]) -> int:
    # Bug: returns string instead of int
    return str(sum(items))

def get_item(items: List[str], index: int) -> Optional[str]:
    # Bug: doesn't handle negative indices
    if index >= len(items):
        return None
    return items[index]

def concat_strings(a: str, b: str) -> str:
    # Bug: returns int instead of str
    return len(a) + len(b)
""")
        
        tests_path = repo_path / "tests"
        tests_path.mkdir()
        with open(tests_path / "__init__.py", 'w') as f:
            f.write("")
        with open(tests_path / "test_typed_functions.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.typed_functions import process_list, get_item, concat_strings

def test_process_list():
    result = process_list([1, 2, 3])
    assert result == 6
    assert isinstance(result, int)

def test_get_item():
    items = ["a", "b", "c"]
    assert get_item(items, 0) == "a"
    assert get_item(items, -1) == "c"
    assert get_item(items, 10) is None

def test_concat_strings():
    result = concat_strings("hello", "world")
    assert result == "helloworld"
    assert isinstance(result, str)
""")
        
        with open(repo_path / "pyproject.toml", 'w') as f:
            f.write("""[tool.pytest.ini_options]
python_files = ["test_*.py"]
pythonpath = ["."]
""")
        
        return repo_path
    
    def generate_exception_handling_repo(self) -> Path:
        """Generate repository with exception handling issues."""
        repo_path = self.base_path / "exception_handling"
        if repo_path.exists():
            shutil.rmtree(repo_path)
        repo_path.mkdir()
        
        src_path = repo_path / "src"
        src_path.mkdir()
        with open(src_path / "__init__.py", 'w') as f:
            f.write("")
        with open(src_path / "error_handlers.py", 'w') as f:
            f.write("""def divide_safe(a, b):
    # Bug: catches wrong exception
    try:
        return a / b
    except ValueError:  # Should catch ZeroDivisionError
        return None

def parse_int_safe(s):
    # Bug: doesn't catch exception
    return int(s)

def validate_positive(n):
    # Bug: raises wrong exception
    if n < 0:
        raise TypeError(f"{n} is negative")  # Should be ValueError

def safe_list_access(lst, index):
    # Bug: doesn't handle negative indices correctly
    try:
        return lst[index]
    except IndexError:
        return None  # Negative indices might not raise IndexError
""")
        
        tests_path = repo_path / "tests"
        tests_path.mkdir()
        with open(tests_path / "__init__.py", 'w') as f:
            f.write("")
        with open(tests_path / "test_error_handlers.py", 'w') as f:
            f.write("""import sys
import os
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.error_handlers import divide_safe, parse_int_safe, validate_positive, safe_list_access

def test_divide_safe():
    assert divide_safe(10, 2) == 5
    assert divide_safe(10, 0) is None

def test_parse_int_safe():
    assert parse_int_safe("42") == 42
    result = parse_int_safe("invalid")
    assert result is None or result == 0  # Should handle gracefully

def test_validate_positive():
    validate_positive(5)  # Should not raise
    with pytest.raises(ValueError):
        validate_positive(-5)

def test_safe_list_access():
    lst = [1, 2, 3]
    assert safe_list_access(lst, 0) == 1
    assert safe_list_access(lst, -1) == 3
    assert safe_list_access(lst, 10) is None
""")
        
        with open(repo_path / "pyproject.toml", 'w') as f:
            f.write("""[tool.pytest.ini_options]
python_files = ["test_*.py"]
pythonpath = ["."]
""")
        
        return repo_path

# ============================================================================
# Nova Test Runner
# ============================================================================

class TestMode(Enum):
    """Test execution modes."""
    SINGLE = "single"  # Test single version
    COMPARE = "compare"  # Compare two versions
    EVAL = "eval"  # Use Nova eval mode

class NovaTestRunner:
    """Runs Nova tests and analyzes results."""
    
    def __init__(self, config: Optional[Dict] = None, verbose: bool = False):
        self.config = config or {}
        self.verbose = verbose
        self.results = {}
        
    def run_nova_fix(self, repo_path: Path, nova_cmd: str = "nova",
                     max_iters: Optional[int] = None, timeout: Optional[int] = None,
                     version_label: str = "nova") -> Dict[str, Any]:
        """Run nova fix on a repository and capture results."""
        
        # Build command
        if isinstance(nova_cmd, str) and ' ' in nova_cmd:
            cmd = nova_cmd.split() + ["fix", str(repo_path)]
        else:
            cmd = [nova_cmd, "fix", str(repo_path)]
        
        if max_iters is not None:
            cmd.extend(["--max-iters", str(max_iters)])
        if timeout is not None:
            cmd.extend(["--timeout", str(timeout)])
        if self.verbose:
            cmd.append("--verbose")
        
        # Run Nova
        print(f"{Colors.CYAN}Running {version_label} on {repo_path.name}...{Colors.END}")
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=timeout if timeout else 3600
            )
            elapsed = time.time() - start_time
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "elapsed_time": elapsed,
                "version": version_label
            }
            
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            return {
                "stdout": "",
                "stderr": f"Process timed out after {timeout} seconds",
                "exit_code": -1,
                "elapsed_time": elapsed,
                "version": version_label
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "elapsed_time": 0,
                "version": version_label,
                "error": str(e)
            }
    
    def analyze_nova_output(self, output: Dict, repo_path: Path) -> Dict[str, Any]:
        """Analyze Nova output to extract metrics and determine success."""
        
        metrics = {
            "all_tests_passed": False,
            "iterations": 0,
            "patches_applied": 0,
            "error_type": None,
            "exit_code": output.get("exit_code", -1),
            "elapsed_time": output.get("elapsed_time", 0)
        }
        
        # Determine success from exit code
        if output["exit_code"] == 0:
            metrics["all_tests_passed"] = True
        
        # Analyze output for error conditions
        combined_output = output.get("stdout", "") + output.get("stderr", "")
        out_lower = combined_output.lower()
        
        # Check for specific error types
        if output["exit_code"] == -1 or "timeout" in out_lower:
            metrics["error_type"] = "timeout"
        elif "max iterations reached" in out_lower or "max iteration" in out_lower:
            metrics["error_type"] = "max_iterations"
        elif "patch error" in out_lower or "patch rejected" in out_lower:
            metrics["error_type"] = "patch_failure"
        elif "api key" in out_lower.lower():
            metrics["error_type"] = "no_api_key"
        
        # Extract iteration count
        for line in combined_output.splitlines():
            # Try multiple patterns
            patterns = [
                r'iteration\s+(\d+)',
                r'Iteration\s+(\d+)/',
                r'Iterations completed:\s*(\d+)',
                r'Fixed after\s+(\d+)\s+iteration'
            ]
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    iter_num = int(match.group(1))
                    metrics["iterations"] = max(metrics["iterations"], iter_num)
        
        # Count patches applied
        nova_dir = repo_path / ".nova"
        if nova_dir.exists():
            run_dirs = sorted([d for d in nova_dir.iterdir() if d.is_dir()])
            if run_dirs:
                latest_run = run_dirs[-1]
                diffs_dir = latest_run / "diffs"
                if diffs_dir.exists():
                    patches = list(diffs_dir.glob("*.patch"))
                    metrics["patches_applied"] = len(patches)
        
        # Get test failures before and after
        metrics["initial_failures"] = self._count_test_failures(repo_path, check_initial=True)
        metrics["final_failures"] = self._count_test_failures(repo_path, check_initial=False)
        metrics["tests_fixed"] = max(0, metrics["initial_failures"] - metrics["final_failures"])
        
        return metrics
    
    def _count_test_failures(self, repo_path: Path, check_initial: bool = False) -> int:
        """Count the number of failing tests in a repository."""
        try:
            # Run pytest to count failures
            result = subprocess.run(
                ["python", "-m", "pytest", "--tb=no", "-q"],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout + result.stderr
            
            # Parse pytest output for failure count
            if "failed" in output.lower():
                match = re.search(r'(\d+) failed', output)
                if match:
                    return int(match.group(1))
                return 1  # At least one failure
            
            return 0
            
        except Exception:
            return 0

# ============================================================================
# Unified Test Suite
# ============================================================================

class NovaUnifiedTestSuite:
    """Unified test suite combining all best features."""
    
    def __init__(self, workspace_dir: Optional[Path] = None, 
                 verbose: bool = False,
                 mode: TestMode = TestMode.SINGLE):
        self.workspace_dir = workspace_dir or Path.cwd()
        self.verbose = verbose
        self.mode = mode
        self.test_dir = Path(tempfile.mkdtemp(prefix="nova_test_"))
        self.venv_dir = None
        self.results = []
        self.generator = SyntheticRepoGenerator(self.test_dir / "repos")
        self.runner = NovaTestRunner(verbose=verbose)
        
    def setup_environment(self, skip_venv: bool = False) -> bool:
        """Set up the test environment."""
        print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}{Colors.BOLD}Setting Up Test Environment{Colors.END}")
        print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}\n")
        
        if not skip_venv:
            # Create virtual environment
            self.venv_dir = self.test_dir / "venv"
            print(f"Creating virtual environment at {self.venv_dir}...")
            
            try:
                subprocess.run(
                    [sys.executable, "-m", "venv", str(self.venv_dir)],
                    check=True,
                    capture_output=True
                )
                print(f"{Colors.GREEN}✅ Virtual environment created{Colors.END}")
                
                # Install Nova
                pip_cmd = str(self.venv_dir / "bin" / "pip")
                if sys.platform == "win32":
                    pip_cmd = str(self.venv_dir / "Scripts" / "pip.exe")
                
                print("Installing Nova CI-Rescue...")
                subprocess.run(
                    [pip_cmd, "install", "-e", str(self.workspace_dir)],
                    check=True,
                    capture_output=True
                )
                print(f"{Colors.GREEN}✅ Nova installed{Colors.END}")
                
            except subprocess.CalledProcessError as e:
                print(f"{Colors.RED}❌ Environment setup failed: {e}{Colors.END}")
                return False
        else:
            print(f"{Colors.YELLOW}⚠️  Skipping virtual environment setup{Colors.END}")
        
        return True
    
    def load_test_configuration(self, config_path: Optional[Path] = None) -> List[Dict]:
        """Load test configuration from YAML or use built-in tests."""
        if config_path and config_path.exists():
            print(f"Loading configuration from {config_path}")
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Extract test runs
            if isinstance(config, dict) and 'runs' in config:
                return config['runs']
            elif isinstance(config, list):
                return config
            else:
                print(f"{Colors.YELLOW}Warning: Invalid config format, using built-in tests{Colors.END}")
        
        # Use built-in test repositories
        print("Using built-in test repositories...")
        return self.generator.generate_all()
    
    def run_single_test(self, test_config: Dict, nova_cmd: str = "nova") -> Dict:
        """Run a single test scenario."""
        test_name = test_config.get('name', 'unknown')
        print(f"\n{Colors.YELLOW}Testing: {test_name}{Colors.END}")
        print(f"Description: {test_config.get('description', 'No description')}")
        
        # Prepare repository
        if 'path' in test_config:
            repo_path = Path(test_config['path'])
            if not repo_path.is_absolute():
                repo_path = self.workspace_dir / repo_path
        else:
            # Generate synthetic repo
            repos = self.generator.generate_all()
            matching = [r for r in repos if r['name'] == test_name]
            if matching:
                repo_path = Path(matching[0]['path'])
            else:
                print(f"{Colors.RED}Repository not found: {test_name}{Colors.END}")
                return {"name": test_name, "error": "Repository not found"}
        
        # Copy to temp directory for isolation
        with tempfile.TemporaryDirectory(prefix=f"nova_test_{test_name}_") as tmpdir:
            test_repo = Path(tmpdir) / "repo"
            if repo_path.exists():
                shutil.copytree(repo_path, test_repo)
            else:
                print(f"{Colors.RED}Repository path does not exist: {repo_path}{Colors.END}")
                return {"name": test_name, "error": "Repository path not found"}
            
            # Run Nova
            output = self.runner.run_nova_fix(
                test_repo,
                nova_cmd=nova_cmd,
                max_iters=test_config.get('max_iters', 6),
                timeout=test_config.get('timeout', 600)
            )
            
            # Analyze results
            metrics = self.runner.analyze_nova_output(output, test_repo)
            
            # Add test metadata
            metrics.update({
                "name": test_name,
                "description": test_config.get('description', ''),
                "difficulty": test_config.get('difficulty', 'unknown'),
                "expected_failures": test_config.get('expected_failures', 0)
            })
            
            # Print result
            if metrics["all_tests_passed"]:
                print(f"{Colors.GREEN}✅ Success! Fixed {metrics['tests_fixed']} tests in {metrics['iterations']} iterations ({metrics['elapsed_time']:.1f}s){Colors.END}")
            else:
                error_msg = metrics.get('error_type', 'unknown error')
                print(f"{Colors.RED}❌ Failed: {error_msg}. Fixed {metrics['tests_fixed']} tests.{Colors.END}")
            
            return metrics
    
    def run_comparison_test(self, test_config: Dict, 
                           nova_v1_cmd: str, nova_v2_cmd: str) -> Dict:
        """Run comparison test between two Nova versions."""
        test_name = test_config.get('name', 'unknown')
        
        print(f"\n{Colors.YELLOW}Comparison Test: {test_name}{Colors.END}")
        
        # Run v1
        print(f"{Colors.CYAN}Running v1.0...{Colors.END}")
        v1_result = self.run_single_test(test_config, nova_cmd=nova_v1_cmd)
        
        # Run v2
        print(f"{Colors.CYAN}Running v1.1...{Colors.END}")
        v2_result = self.run_single_test(test_config, nova_cmd=nova_v2_cmd)
        
        # Compare results
        comparison = {
            "name": test_name,
            "v1_0": v1_result,
            "v1_1": v2_result,
            "regression": False,
            "improvement": False
        }
        
        # Determine outcome
        if v2_result.get("all_tests_passed") and not v1_result.get("all_tests_passed"):
            comparison["improvement"] = True
            comparison["outcome"] = "v1_1_better"
        elif v1_result.get("all_tests_passed") and not v2_result.get("all_tests_passed"):
            comparison["regression"] = True
            comparison["outcome"] = "v1_0_better"
        elif v1_result.get("all_tests_passed") and v2_result.get("all_tests_passed"):
            # Both passed, compare efficiency
            if v2_result.get("iterations", 0) < v1_result.get("iterations", 0):
                comparison["outcome"] = "v1_1_more_efficient"
            elif v2_result.get("iterations", 0) > v1_result.get("iterations", 0):
                comparison["outcome"] = "v1_0_more_efficient"
            else:
                comparison["outcome"] = "equal"
        else:
            comparison["outcome"] = "both_failed"
        
        return comparison
    
    def print_results_table(self, results: List[Dict]):
        """Print results in a professional table format."""
        if not results:
            print("No results to display")
            return
        
        print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}Test Results Summary{Colors.END}")
        print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")
        
        # Determine if this is comparison mode
        is_comparison = 'v1_0' in results[0] if results else False
        
        if is_comparison:
            # Comparison table
            headers = ["Test", "v1.0", "v1.1", "Outcome", "Time (v1.0/v1.1)"]
            col_widths = [20, 10, 10, 20, 15]
            
            # Header row
            header_line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
            print(header_line)
            print("-" * len(header_line))
            
            # Data rows
            for res in results:
                v1 = res.get('v1_0', {})
                v2 = res.get('v1_1', {})
                
                row = [
                    res['name'][:20],
                    "✅" if v1.get('all_tests_passed') else "❌",
                    "✅" if v2.get('all_tests_passed') else "❌",
                    res.get('outcome', 'unknown'),
                    f"{v1.get('elapsed_time', 0):.1f}s/{v2.get('elapsed_time', 0):.1f}s"
                ]
                
                print(" | ".join(str(r).ljust(w) for r, w in zip(row, col_widths)))
        else:
            # Single version table
            headers = ["Repository", "Status", "Fixed", "Iterations", "Time", "Notes"]
            
            # Calculate column widths
            col_widths = [len(h) for h in headers]
            for res in results:
                col_widths[0] = max(col_widths[0], len(res.get("name", "")))
                col_widths[2] = max(col_widths[2], len(f"{res.get('tests_fixed', 0)}/{res.get('initial_failures', 0)}"))
            
            # Header row
            header_line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
            print(header_line)
            print("-" * len(header_line))
            
            # Data rows
            for res in results:
                status = "✅ Passed" if res.get("all_tests_passed") else "❌ Failed"
                fixed = f"{res.get('tests_fixed', 0)}/{res.get('initial_failures', 0)}"
                iterations = str(res.get("iterations", 0))
                time_str = f"{res.get('elapsed_time', 0):.1f}s"
                notes = res.get("error_type", "") if not res.get("all_tests_passed") else ""
                
                row = [res.get("name", ""), status, fixed, iterations, time_str, notes]
                print(" | ".join(str(r).ljust(w) for r, w in zip(row, col_widths)))
        
        # Summary statistics
        print(f"\n{Colors.BOLD}Summary Statistics:{Colors.END}")
        
        if is_comparison:
            total = len(results)
            improvements = sum(1 for r in results if r.get('improvement'))
            regressions = sum(1 for r in results if r.get('regression'))
            
            print(f"Total Tests: {total}")
            print(f"Improvements: {Colors.GREEN}{improvements}{Colors.END}")
            print(f"Regressions: {Colors.RED}{regressions}{Colors.END}")
            print(f"No Change: {total - improvements - regressions}")
        else:
            total = len(results)
            passed = sum(1 for r in results if r.get("all_tests_passed"))
            total_fixed = sum(r.get("tests_fixed", 0) for r in results)
            total_failures = sum(r.get("initial_failures", 0) for r in results)
            
            success_rate = (passed / total * 100) if total > 0 else 0
            fix_rate = (total_fixed / total_failures * 100) if total_failures > 0 else 0
            
            print(f"Total Scenarios: {total}")
            print(f"Successful: {Colors.GREEN}{passed}{Colors.END} ({success_rate:.1f}%)")
            print(f"Tests Fixed: {total_fixed}/{total_failures} ({fix_rate:.1f}%)")
            
            if success_rate >= 70:
                print(f"\n{Colors.GREEN}✅ Success criteria met! ({success_rate:.1f}% >= 70%){Colors.END}")
            else:
                print(f"\n{Colors.RED}❌ Below success threshold ({success_rate:.1f}% < 70%){Colors.END}")
    
    def save_results(self, output_dir: Path, results: List[Dict]):
        """Save results to JSON and Markdown files."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON
        json_file = output_dir / "results.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Results saved to {json_file}")
        
        # Generate Markdown report
        md_file = output_dir / "report.md"
        self._generate_markdown_report(md_file, results)
        print(f"Report saved to {md_file}")
    
    def _generate_markdown_report(self, output_file: Path, results: List[Dict]):
        """Generate a Markdown report of the test results."""
        lines = []
        lines.append("# Nova CI-Rescue Test Report")
        lines.append(f"\n**Date:** {datetime.now().isoformat()}")
        lines.append(f"**Mode:** {self.mode.value}")
        lines.append(f"**Total Tests:** {len(results)}")
        
        # Check if comparison mode
        is_comparison = 'v1_0' in results[0] if results else False
        
        if is_comparison:
            lines.append("\n## Version Comparison Results")
            lines.append("\n| Test | v1.0 | v1.1 | Outcome |")
            lines.append("|------|------|------|---------|")
            
            for res in results:
                v1_status = "✅" if res['v1_0'].get('all_tests_passed') else "❌"
                v2_status = "✅" if res['v1_1'].get('all_tests_passed') else "❌"
                lines.append(f"| {res['name']} | {v1_status} | {v2_status} | {res.get('outcome', '')} |")
        else:
            lines.append("\n## Test Results")
            lines.append("\n| Test | Status | Tests Fixed | Iterations | Time | Error |")
            lines.append("|------|--------|-------------|------------|------|-------|")
            
            for res in results:
                status = "✅" if res.get('all_tests_passed') else "❌"
                fixed = f"{res.get('tests_fixed', 0)}/{res.get('initial_failures', 0)}"
                iterations = res.get('iterations', 0)
                time_str = f"{res.get('elapsed_time', 0):.1f}s"
                error = res.get('error_type', '') if not res.get('all_tests_passed') else ''
                
                lines.append(f"| {res.get('name', '')} | {status} | {fixed} | {iterations} | {time_str} | {error} |")
        
        # Summary
        lines.append("\n## Summary")
        
        if is_comparison:
            improvements = sum(1 for r in results if r.get('improvement'))
            regressions = sum(1 for r in results if r.get('regression'))
            lines.append(f"- **Improvements:** {improvements}")
            lines.append(f"- **Regressions:** {regressions}")
            
            if regressions > 0:
                lines.append("\n### ⚠️ Regressions Detected")
                for res in results:
                    if res.get('regression'):
                        lines.append(f"- {res['name']}")
        else:
            passed = sum(1 for r in results if r.get('all_tests_passed'))
            success_rate = (passed / len(results) * 100) if results else 0
            
            lines.append(f"- **Success Rate:** {success_rate:.1f}%")
            lines.append(f"- **Tests Passed:** {passed}/{len(results)}")
            
            if success_rate >= 70:
                lines.append("\n✅ **Success criteria met!**")
            else:
                lines.append("\n❌ **Below success threshold**")
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(lines))
    
    def cleanup(self):
        """Clean up temporary files."""
        if self.test_dir and self.test_dir.exists():
            print(f"\nCleaning up {self.test_dir}...")
            shutil.rmtree(self.test_dir)
            print(f"{Colors.GREEN}✅ Cleanup complete{Colors.END}")

# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point for the unified test suite."""
    parser = argparse.ArgumentParser(
        description="Nova CI-Rescue Unified Test Suite - Best of All Worlds",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with built-in tests
  %(prog)s
  
  # Generate test repos and run
  %(prog)s --generate
  
  # Use YAML configuration
  %(prog)s --config test_repos.yaml
  
  # Compare two versions
  %(prog)s --compare --v1-cmd "./nova_v1_0" --v2-cmd "./nova_v1_1"
  
  # Save results
  %(prog)s --json-out results.json --md-out report.md
        """
    )
    
    # Test configuration
    parser.add_argument(
        "-c", "--config",
        type=Path,
        help="YAML configuration file for test repositories"
    )
    parser.add_argument(
        "-g", "--generate",
        action="store_true",
        help="Generate synthetic test repositories before running"
    )
    
    # Execution modes
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare two Nova versions"
    )
    parser.add_argument(
        "--nova-cmd",
        default="nova",
        help="Nova command to use (default: nova)"
    )
    parser.add_argument(
        "--v1-cmd",
        default="nova",
        help="Nova v1 command for comparison mode"
    )
    parser.add_argument(
        "--v2-cmd",
        default="nova",
        help="Nova v2 command for comparison mode"
    )
    
    # Output options
    parser.add_argument(
        "-j", "--json-out",
        type=Path,
        help="Save JSON results to file"
    )
    parser.add_argument(
        "-m", "--md-out",
        type=Path,
        help="Save Markdown report to file"
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("nova_test_results"),
        help="Output directory for all results"
    )
    
    # Execution options
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--skip-venv",
        action="store_true",
        help="Skip virtual environment creation"
    )
    parser.add_argument(
        "--keep-files",
        action="store_true",
        help="Keep temporary test files after completion"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Default timeout for each test in seconds"
    )
    parser.add_argument(
        "--max-iters",
        type=int,
        default=6,
        help="Default maximum iterations for Nova"
    )
    
    args = parser.parse_args()
    
    # Disable colors if requested or not in TTY
    if args.no_color or not sys.stdout.isatty():
        Colors.disable()
    
    # Print header
    print(f"{Colors.GREEN}{Colors.BOLD}")
    print("=" * 80)
    print("Nova CI-Rescue Unified Test Suite".center(80))
    print("Best of All Worlds Edition".center(80))
    print("=" * 80)
    print(f"{Colors.END}")
    
    # Determine test mode
    if args.compare:
        mode = TestMode.COMPARE
    else:
        mode = TestMode.SINGLE
    
    # Create test suite
    suite = NovaUnifiedTestSuite(
        workspace_dir=Path.cwd(),
        verbose=args.verbose,
        mode=mode
    )
    
    try:
        # Setup environment
        if not suite.setup_environment(skip_venv=args.skip_venv):
            print(f"{Colors.RED}Failed to setup environment{Colors.END}")
            sys.exit(1)
        
        # Generate repos if requested
        if args.generate:
            print(f"\n{Colors.CYAN}Generating synthetic test repositories...{Colors.END}")
            repos = suite.generator.generate_all()
            print(f"{Colors.GREEN}✅ Generated {len(repos)} test repositories{Colors.END}")
        
        # Load test configuration
        test_configs = suite.load_test_configuration(args.config)
        
        # Apply default timeout and max_iters if not specified
        for config in test_configs:
            if 'timeout' not in config:
                config['timeout'] = args.timeout
            if 'max_iters' not in config:
                config['max_iters'] = args.max_iters
        
        # Run tests
        results = []
        
        if mode == TestMode.COMPARE:
            # Comparison mode
            print(f"\n{Colors.BOLD}Running comparison tests...{Colors.END}")
            for config in test_configs:
                result = suite.run_comparison_test(
                    config,
                    nova_v1_cmd=args.v1_cmd,
                    nova_v2_cmd=args.v2_cmd
                )
                results.append(result)
        else:
            # Single version mode
            print(f"\n{Colors.BOLD}Running tests...{Colors.END}")
            for config in test_configs:
                result = suite.run_single_test(config, nova_cmd=args.nova_cmd)
                results.append(result)
        
        # Print results table
        suite.print_results_table(results)
        
        # Save results if requested
        if args.json_out or args.md_out:
            output_dir = args.output_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if args.json_out:
                with open(args.json_out, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                print(f"\n{Colors.GREEN}JSON results saved to {args.json_out}{Colors.END}")
            
            if args.md_out:
                suite._generate_markdown_report(args.md_out, results)
                print(f"{Colors.GREEN}Markdown report saved to {args.md_out}{Colors.END}")
        else:
            # Save to default location
            suite.save_results(args.output_dir, results)
        
        # Determine exit code
        if mode == TestMode.COMPARE:
            # Exit with error if regressions found
            regressions = sum(1 for r in results if r.get('regression'))
            if regressions > 0:
                print(f"\n{Colors.RED}⚠️  {regressions} regression(s) detected!{Colors.END}")
                sys.exit(1)
        else:
            # Exit with error if success rate < 70%
            passed = sum(1 for r in results if r.get('all_tests_passed'))
            success_rate = (passed / len(results) * 100) if results else 0
            if success_rate < 70:
                print(f"\n{Colors.RED}Below success threshold: {success_rate:.1f}% < 70%{Colors.END}")
                sys.exit(1)
        
        print(f"\n{Colors.GREEN}✅ All tests completed successfully!{Colors.END}")
        sys.exit(0)
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test suite interrupted by user{Colors.END}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.END}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)
    finally:
        if not args.keep_files:
            suite.cleanup()

if __name__ == "__main__":
    main()
