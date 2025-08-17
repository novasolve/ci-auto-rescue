"""
Tests for the fixed implementation (these should pass).
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fixed import (
    divide_numbers, find_max, concatenate_strings,
    calculate_average, get_first_char, sort_list
)


def test_divide_numbers_normal():
    """Test normal division."""
    assert divide_numbers(10, 2) == 5.0
    assert divide_numbers(7, 3) == 7/3


def test_divide_numbers_by_zero():
    """Test division by zero handling."""
    with pytest.raises(ValueError) as exc_info:
        divide_numbers(10, 0)
    assert "Cannot divide by zero" in str(exc_info.value)


def test_find_max_normal():
    """Test finding max in normal list."""
    assert find_max([1, 5, 3, 9, 2]) == 9
    assert find_max([42]) == 42
    assert find_max([-5, -2, -10]) == -2


def test_find_max_empty():
    """Test finding max in empty list."""
    with pytest.raises(ValueError) as exc_info:
        find_max([])
    assert "Cannot find max of empty list" in str(exc_info.value)


def test_concatenate_strings():
    """Test string concatenation with default separator."""
    assert concatenate_strings("Hello", "World") == "Hello World"
    assert concatenate_strings("Python", "Programming") == "Python Programming"


def test_concatenate_strings_custom_separator():
    """Test string concatenation with custom separator."""
    assert concatenate_strings("Hello", "World", "-") == "Hello-World"
    assert concatenate_strings("A", "B", "") == "AB"


def test_calculate_average():
    """Test average calculation."""
    assert calculate_average([1, 2, 3, 4]) == 2.5
    assert calculate_average([5]) == 5.0
    assert calculate_average([1.5, 2.5, 3.5]) == 2.5


def test_calculate_average_empty():
    """Test average of empty list."""
    assert calculate_average([]) == 0.0


def test_get_first_char_normal():
    """Test getting first character."""
    assert get_first_char("Hello") == "H"
    assert get_first_char("A") == "A"
    assert get_first_char("123") == "1"


def test_get_first_char_empty():
    """Test getting first char of empty string."""
    assert get_first_char("") == ""


def test_sort_list():
    """Test list sorting without mutation."""
    original = [3, 1, 4, 1, 5]
    sorted_list = sort_list(original)
    
    # Check sorted result
    assert sorted_list == [1, 1, 3, 4, 5]
    
    # Check original is unchanged
    assert original == [3, 1, 4, 1, 5]


def test_sort_list_strings():
    """Test sorting string list."""
    fruits = ["banana", "apple", "cherry"]
    sorted_fruits = sort_list(fruits)
    assert sorted_fruits == ["apple", "banana", "cherry"]
    assert fruits == ["banana", "apple", "cherry"]  # Original unchanged
