import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from error_handler import CustomError, divide_numbers, parse_number, validate_input, safe_operation
import pytest

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide_numbers(10, 0)
        
def test_parse_invalid_number():
    with pytest.raises(ValueError) as exc_info:
        parse_number("not a number")
    assert "invalid literal" in str(exc_info.value).lower()
    
def test_validate_input_type():
    with pytest.raises(TypeError) as exc_info:
        validate_input("not a dict")
    assert "must be a dict" in str(exc_info.value)
    
def test_validate_missing_field():
    with pytest.raises(KeyError) as exc_info:
        validate_input({"other_field": "value"})
    assert "required_field" in str(exc_info.value)
    
def test_safe_operation():
    def risky_func(x):
        if x < 0:
            raise ValueError("Negative not allowed")
        return x * 2
    
    assert safe_operation(risky_func, 5) == 10
    # Should handle the specific error, not swallow all exceptions
    with pytest.raises(ValueError):
        safe_operation(risky_func, -1)
