#!/usr/bin/env python3
"""
Edge Case Test Repository Generator for Nova CI-Rescue Regression Tests
Creates test repositories with specific scenarios to test edge cases
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
import json
import time


class EdgeCaseGenerator:
    """Generate test repositories for specific edge case scenarios"""
    
    def __init__(self, base_path: str = "./test_repos"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    def generate_all_edge_cases(self):
        """Generate all edge case test repositories"""
        print("Generating edge case test repositories...")
        
        # Generate each edge case
        self.generate_no_failures_repo()
        self.generate_patch_conflict_repo()
        self.generate_max_iterations_repo()
        self.generate_timeout_repo()
        self.generate_one_line_fix_repo()
        self.generate_multi_file_fix_repo()
        self.generate_refactor_repo()
        
        # Generate real-world-like repos
        self.generate_simple_math_repo()
        self.generate_string_ops_repo()
        self.generate_file_parser_repo()
        self.generate_import_issues_repo()
        self.generate_type_hints_repo()
        self.generate_exception_handling_repo()
        
        print("All edge case repositories generated successfully!")
        
    def generate_no_failures_repo(self):
        """Generate repository with all tests passing"""
        repo_path = self.base_path / "all_passing"
        repo_path.mkdir(exist_ok=True)
        
        # Create source file
        src_path = repo_path / "src"
        src_path.mkdir(exist_ok=True)
        
        with open(src_path / "calculator.py", 'w') as f:
            f.write("""def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
""")
        
        # Create test file with all passing tests
        tests_path = repo_path / "tests"
        tests_path.mkdir(exist_ok=True)
        
        with open(tests_path / "test_calculator.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from calculator import add, subtract, multiply, divide
import pytest

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    
def test_subtract():
    assert subtract(5, 3) == 2
    assert subtract(0, 5) == -5
    
def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(-2, 3) == -6
    
def test_divide():
    assert divide(10, 2) == 5
    assert divide(7, 2) == 3.5
    
def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)
""")
        
        # Create pyproject.toml
        with open(repo_path / "pyproject.toml", 'w') as f:
            f.write("""[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
""")
        
        print(f"✅ Generated no-failures repository at {repo_path}")
        
    def generate_patch_conflict_repo(self):
        """Generate repository designed to cause patch conflicts"""
        repo_path = self.base_path / "patch_conflict"
        repo_path.mkdir(exist_ok=True)
        
        # Create source file with specific formatting
        src_path = repo_path / "src"
        src_path.mkdir(exist_ok=True)
        
        with open(src_path / "data_processor.py", 'w') as f:
            f.write("""# Data Processor Module
# This file has specific formatting that might cause patch conflicts

def process_data(data):
    # This function has a bug
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)  # Bug: should be item * 3
    return result

def validate_data(data):
    # This function is correct
    if not isinstance(data, list):
        raise TypeError("Data must be a list")
    for item in data:
        if not isinstance(item, (int, float)):
            raise TypeError("All items must be numeric")
    return True

def transform_data(data):
    # Another function with a bug
    validated = validate_data(data)
    if validated:
        processed = process_data(data)
        # Bug: should filter out values > 100
        return processed
    return []
""")
        
        # Create test file
        tests_path = repo_path / "tests"
        tests_path.mkdir(exist_ok=True)
        
        with open(tests_path / "test_processor.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_processor import process_data, validate_data, transform_data
import pytest

def test_process_data():
    # This test will fail due to the bug
    assert process_data([1, 2, 3]) == [3, 6, 9]  # Expects multiplication by 3
    assert process_data([-1, 0, 1]) == [3]
    
def test_transform_data():
    # This test will fail due to missing filtering
    data = [10, 50, 150, 200]
    result = transform_data(data)
    assert all(x <= 100 for x in result), "Should filter out values > 100"
""")
        
        # Create script to simulate conflict
        scripts_path = repo_path.parent.parent / "scripts"
        scripts_path.mkdir(exist_ok=True)
        
        with open(scripts_path / "setup_patch_conflict.sh", 'w') as f:
            f.write("""#!/bin/bash
# Script to set up patch conflict scenario
# This modifies the file during test run to cause conflicts

sleep 2  # Wait for Nova to start
echo "# Modified by conflict script" >> src/data_processor.py
""")
        os.chmod(scripts_path / "setup_patch_conflict.sh", 0o755)
        
        print(f"✅ Generated patch-conflict repository at {repo_path}")
        
    def generate_max_iterations_repo(self):
        """Generate repository requiring many iterations to fix"""
        repo_path = self.base_path / "complex_refactor"
        repo_path.mkdir(exist_ok=True)
        
        # Create interconnected source files with multiple bugs
        src_path = repo_path / "src"
        src_path.mkdir(exist_ok=True)
        
        # File 1: Core module with bugs
        with open(src_path / "core.py", 'w') as f:
            f.write("""class DataManager:
    def __init__(self):
        self.data = []
        self.validators = []  # Bug: should be a dict
        
    def add_validator(self, name, func):
        # Bug: treating list as dict
        self.validators[name] = func
        
    def validate(self, item):
        # Bug: iterating over list incorrectly
        for name, validator in self.validators.items():
            if not validator(item):
                return False
        return True
        
    def process(self, items):
        # Bug: wrong variable name
        valid_items = []
        for item in items:
            if self.validate(item):
                valid_item.append(item)  # Bug: should be valid_items
        return valid_items
""")
        
        # File 2: Utils with dependent bugs
        with open(src_path / "utils.py", 'w') as f:
            f.write("""from core import DataManager

def create_manager():
    manager = DataManager()
    # Bug: method doesn't exist yet
    manager.set_default_validators()
    return manager

def process_batch(data_batch):
    manager = create_manager()
    results = []
    for data in data_batch:
        # Bug: wrong method name
        result = manager.proces(data)  # Should be process
        results.extend(result)
    return results
""")
        
        # File 3: Extended functionality
        with open(src_path / "extended.py", 'w') as f:
            f.write("""from core import DataManager
from utils import create_manager

class ExtendedManager(DataManager):
    def __init__(self):
        super().__init__()
        self.cache = {}
        
    def process_with_cache(self, items):
        # Bug: cache key generation is wrong
        cache_key = str(item)  # Bug: should be str(items)
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        result = self.process(items)
        self.cache[cache_key] = result
        return result
        
    def set_default_validators(self):
        # This method is missing in parent class
        self.add_validator('positive', lambda x: x > 0)
        self.add_validator('max_100', lambda x: x <= 100)
""")
        
        # Create complex test file
        tests_path = repo_path / "tests"
        tests_path.mkdir(exist_ok=True)
        
        with open(tests_path / "test_complex.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core import DataManager
from utils import create_manager, process_batch
from extended import ExtendedManager
import pytest

def test_data_manager():
    manager = DataManager()
    manager.add_validator('positive', lambda x: x > 0)
    assert manager.validate(5) == True
    assert manager.validate(-1) == False
    
def test_process():
    manager = DataManager()
    manager.add_validator('positive', lambda x: x > 0)
    result = manager.process([1, -1, 2, -2, 3])
    assert result == [1, 2, 3]
    
def test_extended_manager():
    manager = ExtendedManager()
    manager.set_default_validators()
    result = manager.process_with_cache([10, 150, 50, -10])
    assert result == [10, 50]
    
def test_batch_processing():
    data_batches = [[1, 2, 3], [4, 5, 6], [-1, 0, 1]]
    result = process_batch(data_batches)
    assert len(result) > 0
""")
        
        print(f"✅ Generated max-iterations repository at {repo_path}")
        
    def generate_timeout_repo(self):
        """Generate repository with slow/hanging tests"""
        repo_path = self.base_path / "slow_tests"
        repo_path.mkdir(exist_ok=True)
        
        # Create source file with slow operations
        src_path = repo_path / "src"
        src_path.mkdir(exist_ok=True)
        
        with open(src_path / "slow_ops.py", 'w') as f:
            f.write("""import time

def slow_fibonacci(n):
    # Intentionally inefficient implementation
    if n <= 1:
        return n
    return slow_fibonacci(n-1) + slow_fibonacci(n-2)

def process_large_data(data):
    # Bug: infinite loop condition
    result = []
    i = 0
    while i < len(data):
        time.sleep(0.1)  # Simulate slow processing
        result.append(data[i] * 2)
        # Bug: forgot to increment i (causes infinite loop)
    return result

def timeout_operation(timeout_seconds):
    # This will definitely timeout
    time.sleep(timeout_seconds * 2)
    return "completed"
""")
        
        # Create test file with slow tests
        tests_path = repo_path / "tests"
        tests_path.mkdir(exist_ok=True)
        
        with open(tests_path / "test_slow.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from slow_ops import slow_fibonacci, process_large_data, timeout_operation
import pytest

def test_fibonacci():
    # This will be slow but should pass if the bug is fixed
    assert slow_fibonacci(5) == 5
    assert slow_fibonacci(10) == 55
    
def test_process_data():
    # This will timeout due to infinite loop bug
    result = process_large_data([1, 2, 3])
    assert result == [2, 4, 6]
    
def test_timeout():
    # This is designed to timeout
    result = timeout_operation(30)
    assert result == "completed"
""")
        
        print(f"✅ Generated timeout repository at {repo_path}")
        
    def generate_one_line_fix_repo(self):
        """Generate repository needing just a one-line fix"""
        repo_path = self.base_path / "one_line_fix"
        repo_path.mkdir(exist_ok=True)
        
        # Create source file with single bug
        src_path = repo_path / "src"
        src_path.mkdir(exist_ok=True)
        
        with open(src_path / "simple_calc.py", 'w') as f:
            f.write("""def calculate_average(numbers):
    if not numbers:
        return 0
    total = sum(numbers)
    # Bug: off-by-one error in denominator
    return total / (len(numbers) - 1)  # Should be len(numbers)

def find_max(numbers):
    if not numbers:
        return None
    return max(numbers)

def find_min(numbers):
    if not numbers:
        return None
    return min(numbers)
""")
        
        # Create test file
        tests_path = repo_path / "tests"
        tests_path.mkdir(exist_ok=True)
        
        with open(tests_path / "test_simple.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from simple_calc import calculate_average, find_max, find_min
import pytest

def test_calculate_average():
    assert calculate_average([1, 2, 3, 4, 5]) == 3.0
    assert calculate_average([10, 20]) == 15.0
    assert calculate_average([5]) == 5.0
    assert calculate_average([]) == 0
    
def test_find_max():
    assert find_max([1, 5, 3, 9, 2]) == 9
    assert find_max([-1, -5, -3]) == -1
    
def test_find_min():
    assert find_min([1, 5, 3, 9, 2]) == 1
    assert find_min([-1, -5, -3]) == -5
""")
        
        print(f"✅ Generated one-line-fix repository at {repo_path}")
        
    def generate_multi_file_fix_repo(self):
        """Generate repository requiring fixes across multiple files"""
        repo_path = self.base_path / "multi_file_fix"
        repo_path.mkdir(exist_ok=True)
        
        # Create interconnected source files
        src_path = repo_path / "src"
        src_path.mkdir(exist_ok=True)
        
        # File 1: Models
        with open(src_path / "models.py", 'w') as f:
            f.write("""class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age
        
    def can_vote(self):
        # Bug: wrong age threshold
        return self.age >= 21  # Should be 18
        
class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price
        
    def apply_discount(self, percentage):
        # Bug: wrong calculation
        discount = self.price * percentage  # Should be percentage / 100
        return self.price - discount
""")
        
        # File 2: Services
        with open(src_path / "services.py", 'w') as f:
            f.write("""from models import User, Product

class UserService:
    def __init__(self):
        self.users = []
        
    def add_user(self, name, age):
        # Bug: wrong parameter order
        user = User(age, name)  # Should be (name, age)
        self.users.append(user)
        return user
        
    def get_voters(self):
        return [u for u in self.users if u.can_vote()]
        
class ProductService:
    def __init__(self):
        self.products = []
        
    def add_product(self, name, price):
        product = Product(name, price)
        self.products.append(product)
        return product
        
    def apply_sale(self, discount_percentage):
        # Bug: passing percentage incorrectly
        return [p.apply_discount(discount_percentage / 100) for p in self.products]  # Should just pass discount_percentage
""")
        
        # File 3: Main app
        with open(src_path / "app.py", 'w') as f:
            f.write("""from services import UserService, ProductService

def create_sample_data():
    user_service = UserService()
    product_service = ProductService()
    
    # Add users
    user_service.add_user("Alice", 25)
    user_service.add_user("Bob", 17)
    user_service.add_user("Charlie", 18)
    
    # Add products
    product_service.add_product("Laptop", 1000)
    product_service.add_product("Mouse", 50)
    
    return user_service, product_service

def get_voting_stats(user_service):
    voters = user_service.get_voters()
    total = len(user_service.users)
    # Bug: division by zero not handled
    percentage = len(voters) / total * 100
    return percentage
""")
        
        # Create test file
        tests_path = repo_path / "tests"
        tests_path.mkdir(exist_ok=True)
        
        with open(tests_path / "test_multi.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models import User, Product
from services import UserService, ProductService
from app import create_sample_data, get_voting_stats
import pytest

def test_user_voting_age():
    user1 = User("Alice", 17)
    user2 = User("Bob", 18)
    user3 = User("Charlie", 25)
    
    assert user1.can_vote() == False
    assert user2.can_vote() == True
    assert user3.can_vote() == True
    
def test_product_discount():
    product = Product("Laptop", 1000)
    discounted_price = product.apply_discount(10)  # 10% discount
    assert discounted_price == 900
    
def test_user_service():
    service = UserService()
    user = service.add_user("John", 30)
    assert user.name == "John"
    assert user.age == 30
    
def test_product_service():
    service = ProductService()
    service.add_product("Item1", 100)
    service.add_product("Item2", 200)
    
    sale_prices = service.apply_sale(20)  # 20% off
    assert sale_prices[0] == 80
    assert sale_prices[1] == 160
    
def test_voting_stats():
    user_service, _ = create_sample_data()
    percentage = get_voting_stats(user_service)
    assert percentage == 66.66666666666666  # 2 out of 3 users can vote (18+)
""")
        
        print(f"✅ Generated multi-file-fix repository at {repo_path}")
        
    def generate_refactor_repo(self):
        """Generate repository needing major refactoring"""
        repo_path = self.base_path / "needs_refactor"
        repo_path.mkdir(exist_ok=True)
        
        # Create source file needing significant refactoring
        src_path = repo_path / "src"
        src_path.mkdir(exist_ok=True)
        
        with open(src_path / "legacy_code.py", 'w') as f:
            f.write("""# Legacy code that needs refactoring to fix tests

# Global state (bad practice)
global_cache = {}
global_counter = 0

def process_item(item):
    # Multiple issues: global state, no error handling, wrong logic
    global global_counter
    global_counter += 1
    
    # Bug: using global cache incorrectly
    if item in global_cache:
        return global_cache[item]
    
    # Complex processing with bugs
    if isinstance(item, str):
        result = item.upper()
    elif isinstance(item, int):
        result = item ** 2  # Bug: should be item * 2
    elif isinstance(item, list):
        # Bug: not handling nested lists properly
        result = [process_item(x) for x in item]
    else:
        result = str(item)
    
    # Bug: cache not being updated
    # global_cache[item] = result
    
    return result

class DataProcessor:
    # This class needs refactoring to fix the tests
    
    def __init__(self):
        # Bug: shared mutable default
        self.data = []  # This should be None and initialized properly
        self.processors = {}
        
    def add_processor(self, type_name, func):
        # Bug: not checking if type_name already exists
        self.processors[type_name] = func
        
    def process(self, items, type_name):
        # Multiple bugs here
        if type_name not in self.processors:
            # Bug: should raise an exception or return None
            return items
            
        processor = self.processors[type_name]
        
        # Bug: not handling exceptions
        results = []
        for item in items:
            result = processor(item)
            results.append(result)
            
        # Bug: modifying internal state incorrectly
        self.data = results  # Should extend, not replace
        
        return results
        
    def get_processed_data(self):
        # Bug: returning mutable internal state
        return self.data  # Should return a copy

def create_processor_chain(*processors):
    # This function needs complete refactoring
    # Bug: chain doesn't work as expected
    def chained(item):
        result = item
        for proc in processors:
            result = proc(item)  # Bug: should pass result, not item
        return result
    return chained
""")
        
        # Create test file
        tests_path = repo_path / "tests"
        tests_path.mkdir(exist_ok=True)
        
        with open(tests_path / "test_refactor.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from legacy_code import process_item, DataProcessor, create_processor_chain
import pytest

def test_process_item_string():
    # Reset global state (this is why globals are bad)
    import legacy_code
    legacy_code.global_cache.clear()
    legacy_code.global_counter = 0
    
    assert process_item("hello") == "HELLO"
    assert process_item("world") == "WORLD"
    
def test_process_item_integer():
    assert process_item(5) == 10  # Should be multiplication by 2
    assert process_item(3) == 6
    
def test_process_item_caching():
    import legacy_code
    legacy_code.global_cache.clear()
    
    # First call
    result1 = process_item("test")
    # Second call should use cache
    result2 = process_item("test")
    
    assert result1 == result2
    assert "test" in legacy_code.global_cache
    
def test_data_processor():
    processor = DataProcessor()
    
    processor.add_processor("double", lambda x: x * 2)
    processor.add_processor("square", lambda x: x ** 2)
    
    result1 = processor.process([1, 2, 3], "double")
    assert result1 == [2, 4, 6]
    
    result2 = processor.process([1, 2, 3], "square")
    assert result2 == [1, 4, 9]
    
    # Test that data is accumulated, not replaced
    all_data = processor.get_processed_data()
    assert len(all_data) == 6  # Should have all results
    
def test_processor_chain():
    double = lambda x: x * 2
    add_ten = lambda x: x + 10
    
    chain = create_processor_chain(double, add_ten)
    
    assert chain(5) == 20  # (5 * 2) + 10
    assert chain(3) == 16  # (3 * 2) + 10
    
def test_data_processor_immutability():
    processor = DataProcessor()
    processor.add_processor("double", lambda x: x * 2)
    processor.process([1, 2, 3], "double")
    
    data1 = processor.get_processed_data()
    data1.append(999)  # Modify returned data
    
    data2 = processor.get_processed_data()
    assert 999 not in data2  # Internal data should not be affected
""")
        
        print(f"✅ Generated refactor repository at {repo_path}")
        
    def generate_simple_math_repo(self):
        """Generate simple math repository with basic failures"""
        repo_path = self.base_path / "simple_math"
        repo_path.mkdir(exist_ok=True)
        
        # Create source file
        src_path = repo_path / "src"
        src_path.mkdir(exist_ok=True)
        
        with open(src_path / "math_ops.py", 'w') as f:
            f.write("""def factorial(n):
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n == 0:
        return 1
    result = 1
    for i in range(1, n):  # Bug: should be range(1, n+1)
        result *= i
    return result

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, n):
        if n % i == 0:
            return True  # Bug: should return False
    return True  # Bug: logic is inverted

def gcd(a, b):
    # Bug: doesn't handle negative numbers correctly
    while b:
        a, b = b, a % b
    return a
""")
        
        # Create test file
        tests_path = repo_path / "tests"
        tests_path.mkdir(exist_ok=True)
        
        with open(tests_path / "test_math.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from math_ops import factorial, is_prime, gcd
import pytest

def test_factorial():
    assert factorial(0) == 1
    assert factorial(1) == 1
    assert factorial(5) == 120
    assert factorial(10) == 3628800
    
def test_is_prime():
    assert is_prime(2) == True
    assert is_prime(3) == True
    assert is_prime(4) == False
    assert is_prime(17) == True
    assert is_prime(100) == False
""")
        
        print(f"✅ Generated simple-math repository at {repo_path}")
        
    def generate_string_ops_repo(self):
        """Generate string operations repository"""
        repo_path = self.base_path / "string_ops"
        repo_path.mkdir(exist_ok=True)
        
        # Create source file
        src_path = repo_path / "src"
        src_path.mkdir(exist_ok=True)
        
        with open(src_path / "string_utils.py", 'w') as f:
            f.write("""def reverse_string(s):
    # Bug: doesn't handle Unicode properly
    return s[::-2]  # Bug: should be [::-1]

def count_vowels(s):
    vowels = 'aeiouAEIOU'
    count = 0
    for char in s:
        if char in vowels:
            count += 2  # Bug: should increment by 1
    return count

def remove_duplicates(s):
    # Bug: doesn't preserve order
    return ''.join(set(s))  # set() doesn't preserve order

def is_palindrome(s):
    # Bug: doesn't handle case and spaces
    return s == s[::-1]
""")
        
        # Create test file
        tests_path = repo_path / "tests"
        tests_path.mkdir(exist_ok=True)
        
        with open(tests_path / "test_strings.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from string_utils import reverse_string, count_vowels, remove_duplicates, is_palindrome
import pytest

def test_reverse_string():
    assert reverse_string("hello") == "olleh"
    assert reverse_string("Python") == "nohtyP"
    assert reverse_string("") == ""
    
def test_count_vowels():
    assert count_vowels("hello") == 2
    assert count_vowels("Python") == 1
    assert count_vowels("aeiou") == 5
    assert count_vowels("xyz") == 0
    
def test_remove_duplicates():
    assert remove_duplicates("hello") == "helo"
    assert remove_duplicates("aabbcc") == "abc"
    # Order should be preserved
    assert remove_duplicates("abcabc") == "abc"
""")
        
        print(f"✅ Generated string-ops repository at {repo_path}")
        
    def generate_file_parser_repo(self):
        """Generate file parser repository"""
        repo_path = self.base_path / "file_parser"
        repo_path.mkdir(exist_ok=True)
        
        # Create source file
        src_path = repo_path / "src"
        src_path.mkdir(exist_ok=True)
        
        with open(src_path / "parser.py", 'w') as f:
            f.write("""import json
import csv

def parse_json(file_path):
    # Bug: doesn't handle file not found
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def parse_csv(file_path):
    # Bug: doesn't return proper list of dicts
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        return list(reader)  # Should use DictReader

def parse_config(file_path):
    # Bug: doesn't handle comments properly
    config = {}
    with open(file_path, 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.split('=')  # Bug: doesn't strip whitespace
                config[key] = value
    return config

def count_lines(file_path):
    # Bug: counts empty lines
    with open(file_path, 'r') as f:
        return len(f.readlines())  # Should filter empty lines
""")
        
        # Create test file
        tests_path = repo_path / "tests"
        tests_path.mkdir(exist_ok=True)
        
        with open(tests_path / "test_parser.py", 'w') as f:
            f.write("""import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parser import parse_json, parse_csv, parse_config, count_lines
import pytest
import json

def test_parse_json():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"key": "value", "number": 42}, f)
        temp_path = f.name
    
    try:
        data = parse_json(temp_path)
        assert data["key"] == "value"
        assert data["number"] == 42
    finally:
        os.unlink(temp_path)
    
def test_parse_csv():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("name,age\\n")
        f.write("Alice,30\\n")
        f.write("Bob,25\\n")
        temp_path = f.name
    
    try:
        data = parse_csv(temp_path)
        # Should return list of dicts, not list of lists
        assert isinstance(data[0], dict)
        assert data[0]["name"] == "Alice"
        assert data[0]["age"] == "30"
    finally:
        os.unlink(temp_path)
        
def test_parse_config():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
        f.write("key1 = value1\\n")
        f.write("key2 = value2\\n")
        f.write("# This is a comment\\n")
        f.write("key3 = value3\\n")
        temp_path = f.name
    
    try:
        config = parse_config(temp_path)
        assert config["key1"] == "value1"  # Should strip whitespace
        assert config["key2"] == "value2"
        assert "# This is a comment" not in config
    finally:
        os.unlink(temp_path)
        
def test_count_lines():
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Line 1\\n")
        f.write("\\n")  # Empty line
        f.write("Line 3\\n")
        f.write("\\n")  # Empty line
        f.write("Line 5\\n")
        temp_path = f.name
    
    try:
        count = count_lines(temp_path)
        assert count == 3  # Should only count non-empty lines
    finally:
        os.unlink(temp_path)
""")
        
        print(f"✅ Generated file-parser repository at {repo_path}")
        
    def generate_import_issues_repo(self):
        """Generate repository with import issues"""
        repo_path = self.base_path / "import_issues"
        repo_path.mkdir(exist_ok=True)
        
        # Create package structure with import problems
        src_path = repo_path / "src"
        src_path.mkdir(exist_ok=True)
        
        # Create __init__.py with wrong imports
        with open(src_path / "__init__.py", 'w') as f:
            f.write("""# Bug: circular import
from .module_a import function_a
from .module_b import function_b
""")
        
        # Module A
        with open(src_path / "module_a.py", 'w') as f:
            f.write("""# Bug: importing from wrong module
from .module_b import helper_b  # Creates circular dependency

def function_a(x):
    return helper_b(x) * 2

def helper_a(x):
    return x + 1
""")
        
        # Module B
        with open(src_path / "module_b.py", 'w') as f:
            f.write("""# Bug: importing from wrong module
from .module_a import helper_a  # Creates circular dependency

def function_b(x):
    return helper_a(x) * 3

def helper_b(x):
    return x - 1
""")
        
        # Module C (standalone with missing import)
        with open(src_path / "module_c.py", 'w') as f:
            f.write("""# Bug: missing import
def process_data(data):
    # Bug: using math.sqrt without importing math
    return [sqrt(x) for x in data]  # NameError: sqrt not defined
""")
        
        # Create test file
        tests_path = repo_path / "tests"
        tests_path.mkdir(exist_ok=True)
        
        with open(tests_path / "test_imports.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest

def test_function_a():
    from src.module_a import function_a
    assert function_a(5) == 8  # (5-1)*2
    
def test_function_b():
    from src.module_b import function_b
    assert function_b(5) == 18  # (5+1)*3
    
def test_module_c():
    from src.module_c import process_data
    import math
    result = process_data([4, 9, 16])
    assert result == [2.0, 3.0, 4.0]
""")
        
        print(f"✅ Generated import-issues repository at {repo_path}")
        
    def generate_type_hints_repo(self):
        """Generate repository with type hint issues"""
        repo_path = self.base_path / "type_hints"
        repo_path.mkdir(exist_ok=True)
        
        # Create source file with type hint issues
        src_path = repo_path / "src"
        src_path.mkdir(exist_ok=True)
        
        with open(src_path / "typed_functions.py", 'w') as f:
            f.write("""from typing import List, Dict, Optional, Union

def add_numbers(a: int, b: int) -> int:
    # Bug: returns float for division
    return (a + b) / 2  # Should return (a + b) or use // for int division

def process_list(items: List[int]) -> List[str]:
    # Bug: returns List[int] not List[str]
    return [x * 2 for x in items]  # Should convert to strings

def get_value(data: Dict[str, int], key: str) -> Optional[int]:
    # Bug: doesn't handle missing key properly
    return data[key]  # Should use data.get(key)

def combine_values(x: Union[int, str], y: Union[int, str]) -> str:
    # Bug: doesn't handle all type combinations
    return x + y  # Will fail if types don't match
""")
        
        # Create test file
        tests_path = repo_path / "tests"
        tests_path.mkdir(exist_ok=True)
        
        with open(tests_path / "test_types.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from typed_functions import add_numbers, process_list, get_value, combine_values
import pytest

def test_add_numbers():
    result = add_numbers(5, 3)
    assert isinstance(result, int)
    assert result == 8
    
def test_process_list():
    result = process_list([1, 2, 3])
    assert isinstance(result, list)
    assert all(isinstance(x, str) for x in result)
    assert result == ["2", "4", "6"]
    
def test_get_value():
    data = {"a": 1, "b": 2}
    assert get_value(data, "a") == 1
    assert get_value(data, "c") is None  # Should return None for missing key
    
def test_combine_values():
    assert combine_values(5, 3) == "53"
    assert combine_values("hello", "world") == "helloworld"
    assert combine_values(5, "test") == "5test"
""")
        
        print(f"✅ Generated type-hints repository at {repo_path}")
        
    def generate_exception_handling_repo(self):
        """Generate repository with exception handling issues"""
        repo_path = self.base_path / "exceptions"
        repo_path.mkdir(exist_ok=True)
        
        # Create source file with exception handling issues
        src_path = repo_path / "src"
        src_path.mkdir(exist_ok=True)
        
        with open(src_path / "error_handler.py", 'w') as f:
            f.write("""class CustomError(Exception):
    pass

def divide_numbers(a, b):
    # Bug: doesn't raise proper exception
    if b == 0:
        return None  # Should raise ZeroDivisionError or custom exception
    return a / b

def parse_number(s):
    # Bug: doesn't handle ValueError properly
    return int(s)  # Should catch and re-raise or handle

def validate_input(data):
    # Bug: raises wrong exception type
    if not isinstance(data, dict):
        raise ValueError("Input must be a dict")  # Should be TypeError
    if "required_field" not in data:
        raise Exception("Missing field")  # Should be KeyError or custom
    return True

def safe_operation(func, *args):
    # Bug: catches too broad exception
    try:
        return func(*args)
    except:  # Should catch specific exceptions
        return None
""")
        
        # Create test file
        tests_path = repo_path / "tests"
        tests_path.mkdir(exist_ok=True)
        
        with open(tests_path / "test_exceptions.py", 'w') as f:
            f.write("""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from error_handler import CustomError, divide_numbers, parse_number, validate_input, safe_operation
import pytest

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide_numbers(10, 0)
        
def test_parse_invalid_number():
    with pytest.raises(ValueError) as exc_info:
        parse_number("not a number")
    assert "invalid literal" in str(exc_info.value).lower()
    
def test_validate_input_type():
    with pytest.raises(TypeError) as exc_info:
        validate_input("not a dict")
    assert "must be a dict" in str(exc_info.value)
    
def test_validate_missing_field():
    with pytest.raises(KeyError) as exc_info:
        validate_input({"other_field": "value"})
    assert "required_field" in str(exc_info.value)
    
def test_safe_operation():
    def risky_func(x):
        if x < 0:
            raise ValueError("Negative not allowed")
        return x * 2
    
    assert safe_operation(risky_func, 5) == 10
    # Should handle the specific error, not swallow all exceptions
    with pytest.raises(ValueError):
        safe_operation(risky_func, -1)
""")
        
        print(f"✅ Generated exception-handling repository at {repo_path}")


def main():
    """Main function to generate all test repositories"""
    generator = EdgeCaseGenerator()
    generator.generate_all_edge_cases()
    
    print("\n" + "=" * 60)
    print("All test repositories generated successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review the generated repositories in ./test_repos/")
    print("2. Adjust test_repos.yaml if needed")
    print("3. Run the regression tests with:")
    print("   python regression_orchestrator.py test_repos.yaml")


if __name__ == "__main__":
    main()
