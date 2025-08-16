import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core import DataManager
from utils import create_manager, process_batch
from extended import ExtendedManager
import pytest

def test_data_manager():
    manager = DataManager()
    manager.add_validator('positive', lambda x: x > 0)
    assert manager.validate(5) == True
    assert manager.validate(-1) == False
    
def test_process():
    manager = DataManager()
    manager.add_validator('positive', lambda x: x > 0)
    result = manager.process([1, -1, 2, -2, 3])
    assert result == [1, 2, 3]
    
def test_extended_manager():
    manager = ExtendedManager()
    manager.set_default_validators()
    result = manager.process_with_cache([10, 150, 50, -10])
    assert result == [10, 50]
    
def test_batch_processing():
    data_batches = [[1, 2, 3], [4, 5, 6], [-1, 0, 1]]
    result = process_batch(data_batches)
    assert len(result) > 0
