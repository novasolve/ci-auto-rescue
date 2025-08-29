"""Tests for the broken calculator - all will fail."""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from calculator import Calculator

class TestCalculator:
    """Test the Calculator class."""

    @pytest.fixture
    def calc(self):
        """Create a calculator instance."""
        return Calculator()

    def test_add(self, calc):
        """Test addition."""
        assert calc.add(2, 3) == 5
        assert calc.add(0, 0) == 0
        assert calc.add(-1, 1) == 0
        assert calc.add(10, -5) == 5

    def test_subtract(self, calc):
        """Test subtraction."""
        assert calc.subtract(5, 3) == 2
        assert calc.subtract(0, 0) == 0
        assert calc.subtract(10, 15) == -5
        assert calc.subtract(-5, -3) == -2

    def test_multiply(self, calc):
        """Test multiplication."""
        assert calc.multiply(3, 4) == 12
        assert calc.multiply(0, 5) == 0
        assert calc.multiply(-2, 3) == -6
        assert calc.multiply(-2, -3) == 6

    def test_divide(self, calc):
        """Test division."""
        assert calc.divide(10, 2) == 5
        assert calc.divide(7, 2) == 3.5
        assert calc.divide(-6, 3) == -2

    def test_divide_by_zero(self, calc):
        """Test division by zero handling."""
        assert calc.divide(5, 0) is None  # Should return None, not raise

    def test_power(self, calc):
        """Test power function."""
        assert calc.power(2, 3) == 8
        assert calc.power(5, 0) == 1
        assert calc.power(10, 2) == 100
        assert calc.power(3, -1) == 1/3

    def test_square_root(self, calc):
        """Test square root."""
        assert calc.square_root(4) == 2
        assert calc.square_root(9) == 3
        assert calc.square_root(16) == 4
        assert abs(calc.square_root(2) - 1.414) < 0.01

    def test_percentage(self, calc):
        """Test percentage calculation."""
        assert calc.percentage(100, 25) == 25
        assert calc.percentage(50, 10) == 5
        assert calc.percentage(200, 50) == 100

    def test_memory_operations(self, calc):
        """Test memory store and recall."""
        calc.store_memory(42)
        assert calc.recall_memory() == 42

        calc.store_memory(100)
        assert calc.recall_memory() == 100

        calc.clear_memory()
        assert calc.recall_memory() == 0

    def test_factorial(self, calc):
        """Test factorial calculation."""
        assert calc.factorial(0) == 1
        assert calc.factorial(1) == 1
        assert calc.factorial(5) == 120
        assert calc.factorial(6) == 720

    def test_is_even(self, calc):
        """Test even number check."""
        assert calc.is_even(2) == True
        assert calc.is_even(3) == False
        assert calc.is_even(0) == True
        assert calc.is_even(-4) == True
        assert calc.is_even(-3) == False

    def test_absolute(self, calc):
        """Test absolute value."""
        assert calc.absolute(5) == 5
        assert calc.absolute(-5) == 5
        assert calc.absolute(0) == 0
        assert calc.absolute(-100) == 100

    def test_average(self, calc):
        """Test average calculation."""
        assert calc.average([1, 2, 3, 4, 5]) == 3.0
        assert calc.average([10, 20]) == 15.0
        assert calc.average([5]) == 5.0
        assert calc.average([2, 4, 6, 8]) == 5.0
        assert calc.average([]) is None
