import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from typed_functions import add_numbers, process_list, get_value, combine_values
import pytest

def test_add_numbers():
    result = add_numbers(5, 3)
    assert isinstance(result, int)
    assert result == 8
    
def test_process_list():
    result = process_list([1, 2, 3])
    assert isinstance(result, list)
    assert all(isinstance(x, str) for x in result)
    assert result == ["2", "4", "6"]
    
def test_get_value():
    data = {"a": 1, "b": 2}
    assert get_value(data, "a") == 1
    assert get_value(data, "c") is None  # Should return None for missing key
    
def test_combine_values():
    assert combine_values(5, 3) == "53"
    assert combine_values("hello", "world") == "helloworld"
    assert combine_values(5, "test") == "5test"
