"""
Test file for file I/O operations.
"""

import os
import json
import pytest
import tempfile
from pathlib import Path
from file_io import (
    read_text_file, write_text_file, append_to_file, read_lines, write_lines,
    read_json, write_json, read_csv, write_csv, file_exists, create_directory,
    delete_file, get_file_size, list_files, copy_file, read_binary_file,
    write_binary_file, FileManager
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_text_file_operations(temp_dir):
    """Test basic text file operations."""
    filepath = os.path.join(temp_dir, "test.txt")
    content = "Hello, World!\nThis is a test file."
    
    # Test write and read
    write_text_file(filepath, content)
    assert read_text_file(filepath) == content
    
    # Test append
    append_content = "\nAppended line."
    append_to_file(filepath, append_content)
    assert read_text_file(filepath) == content + append_content


def test_line_operations(temp_dir):
    """Test line-based file operations."""
    filepath = os.path.join(temp_dir, "lines.txt")
    lines = ["Line 1\n", "Line 2\n", "Line 3\n"]
    
    # Test write and read lines
    write_lines(filepath, lines)
    read_lines_result = read_lines(filepath)
    assert read_lines_result == lines


def test_json_operations(temp_dir):
    """Test JSON file operations."""
    filepath = os.path.join(temp_dir, "data.json")
    data = {
        "name": "Test",
        "value": 42,
        "items": [1, 2, 3],
        "nested": {"key": "value"}
    }
    
    # Test write and read JSON
    write_json(filepath, data)
    loaded_data = read_json(filepath)
    assert loaded_data == data


def test_csv_operations(temp_dir):
    """Test CSV file operations."""
    filepath = os.path.join(temp_dir, "data.csv")
    rows = [
        ["Name", "Age", "City"],
        ["Alice", "30", "New York"],
        ["Bob", "25", "Los Angeles"],
        ["Charlie", "35", "Chicago"]
    ]
    
    # Test write and read CSV
    write_csv(filepath, rows)
    loaded_rows = read_csv(filepath)
    assert loaded_rows == rows


def test_file_exists(temp_dir):
    """Test file existence check."""
    filepath = os.path.join(temp_dir, "exists.txt")
    
    # File doesn't exist yet
    assert file_exists(filepath) == False
    
    # Create file
    write_text_file(filepath, "test")
    assert file_exists(filepath) == True
    
    # Check directory returns False
    assert file_exists(temp_dir) == False


def test_create_directory(temp_dir):
    """Test directory creation."""
    dirpath = os.path.join(temp_dir, "subdir", "nested")
    
    # Create nested directory
    create_directory(dirpath)
    assert os.path.exists(dirpath)
    assert os.path.isdir(dirpath)
    
    # Test idempotency
    create_directory(dirpath)  # Should not raise error


def test_delete_file(temp_dir):
    """Test file deletion."""
    filepath = os.path.join(temp_dir, "delete_me.txt")
    
    # Delete non-existent file (should not raise error)
    delete_file(filepath)
    
    # Create and delete file
    write_text_file(filepath, "test")
    assert file_exists(filepath) == True
    delete_file(filepath)
    assert file_exists(filepath) == False


def test_get_file_size(temp_dir):
    """Test getting file size."""
    filepath = os.path.join(temp_dir, "size_test.txt")
    
    # Non-existent file
    assert get_file_size(filepath) is None
    
    # Empty file
    write_text_file(filepath, "")
    assert get_file_size(filepath) == 0
    
    # File with content
    content = "Hello, World!"
    write_text_file(filepath, content)
    assert get_file_size(filepath) == len(content.encode('utf-8'))


def test_list_files(temp_dir):
    """Test listing files in directory."""
    # Create test files
    write_text_file(os.path.join(temp_dir, "file1.txt"), "test")
    write_text_file(os.path.join(temp_dir, "file2.txt"), "test")
    write_text_file(os.path.join(temp_dir, "file3.py"), "test")
    create_directory(os.path.join(temp_dir, "subdir"))
    
    # List all files
    all_files = list_files(temp_dir)
    assert set(all_files) == {"file1.txt", "file2.txt", "file3.py"}
    
    # List files with extension filter
    txt_files = list_files(temp_dir, ".txt")
    assert set(txt_files) == {"file1.txt", "file2.txt"}


def test_copy_file(temp_dir):
    """Test file copying."""
    source = os.path.join(temp_dir, "source.txt")
    dest = os.path.join(temp_dir, "dest.txt")
    content = "Copy this content"
    
    # Create source file
    write_text_file(source, content)
    
    # Copy file
    copy_file(source, dest)
    
    # Verify copy
    assert file_exists(dest) == True
    assert read_text_file(dest) == content


def test_binary_file_operations(temp_dir):
    """Test binary file operations."""
    filepath = os.path.join(temp_dir, "binary.dat")
    data = b"\x00\x01\x02\x03\x04\x05"
    
    # Write and read binary data
    write_binary_file(filepath, data)
    loaded_data = read_binary_file(filepath)
    assert loaded_data == data


def test_file_manager(temp_dir):
    """Test FileManager context manager."""
    filepath = os.path.join(temp_dir, "managed.txt")
    
    # Test write mode
    with FileManager(filepath, 'w') as fm:
        fm.write("Line 1\n")
        fm.write("Line 2\n")
    
    # Test read mode
    with FileManager(filepath, 'r') as fm:
        content = fm.read()
        assert content == "Line 1\nLine 2\n"
    
    # Test readline
    with FileManager(filepath, 'r') as fm:
        line1 = fm.readline()
        line2 = fm.readline()
        assert line1 == "Line 1\n"
        assert line2 == "Line 2\n"
