"""Tests for math operations - all will fail due to bugs."""

import pytest
from math_ops import (
    add, subtract, multiply, divide, power, 
    factorial, fibonacci, is_prime, gcd, average
)

def test_addition():
    """Test addition function."""
    assert add(2, 3) == 5
    assert add(0, 0) == 0
    assert add(-1, 1) == 0
    assert add(10, -5) == 5

def test_subtraction():
    """Test subtraction function."""
    assert subtract(5, 3) == 2
    assert subtract(0, 0) == 0
    assert subtract(-1, -1) == 0
    assert subtract(10, 15) == -5

def test_multiplication():
    """Test multiplication function."""
    assert multiply(3, 4) == 12
    assert multiply(0, 5) == 0
    assert multiply(-2, 3) == -6
    assert multiply(-2, -3) == 6

def test_division():
    """Test division function."""
    assert divide(10, 2) == 5
    assert divide(7, 2) == 3.5
    assert divide(-6, 3) == -2
    
def test_division_by_zero():
    """Test division by zero handling."""
    with pytest.raises(ZeroDivisionError):
        divide(5, 0)

def test_power():
    """Test power function."""
    assert power(2, 3) == 8
    assert power(5, 0) == 1
    assert power(10, 2) == 100
    assert power(3, -1) == 1/3

def test_factorial():
    """Test factorial function."""
    assert factorial(0) == 1
    assert factorial(1) == 1
    assert factorial(5) == 120
    assert factorial(6) == 720

def test_fibonacci():
    """Test Fibonacci function."""
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    assert fibonacci(2) == 1
    assert fibonacci(5) == 5
    assert fibonacci(10) == 55

def test_is_prime():
    """Test prime number checker."""
    assert is_prime(2) == True
    assert is_prime(3) == True
    assert is_prime(4) == False
    assert is_prime(17) == True
    assert is_prime(100) == False

def test_gcd():
    """Test greatest common divisor."""
    assert gcd(48, 18) == 6
    assert gcd(12, 8) == 4
    assert gcd(17, 19) == 1
    assert gcd(100, 50) == 50

def test_average():
    """Test average calculation."""
    assert average([1, 2, 3, 4, 5]) == 3.0
    assert average([10, 20]) == 15.0
    assert average([1, 1, 1, 1]) == 1.0
    assert average([2, 4, 6, 8]) == 5.0
