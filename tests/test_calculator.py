"""
Comprehensive test suite for the calculator module.
These tests will pass initially, fail after "bad PR", and be fixed by Nova.
"""

import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculator import Calculator


class TestCalculator:
    """Test suite for Calculator class."""

    @pytest.fixture
    def calc(self):
        """Provide a Calculator instance for tests."""
        return Calculator()

    def test_addition(self, calc):
        """Test addition operation."""
        assert calc.add(2, 3) == 5
        assert calc.add(-1, 1) == 0
        assert calc.add(0, 0) == 0
        assert calc.add(1.5, 2.5) == 4.0

    def test_subtraction(self, calc):
        """Test subtraction operation."""
        assert calc.subtract(5, 3) == 2
        assert calc.subtract(0, 5) == -5
        assert calc.subtract(-3, -3) == 0
        assert calc.subtract(10.5, 0.5) == 10.0

    def test_multiplication(self, calc):
        """Test multiplication operation."""
        assert calc.multiply(3, 4) == 12
        assert calc.multiply(-2, 3) == -6
        assert calc.multiply(0, 100) == 0
        assert calc.multiply(2.5, 4) == 10.0

    def test_division(self, calc):
        """Test division operation."""
        assert calc.divide(10, 2) == 5
        assert calc.divide(7, 2) == 3.5
        assert calc.divide(-10, 2) == -5
        assert calc.divide(1, 3) == pytest.approx(0.3333, rel=1e-3)

    def test_division_by_zero(self, calc):
        """Test division by zero raises error."""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calc.divide(10, 0)

    def test_power(self, calc):
        """Test power operation."""
        assert calc.power(2, 3) == 8
        assert calc.power(5, 0) == 1
        assert calc.power(10, -1) == 0.1
        assert calc.power(3, 2) == 9

    def test_square_root(self, calc):
        """Test square root operation."""
        assert calc.square_root(9) == 3
        assert calc.square_root(16) == 4
        assert calc.square_root(2) == pytest.approx(1.4142, rel=1e-3)
        assert calc.square_root(0) == 0

    def test_square_root_negative(self, calc):
        """Test square root of negative number raises error."""
        with pytest.raises(
            ValueError, match="Cannot calculate square root of negative number"
        ):
            calc.square_root(-4)

    def test_percentage(self, calc):
        """Test percentage calculation."""
        assert calc.percentage(100, 25) == 25
        assert calc.percentage(50, 50) == 25
        assert calc.percentage(200, 10) == 20
        assert calc.percentage(0, 50) == 0

    def test_average(self, calc):
        """Test average calculation."""
        assert calc.average([1, 2, 3, 4, 5]) == 3
        assert calc.average([10]) == 10
        assert calc.average([0, 0, 0]) == 0
        assert calc.average([1.5, 2.5, 3.5]) == 2.5


class TestEdgeCases:
    """Additional edge case tests."""

    @pytest.fixture
    def calc(self):
        return Calculator()

    def test_large_numbers(self, calc):
        """Test operations with large numbers."""
        large = 1e10
        assert calc.add(large, large) == 2 * large
        assert calc.multiply(large, 0) == 0

    def test_precision(self, calc):
        """Test floating point precision."""
        result = calc.add(0.1, 0.2)
        assert result == pytest.approx(0.3, rel=1e-9)

    def test_negative_scenarios(self, calc):
        """Test various negative number scenarios."""
        assert calc.multiply(-1, -1) == 1
        assert calc.divide(-10, -2) == 5
        assert calc.subtract(-5, -10) == 5
