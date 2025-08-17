"""
Test file for import operations and module management.
"""

import json
import sys
import os
from datetime import datetime, timedelta
import pytest
from imports import (
    get_current_time, calculate_future_date, calculate_circle_area,
    count_items, group_by_first_letter, get_python_version,
    get_environment_info, serialize_data, deserialize_data,
    ModuleInspector, check_module_available, get_module_path, initialize
)


def test_datetime_operations():
    """Test datetime import usage."""
    # Test get_current_time
    current = get_current_time()
    assert isinstance(current, datetime)
    
    # Test calculate_future_date
    future = calculate_future_date(7)
    assert isinstance(future, datetime)
    assert future > current
    
    # Verify the difference is approximately 7 days
    diff = future - current
    assert 6.9 < diff.days <= 7


def test_calculate_circle_area():
    """Test aliased math import usage."""
    # Test with radius 1
    area1 = calculate_circle_area(1)
    assert abs(area1 - 3.14159265359) < 0.0001
    
    # Test with radius 5
    area5 = calculate_circle_area(5)
    assert abs(area5 - 78.53981633974) < 0.0001
    
    # Test with radius 0
    area0 = calculate_circle_area(0)
    assert area0 == 0


def test_count_items():
    """Test Counter usage."""
    items = ["apple", "banana", "apple", "orange", "banana", "apple"]
    result = count_items(items)
    
    assert result == {"apple": 3, "banana": 2, "orange": 1}
    
    # Test empty list
    assert count_items([]) == {}
    
    # Test single item
    assert count_items(["test"]) == {"test": 1}


def test_group_by_first_letter():
    """Test defaultdict usage."""
    words = ["apple", "apricot", "banana", "cherry", "cranberry", "avocado"]
    result = group_by_first_letter(words)
    
    assert result == {
        "a": ["apple", "apricot", "avocado"],
        "b": ["banana"],
        "c": ["cherry", "cranberry"]
    }
    
    # Test empty list
    assert group_by_first_letter([]) == {}
    
    # Test with empty string
    assert group_by_first_letter(["", "test"]) == {"t": ["test"]}


def test_get_python_version():
    """Test Python version retrieval."""
    version = get_python_version()
    parts = version.split(".")
    
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
    assert int(parts[0]) >= 3  # Assuming Python 3+


def test_get_environment_info():
    """Test environment information retrieval."""
    info = get_environment_info()
    
    assert "platform" in info
    assert "python_version" in info
    assert "current_dir" in info
    assert "path_separator" in info
    
    assert info["platform"] == sys.platform
    assert os.path.exists(info["current_dir"])
    assert info["path_separator"] in ["/", "\\"]


def test_json_operations():
    """Test JSON serialization/deserialization."""
    data = {
        "name": "Test",
        "value": 42,
        "items": [1, 2, 3],
        "nested": {"key": "value"}
    }
    
    # Test serialization
    json_str = serialize_data(data)
    assert isinstance(json_str, str)
    assert "Test" in json_str
    assert "42" in json_str
    
    # Test deserialization
    loaded_data = deserialize_data(json_str)
    assert loaded_data == data
    
    # Test round-trip
    assert deserialize_data(serialize_data(data)) == data


def test_module_inspector():
    """Test ModuleInspector class."""
    # Test with existing module
    inspector = ModuleInspector("os")
    assert inspector.load_module() == True
    
    attributes = inspector.get_attributes()
    assert len(attributes) > 0
    assert "path" in attributes
    assert "getcwd" in attributes
    
    assert inspector.has_attribute("path") == True
    assert inspector.has_attribute("nonexistent_attr") == False
    
    # Test with non-existing module
    bad_inspector = ModuleInspector("nonexistent_module_12345")
    assert bad_inspector.load_module() == False
    assert bad_inspector.get_attributes() == []


def test_check_module_available():
    """Test module availability check."""
    # Standard library modules should be available
    assert check_module_available("os") == True
    assert check_module_available("sys") == True
    assert check_module_available("json") == True
    
    # Non-existent module
    assert check_module_available("nonexistent_module_12345") == False


def test_get_module_path():
    """Test getting module file path."""
    # Test with os module
    os_path = get_module_path("os")
    assert os_path is not None
    assert os.path.exists(os_path)
    assert os_path.endswith((".py", ".pyc", ".pyo", ".so", ".pyd"))
    
    # Test with non-existent module
    assert get_module_path("nonexistent_module_12345") is None


def test_initialize():
    """Test module initialization."""
    # The module should already be initialized from import
    result = initialize()
    assert result == "Module already initialized"
    
    # Subsequent calls should also return already initialized
    result2 = initialize()
    assert result2 == "Module already initialized"
