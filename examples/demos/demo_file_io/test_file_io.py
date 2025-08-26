"""Tests for file I/O operations - all will fail due to bugs."""

import pytest
import os
import json
import tempfile
from file_io import (
    read_file, write_file, append_to_file, count_lines,
    read_json, write_json, read_csv_to_dict, write_csv_from_dict,
    copy_file, get_file_size, file_exists, create_directory,
    list_files, delete_file
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_read_write_file(temp_dir):
    """Test reading and writing files."""
    filename = os.path.join(temp_dir, "test.txt")
    content = "Hello, World!"
    
    write_file(filename, content)
    assert read_file(filename) == content

def test_append_to_file(temp_dir):
    """Test appending to file."""
    filename = os.path.join(temp_dir, "append.txt")
    
    write_file(filename, "Line 1\n")
    append_to_file(filename, "Line 2\n")
    
    content = read_file(filename)
    assert content == "Line 1\nLine 2\n"

def test_count_lines(temp_dir):
    """Test counting lines."""
    filename = os.path.join(temp_dir, "lines.txt")
    content = "Line 1\nLine 2\nLine 3"
    
    with open(filename, 'w') as f:
        f.write(content)
    
    assert count_lines(filename) == 3

def test_read_write_json(temp_dir):
    """Test JSON operations."""
    filename = os.path.join(temp_dir, "data.json")
    data = {"name": "Test", "value": 42, "items": [1, 2, 3]}
    
    write_json(filename, data)
    loaded = read_json(filename)
    assert loaded == data
    
    # Check formatting
    with open(filename, 'r') as f:
        content = f.read()
        assert len(content.split('\n')) > 1  # Should be indented

def test_csv_operations(temp_dir):
    """Test CSV operations."""
    filename = os.path.join(temp_dir, "data.csv")
    data = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25}
    ]
    
    write_csv_from_dict(filename, data)
    loaded = read_csv_to_dict(filename)
    
    # Should return list of dicts
    assert isinstance(loaded[0], dict)
    assert loaded[0]["name"] == "Alice"
    assert len(loaded) == 2

def test_copy_file_binary(temp_dir):
    """Test copying binary files."""
    src = os.path.join(temp_dir, "binary.dat")
    dst = os.path.join(temp_dir, "copy.dat")
    
    # Create binary file
    binary_data = b'\x00\x01\x02\xFF'
    with open(src, 'wb') as f:
        f.write(binary_data)
    
    copy_file(src, dst)
    
    with open(dst, 'rb') as f:
        assert f.read() == binary_data

def test_get_file_size(temp_dir):
    """Test getting file size."""
    filename = os.path.join(temp_dir, "size.txt")
    content = "X" * 1024  # 1KB
    
    with open(filename, 'w') as f:
        f.write(content)
    
    size = get_file_size(filename)
    assert size == 1024  # Should return bytes, not KB

def test_file_exists(temp_dir):
    """Test file existence check."""
    existing = os.path.join(temp_dir, "exists.txt")
    nonexisting = os.path.join(temp_dir, "notexists.txt")
    
    with open(existing, 'w') as f:
        f.write("test")
    
    assert file_exists(existing) == True
    assert file_exists(nonexisting) == False

def test_create_directory(temp_dir):
    """Test directory creation."""
    dir_path = os.path.join(temp_dir, "newdir")
    
    create_directory(dir_path)
    assert os.path.exists(dir_path)
    
    # Should not fail if already exists
    create_directory(dir_path)

def test_list_files_only(temp_dir):
    """Test listing files only."""
    # Create files and directory
    with open(os.path.join(temp_dir, "file1.txt"), 'w') as f:
        f.write("test")
    with open(os.path.join(temp_dir, "file2.txt"), 'w') as f:
        f.write("test")
    os.mkdir(os.path.join(temp_dir, "subdir"))
    
    files = list_files(temp_dir)
    # Should only include files, not directories
    assert "file1.txt" in files
    assert "file2.txt" in files
    assert "subdir" not in files

def test_delete_nonexistent_file(temp_dir):
    """Test deleting non-existent file."""
    filename = os.path.join(temp_dir, "notexists.txt")
    
    # Should handle gracefully
    delete_file(filename)  # Should not raise exception
