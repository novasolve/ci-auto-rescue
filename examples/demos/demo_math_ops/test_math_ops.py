"""
Test file for mathematical operations - tests expect correct results.
"""

from math_ops import sum_numbers, divide

def test_basic_arithmetic():
    """Test basic arithmetic operations."""
    numbers = [1, 2, 3, 4, 5]
    result = sum_numbers(numbers)
    assert result == 15

def test_division():
    """Test division operations."""
    result = 10 / 3
    assert abs(result - 3.333333333333333) < 1e-9

def test_divide_function():
    """Test the divide function directly."""
    result = divide(10, 3)
    assert abs(result - 3.333333333333333) < 1e-9