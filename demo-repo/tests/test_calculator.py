"""
Test suite for the calculator module.
These tests will fail initially due to intentional bugs in the calculator module.
"""

import pytest
import sys
import os

# Add parent directory to path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.calculator import Calculator, fibonacci, is_prime, gcd


class TestCalculator:
    """Test cases for Calculator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calc = Calculator()
    
    def test_add(self):
        """Test addition operation."""
        assert self.calc.add(2, 3) == 5
        assert self.calc.add(-1, 1) == 0
        assert self.calc.add(0, 0) == 0
        assert self.calc.add(10, -5) == 5
    
    def test_subtract(self):
        """Test subtraction operation."""
        # This will fail due to bug: subtract uses + instead of -
        assert self.calc.subtract(5, 3) == 2
        assert self.calc.subtract(0, 0) == 0
        assert self.calc.subtract(-5, -3) == -2
        assert self.calc.subtract(10, 15) == -5
    
    def test_multiply(self):
        """Test multiplication operation."""
        assert self.calc.multiply(3, 4) == 12
        assert self.calc.multiply(0, 5) == 0
        assert self.calc.multiply(-2, 3) == -6
        assert self.calc.multiply(-2, -3) == 6
    
    def test_divide(self):
        """Test division operation."""
        assert self.calc.divide(10, 2) == 5
        assert self.calc.divide(7, 2) == 3.5
        assert self.calc.divide(-10, 2) == -5
        
    def test_divide_by_zero(self):
        """Test division by zero raises exception."""
        # This will fail due to missing zero check
        with pytest.raises(ZeroDivisionError):
            self.calc.divide(5, 0)
    
    def test_power(self):
        """Test power operation."""
        # This will fail due to bug: power uses * instead of **
        assert self.calc.power(2, 3) == 8
        assert self.calc.power(5, 2) == 25
        assert self.calc.power(10, 0) == 1
        assert self.calc.power(2, -1) == 0.5
    
    def test_square_root(self):
        """Test square root operation."""
        assert self.calc.square_root(4) == 2
        assert self.calc.square_root(9) == 3
        assert self.calc.square_root(0) == 0
        assert abs(self.calc.square_root(2) - 1.414213) < 0.001
    
    def test_square_root_negative(self):
        """Test square root of negative number."""
        # This will fail due to missing negative number handling
        with pytest.raises(ValueError):
            self.calc.square_root(-4)
    
    def test_factorial(self):
        """Test factorial operation."""
        # This will fail due to off-by-one error
        assert self.calc.factorial(0) == 1
        assert self.calc.factorial(1) == 1
        assert self.calc.factorial(5) == 120
        assert self.calc.factorial(6) == 720
    
    def test_factorial_negative(self):
        """Test factorial of negative number raises exception."""
        with pytest.raises(ValueError):
            self.calc.factorial(-1)
    
    def test_history(self):
        """Test calculation history tracking."""
        self.calc.add(2, 3)
        self.calc.multiply(4, 5)
        history = self.calc.get_history()
        assert len(history) == 2
        assert "2 + 3 = 5" in history
        assert "4 * 5 = 20" in history
    
    def test_clear_history(self):
        """Test clearing calculation history."""
        self.calc.add(1, 1)
        self.calc.clear_history()
        assert len(self.calc.get_history()) == 0


class TestUtilityFunctions:
    """Test cases for utility functions."""
    
    def test_fibonacci(self):
        """Test Fibonacci number generation."""
        # This will fail due to wrong initial values
        assert fibonacci(1) == 1
        assert fibonacci(2) == 1
        assert fibonacci(3) == 2
        assert fibonacci(4) == 3
        assert fibonacci(5) == 5
        assert fibonacci(6) == 8
        assert fibonacci(10) == 55
    
    def test_fibonacci_edge_cases(self):
        """Test Fibonacci edge cases."""
        assert fibonacci(0) == 0
        assert fibonacci(-1) == 0
    
    def test_is_prime(self):
        """Test prime number checker."""
        # Basic prime tests
        assert is_prime(2) == True
        assert is_prime(3) == True
        assert is_prime(5) == True
        assert is_prime(7) == True
        assert is_prime(11) == True
        assert is_prime(13) == True
        
        # Non-prime tests
        assert is_prime(1) == False
        assert is_prime(4) == False
        assert is_prime(6) == False
        assert is_prime(8) == False
        assert is_prime(9) == False
        assert is_prime(10) == False
        
        # Edge cases
        assert is_prime(0) == False
        assert is_prime(-5) == False
    
    def test_gcd(self):
        """Test greatest common divisor."""
        assert gcd(12, 8) == 4
        assert gcd(14, 21) == 7
        assert gcd(17, 19) == 1
        assert gcd(100, 50) == 50
        assert gcd(0, 5) == 5
        assert gcd(5, 0) == 5


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
