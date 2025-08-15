"""
Test file for mathematical operations - contains intentional failures for Nova to fix.
"""

def test_basic_arithmetic():
def test_basic_arithmetic():
    numbers = [1, 2, 3, 4, 5]
    result = sum_numbers(numbers)
    assert result == 15

def test_division():
    result = divide(10, 3)
    assert abs(result - 3.333333333333333) < 1e-9
    """Test division operations."""
    # Bug: integer division instead of float
    result = 10 // 3  # Should be / for float division
    assert result == 3.333333333333333
