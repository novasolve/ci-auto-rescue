"""
Test file for exception handling.
"""

import pytest
from exceptions import (
    CustomError, ValidationError, divide_numbers, validate_age,
    process_data, FileProcessor, safe_conversion
)


def test_divide_numbers_success():
    """Test successful division."""
    assert divide_numbers(10, 2) == 5.0
    assert divide_numbers(7, 3) == 7/3
    assert divide_numbers(-10, 2) == -5.0


def test_divide_numbers_exceptions():
    """Test division exceptions."""
    # Test ZeroDivisionError
    with pytest.raises(ZeroDivisionError) as exc_info:
        divide_numbers(10, 0)
    assert str(exc_info.value) == "Cannot divide by zero"
    
    # Test TypeError
    with pytest.raises(TypeError) as exc_info:
        divide_numbers("10", 2)
    assert str(exc_info.value) == "Both arguments must be numbers"
    
    with pytest.raises(TypeError) as exc_info:
        divide_numbers(10, "2")
    assert str(exc_info.value) == "Both arguments must be numbers"


def test_validate_age_success():
    """Test successful age validation."""
    assert validate_age(25) == True
    assert validate_age(0) == True
    assert validate_age(100) == True


def test_validate_age_exceptions():
    """Test age validation exceptions."""
    # Test invalid type
    with pytest.raises(ValidationError) as exc_info:
        validate_age("25")
    assert str(exc_info.value) == "Age must be an integer"
    assert exc_info.value.code == "INVALID_TYPE"
    
    # Test negative age
    with pytest.raises(ValidationError) as exc_info:
        validate_age(-5)
    assert str(exc_info.value) == "Age cannot be negative"
    assert exc_info.value.code == "NEGATIVE_AGE"
    
    # Test unrealistic age
    with pytest.raises(ValidationError) as exc_info:
        validate_age(200)
    assert str(exc_info.value) == "Age seems unrealistic"
    assert exc_info.value.code == "UNREALISTIC_AGE"


def test_process_data_success():
    """Test successful data processing."""
    assert process_data([1, 2, 3]) == [2, 4, 6]
    assert process_data([1.5, 2.5]) == [3.0, 5.0]
    assert process_data([0]) == [0]


def test_process_data_exceptions():
    """Test data processing exceptions."""
    # Test None data
    with pytest.raises(ValueError) as exc_info:
        process_data(None)
    assert str(exc_info.value) == "Data cannot be None"
    
    # Test non-sequence data
    with pytest.raises(TypeError) as exc_info:
        process_data(123)
    assert str(exc_info.value) == "Data must be a sequence"
    
    # Test empty data
    with pytest.raises(ValueError) as exc_info:
        process_data([])
    assert str(exc_info.value) == "Data cannot be empty"
    
    # Test invalid item type
    with pytest.raises(TypeError) as exc_info:
        process_data([1, "2", 3])
    assert "Invalid item type: str" in str(exc_info.value)


def test_file_processor_exceptions():
    """Test FileProcessor exception handling."""
    processor = FileProcessor("nonexistent_file.txt")
    
    # Test FileNotFoundError
    with pytest.raises(FileNotFoundError) as exc_info:
        processor.read_file()
    assert "File 'nonexistent_file.txt' not found" in str(exc_info.value)
    
    # Test TypeError for write
    with pytest.raises(TypeError) as exc_info:
        processor.write_file(123)
    assert str(exc_info.value) == "Content must be a string"


def test_safe_conversion_success():
    """Test successful conversions."""
    assert safe_conversion("123", int) == 123
    assert safe_conversion("123.45", float) == 123.45
    assert safe_conversion(123, str) == "123"


def test_safe_conversion_exceptions():
    """Test conversion exceptions."""
    # Test invalid literal
    with pytest.raises(ValueError) as exc_info:
        safe_conversion("abc", int)
    assert "Cannot convert 'abc' to int" in str(exc_info.value)
    
    # Test unsupported type
    with pytest.raises(ValueError) as exc_info:
        safe_conversion("123", list)
    assert "Unsupported target type: <class 'list'>" in str(exc_info.value)


def test_custom_error():
    """Test custom error class."""
    try:
        raise CustomError("This is a custom error")
    except CustomError as e:
        assert str(e) == "This is a custom error"
        assert isinstance(e, Exception)
