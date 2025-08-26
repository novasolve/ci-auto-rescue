"""Tests for imports - all will fail due to bugs."""

import pytest
from imports import (
    get_current_time, parse_json_data, calculate_square_root,
    get_random_number, join_path, compile_regex, get_system_info,
    encode_base64, sleep_seconds, format_decimal, process_data,
    create_dataframe, create_counter, safe_import_function
)

def test_get_current_time():
    """Test getting current time."""
    result = get_current_time()
    assert result is not None
    assert hasattr(result, 'year')
    assert hasattr(result, 'month')
    assert hasattr(result, 'day')

def test_parse_json_data():
    """Test JSON parsing."""
    json_string = '{"name": "test", "value": 42}'
    result = parse_json_data(json_string)
    assert isinstance(result, dict)
    assert result["name"] == "test"
    assert result["value"] == 42

def test_calculate_square_root():
    """Test square root calculation."""
    assert calculate_square_root(4) == 2.0
    assert calculate_square_root(9) == 3.0
    assert abs(calculate_square_root(2) - 1.414) < 0.001

def test_get_random_number():
    """Test random number generation."""
    result = get_random_number()
    assert isinstance(result, int)
    assert 1 <= result <= 100

def test_join_path():
    """Test path joining."""
    result = join_path("/home", "user", "documents")
    assert "home" in result
    assert "user" in result
    assert "documents" in result

def test_compile_regex():
    """Test regex compilation."""
    pattern = r'\d+'
    regex = compile_regex(pattern)
    assert regex.match("123") is not None
    assert regex.match("abc") is None

def test_get_system_info():
    """Test system info retrieval."""
    info = get_system_info()
    assert isinstance(info, dict)
    assert "platform" in info
    assert "version" in info
    assert isinstance(info["platform"], str)

def test_encode_base64():
    """Test base64 encoding."""
    result = encode_base64("Hello, World!")
    assert isinstance(result, str)
    assert result == "SGVsbG8sIFdvcmxkIQ=="

def test_sleep_seconds():
    """Test sleep function."""
    import time
    start = time.time()
    sleep_seconds(0.1)
    elapsed = time.time() - start
    assert elapsed >= 0.1

def test_format_decimal():
    """Test decimal formatting."""
    result = format_decimal(3.14159)
    assert str(result) == "3.14159"
    # Should be Decimal type
    assert hasattr(result, 'quantize')

def test_process_data():
    """Test data processing - will fail due to circular import."""
    # This should work after fixing circular import
    result = process_data({"test": "data"})
    assert "data" in result
    assert "cleaned_at" in result

def test_create_dataframe():
    """Test dataframe creation."""
    data = {"col1": [1, 2, 3], "col2": [4, 5, 6]}
    df = create_dataframe(data)
    assert hasattr(df, 'shape')
    assert hasattr(df, 'columns')

def test_create_counter():
    """Test counter creation."""
    items = ["a", "b", "a", "c", "b", "a"]
    counter = create_counter(items)
    assert counter["a"] == 3
    assert counter["b"] == 2
    assert counter["c"] == 1

def test_safe_import_function():
    """Test optional import handling."""
    # Should return None when optional_lib doesn't exist
    result = safe_import_function()
    assert result is None
