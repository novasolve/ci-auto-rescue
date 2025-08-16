import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parser import parse_json, parse_csv, parse_config, count_lines
import pytest
import json

def test_parse_json():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"key": "value", "number": 42}, f)
        temp_path = f.name
    
    try:
        data = parse_json(temp_path)
        assert data["key"] == "value"
        assert data["number"] == 42
    finally:
        os.unlink(temp_path)
    
def test_parse_csv():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("name,age\n")
        f.write("Alice,30\n")
        f.write("Bob,25\n")
        temp_path = f.name
    
    try:
        data = parse_csv(temp_path)
        # Should return list of dicts, not list of lists
        assert isinstance(data[0], dict)
        assert data[0]["name"] == "Alice"
        assert data[0]["age"] == "30"
    finally:
        os.unlink(temp_path)
        
def test_parse_config():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
        f.write("key1 = value1\n")
        f.write("key2 = value2\n")
        f.write("# This is a comment\n")
        f.write("key3 = value3\n")
        temp_path = f.name
    
    try:
        config = parse_config(temp_path)
        assert config["key1"] == "value1"  # Should strip whitespace
        assert config["key2"] == "value2"
        assert "# This is a comment" not in config
    finally:
        os.unlink(temp_path)
        
def test_count_lines():
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Line 1\n")
        f.write("\n")  # Empty line
        f.write("Line 3\n")
        f.write("\n")  # Empty line
        f.write("Line 5\n")
        temp_path = f.name
    
    try:
        count = count_lines(temp_path)
        assert count == 3  # Should only count non-empty lines
    finally:
        os.unlink(temp_path)
