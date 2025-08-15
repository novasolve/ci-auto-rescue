"""
Test suite for the calculator module.
These tests will initially fail due to the buggy implementations in calculator.py.
Nova CI-Rescue should be able to fix the bugs automatically.
"""
import pytest
import sys
from pathlib import Path

# Add src directory to Python path to import the calculator module
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculator import add, subtract, multiply, divide

def test_addition():
    """Test the add function (expected correct addition)."""
    assert add(2, 3) == 5       # This will fail (2 - 3 != 5)
    assert add(10, -5) == 5     # This will fail (10 - (-5) != 5)
    assert add(0, 0) == 0       # This will pass (0 - 0 == 0)

def test_subtraction():
    """Test the subtract function (expected a - b)."""
    assert subtract(5, 3) == 2    # This will fail (5 - 3 - 1 != 2)
    assert subtract(0, 5) == -5   # This will fail (0 - 5 - 1 != -5)
    assert subtract(-2, -3) == 1  # This will fail (-2 - -3 - 1 != 1)

def test_multiplication():
    """Test the multiply function (expected a * b)."""
    assert multiply(3, 4) == 12   # This will fail (3 + 4 != 12)
    assert multiply(5, 0) == 0    # This will fail (5 + 0 != 0)
    assert multiply(-2, 3) == -6  # This will fail (-2 + 3 != -6)

def test_division():
    """Test the divide function (expected float division)."""
    assert divide(10, 2) == 5.0   # This will fail (10 // 2 == 5, not 5.0)
    assert divide(7, 2) == 3.5    # This will fail (7 // 2 == 3, not 3.5)
    assert divide(9, 3) == 3.0    # This will fail (9 // 3 == 3, not 3.0)

def test_division_by_zero():
    """Test that dividing by zero raises a ValueError."""
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)  # This should pass once the bug is fixed (currently raises ZeroDivisionError)
