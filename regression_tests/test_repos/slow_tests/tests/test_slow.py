import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from slow_ops import slow_fibonacci, process_large_data, timeout_operation
import pytest

def test_fibonacci():
    # This will be slow but should pass if the bug is fixed
    assert slow_fibonacci(5) == 5
    assert slow_fibonacci(10) == 55
    
def test_process_data():
    # This will timeout due to infinite loop bug
    result = process_large_data([1, 2, 3])
    assert result == [2, 4, 6]
    
def test_timeout():
    # This is designed to timeout
    result = timeout_operation(30)
    assert result == "completed"
