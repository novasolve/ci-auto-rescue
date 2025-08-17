"""
Test file for mathematical operations - contains intentional failures for Nova to fix.
"""

from math_ops import sum_numbers, divide

def test_basic_arithmetic():
    """Test basic arithmetic operations."""
    numbers = [1, 2, 3, 4, 5]
    result = sum_numbers(numbers)
    # Bug: Wrong expected value (should be 15)
    assert result == 10

def test_division():
    """Test division operations."""
    # Bug: integer division instead of float
    result = 10 // 3  # Should be / for float division
    assert result == 3.333333333333333

def test_divide_function():
    """Test the divide function directly."""
    result = divide(10, 3)
    # Bug: Wrong expected value (too strict equality check)
    assert result == 3.0  # Should be approximately 3.333...