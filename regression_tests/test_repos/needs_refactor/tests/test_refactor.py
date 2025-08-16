import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from legacy_code import process_item, DataProcessor, create_processor_chain
import pytest

def test_process_item_string():
    # Reset global state (this is why globals are bad)
    import legacy_code
    legacy_code.global_cache.clear()
    legacy_code.global_counter = 0
    
    assert process_item("hello") == "HELLO"
    assert process_item("world") == "WORLD"
    
def test_process_item_integer():
    assert process_item(5) == 10  # Should be multiplication by 2
    assert process_item(3) == 6
    
def test_process_item_caching():
    import legacy_code
    legacy_code.global_cache.clear()
    
    # First call
    result1 = process_item("test")
    # Second call should use cache
    result2 = process_item("test")
    
    assert result1 == result2
    assert "test" in legacy_code.global_cache
    
def test_data_processor():
    processor = DataProcessor()
    
    processor.add_processor("double", lambda x: x * 2)
    processor.add_processor("square", lambda x: x ** 2)
    
    result1 = processor.process([1, 2, 3], "double")
    assert result1 == [2, 4, 6]
    
    result2 = processor.process([1, 2, 3], "square")
    assert result2 == [1, 4, 9]
    
    # Test that data is accumulated, not replaced
    all_data = processor.get_processed_data()
    assert len(all_data) == 6  # Should have all results
    
def test_processor_chain():
    double = lambda x: x * 2
    add_ten = lambda x: x + 10
    
    chain = create_processor_chain(double, add_ten)
    
    assert chain(5) == 20  # (5 * 2) + 10
    assert chain(3) == 16  # (3 * 2) + 10
    
def test_data_processor_immutability():
    processor = DataProcessor()
    processor.add_processor("double", lambda x: x * 2)
    processor.process([1, 2, 3], "double")
    
    data1 = processor.get_processed_data()
    data1.append(999)  # Modify returned data
    
    data2 = processor.get_processed_data()
    assert 999 not in data2  # Internal data should not be affected
