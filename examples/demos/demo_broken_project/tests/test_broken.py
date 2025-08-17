"""
Tests for the broken implementation (these will fail).
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from broken import (
    divide_numbers, find_max, concatenate_strings,
    calculate_average, get_first_char, sort_list
)


def test_divide_numbers_normal():
    """Test normal division."""
    assert divide_numbers(10, 2) == 5.0
    assert divide_numbers(7, 3) == 7/3


def test_divide_numbers_by_zero():
    """Test division by zero (will fail)."""
    with pytest.raises(ValueError):
        divide_numbers(10, 0)  # This will crash


def test_find_max_normal():
    """Test finding max in normal list."""
    assert find_max([1, 5, 3, 9, 2]) == 9
    assert find_max([42]) == 42


def test_find_max_empty():
    """Test finding max in empty list (will fail)."""
    with pytest.raises(ValueError):
        find_max([])  # This will crash


def test_concatenate_strings():
    """Test string concatenation (will fail due to missing space)."""
    result = concatenate_strings("Hello", "World")
    assert result == "Hello World"  # Will fail: gets "HelloWorld"


def test_calculate_average():
    """Test average calculation (will fail due to integer division)."""
    result = calculate_average([1, 2, 3, 4])
    assert result == 2.5  # Will fail: gets 2 due to integer division


def test_get_first_char_normal():
    """Test getting first character."""
    assert get_first_char("Hello") == "H"
    assert get_first_char("A") == "A"


def test_get_first_char_empty():
    """Test getting first char of empty string (will fail)."""
    assert get_first_char("") == ""  # This will crash


def test_sort_list():
    """Test list sorting (will fail due to mutation)."""
    original = [3, 1, 4, 1, 5]
    sorted_list = sort_list(original)
    assert sorted_list == [1, 1, 3, 4, 5]
    assert original == [3, 1, 4, 1, 5]  # Will fail: original is modified
