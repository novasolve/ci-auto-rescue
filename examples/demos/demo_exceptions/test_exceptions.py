"""Tests for exception handling - all will fail due to bugs."""

import pytest
import json
from exceptions import (
    divide_numbers, get_list_item, convert_to_int, access_dict_key,
    open_and_read, parse_json, recursive_function, validate_age,
    process_data, safe_divide, get_nested_value, calculate_percentage,
    custom_exception_handler, cleanup_resources
)

def test_divide_by_zero():
    """Test division by zero handling."""
    assert divide_numbers(10, 2) == 5
    # Should return None or raise a custom exception
    assert divide_numbers(10, 0) is None

def test_list_index_error():
    """Test list index error handling."""
    lst = [1, 2, 3]
    assert get_list_item(lst, 1) == 2
    # Should return None or default value
    assert get_list_item(lst, 10) is None

def test_value_conversion_error():
    """Test value conversion error handling."""
    assert convert_to_int("123") == 123
    # Should return None or default value
    assert convert_to_int("abc") is None
    assert convert_to_int("12.34") is None

def test_dict_key_error():
    """Test dictionary key error handling."""
    data = {"name": "John", "age": 30}
    assert access_dict_key(data, "name") == "John"
    # Should return None or default value
    assert access_dict_key(data, "email") is None

def test_file_not_found():
    """Test file not found error handling."""
    # Should return None or empty string
    assert open_and_read("nonexistent_file.txt") is None

def test_json_decode_error():
    """Test JSON decode error handling."""
    assert parse_json('{"key": "value"}') == {"key": "value"}
    # Should return None or empty dict
    assert parse_json("invalid json") is None

def test_recursive_limit():
    """Test recursion limit handling."""
    assert recursive_function(5) == 120  # 5!
    # Should handle properly without stack overflow
    with pytest.raises(RecursionError):
        recursive_function(1000)

def test_validate_age():
    """Test age validation."""
    assert validate_age(25) == True
    
    # Should raise ValueError with message
    with pytest.raises(ValueError, match="Age cannot be negative"):
        validate_age(-5)
    
    # Should raise ValueError for too high age
    with pytest.raises(ValueError, match="Age cannot exceed 150"):
        validate_age(200)

def test_process_data():
    """Test data processing with correct exception."""
    assert process_data("hello") == "HELLO"
    # Should handle AttributeError for non-string
    assert process_data(123) == "Error processing data"
    assert process_data(None) == "Error processing data"

def test_safe_divide():
    """Test safe division with specific exception."""
    assert safe_divide(10, 2) == 5
    assert safe_divide(10, 0) == 0  # Should handle ZeroDivisionError
    # Should not catch other exceptions
    with pytest.raises(TypeError):
        safe_divide("10", 2)

def test_get_nested_value():
    """Test nested dictionary access."""
    data = {
        "user": {
            "profile": {
                "name": "John"
            }
        }
    }
    
    assert get_nested_value(data, ["user", "profile", "name"]) == "John"
    # Should return None for missing keys
    assert get_nested_value(data, ["user", "email"]) is None
    assert get_nested_value(data, ["admin", "profile"]) is None

def test_calculate_percentage():
    """Test percentage calculation."""
    assert calculate_percentage(25, 100) == 25.0
    # Should handle division by zero
    assert calculate_percentage(10, 0) == 0
    # Should handle type errors
    assert calculate_percentage("10", 100) == 10.0

def test_custom_exception():
    """Test custom exception with message."""
    with pytest.raises(Exception, match="Custom error occurred"):
        custom_exception_handler()

class MockResource:
    """Mock resource for testing cleanup."""
    def __init__(self):
        self.opened = False
        self.closed = False
        self.should_fail = False
    
    def open(self):
        self.opened = True
    
    def process(self):
        if self.should_fail:
            raise RuntimeError("Processing failed")
        return "data"
    
    def close(self):
        self.closed = True

def test_cleanup_resources():
    """Test resource cleanup."""
    # Success case
    resource = MockResource()
    result = cleanup_resources(resource)
    assert result == "data"
    assert resource.closed == True
    
    # Failure case - should still close
    resource = MockResource()
    resource.should_fail = True
    with pytest.raises(RuntimeError):
        cleanup_resources(resource)
    assert resource.closed == True  # Should be closed even on error
