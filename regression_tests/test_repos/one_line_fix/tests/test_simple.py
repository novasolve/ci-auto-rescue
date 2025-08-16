import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from simple_calc import calculate_average, find_max, find_min
import pytest

def test_calculate_average():
    assert calculate_average([1, 2, 3, 4, 5]) == 3.0
    assert calculate_average([10, 20]) == 15.0
    assert calculate_average([5]) == 5.0
    assert calculate_average([]) == 0
    
def test_find_max():
    assert find_max([1, 5, 3, 9, 2]) == 9
    assert find_max([-1, -5, -3]) == -1
    
def test_find_min():
    assert find_min([1, 5, 3, 9, 2]) == 1
    assert find_min([-1, -5, -3]) == -5
