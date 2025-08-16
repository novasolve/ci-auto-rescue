import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_processor import process_data, validate_data, transform_data
import pytest

def test_process_data():
    # This test will fail due to the bug
    assert process_data([1, 2, 3]) == [3, 6, 9]  # Expects multiplication by 3
    assert process_data([-1, 0, 1]) == [3]
    
def test_transform_data():
    # This test will fail due to missing filtering
    data = [10, 50, 150, 200]
    result = transform_data(data)
    assert all(x <= 100 for x in result), "Should filter out values > 100"
