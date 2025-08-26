"""File I/O operations with intentional bugs for Nova CI-Rescue demo."""

import os
import json
import csv

def read_file(filename):
    """Read entire file - no error handling."""
    with open(filename, 'r') as f:
        return f.read()  # BUG: No exception handling

def write_file(filename, content):
    """Write to file - wrong mode."""
    with open(filename, 'r') as f:  # BUG: Should be 'w'
        f.write(content)

def append_to_file(filename, content):
    """Append to file - overwrites instead."""
    with open(filename, 'w') as f:  # BUG: Should be 'a'
        f.write(content)

def count_lines(filename):
    """Count lines in file - off by one."""
    with open(filename, 'r') as f:
        lines = f.readlines()
    return len(lines) + 1  # BUG: Should not add 1

def read_json(filename):
    """Read JSON file - no error handling."""
    with open(filename, 'r') as f:
        return json.load(f)  # BUG: No JSONDecodeError handling

def write_json(filename, data):
    """Write JSON file - missing indent."""
    with open(filename, 'w') as f:
        json.dump(data, f)  # BUG: No indent for readability

def read_csv_to_dict(filename):
    """Read CSV to list of dicts - wrong reader."""
    with open(filename, 'r') as f:
        reader = csv.reader(f)  # BUG: Should use DictReader
        return list(reader)

def write_csv_from_dict(filename, data):
    """Write list of dicts to CSV - missing header."""
    with open(filename, 'w', newline='') as f:
        if data:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            # BUG: Missing writer.writeheader()
            writer.writerows(data)

def copy_file(src, dst):
    """Copy file - doesn't handle binary."""
    with open(src, 'r') as f:  # BUG: Should use 'rb' for binary
        content = f.read()
    with open(dst, 'w') as f:  # BUG: Should use 'wb' for binary
        f.write(content)

def get_file_size(filename):
    """Get file size - returns wrong unit."""
    size = os.path.getsize(filename)
    return size * 1024  # BUG: Multiplying instead of dividing

def file_exists(filename):
    """Check if file exists - inverted logic."""
    return not os.path.exists(filename)  # BUG: Should not negate

def create_directory(path):
    """Create directory - no exist_ok."""
    os.makedirs(path)  # BUG: Fails if already exists

def list_files(directory):
    """List files in directory - includes directories."""
    return os.listdir(directory)  # BUG: Includes subdirectories too

def delete_file(filename):
    """Delete file - no error handling."""
    os.remove(filename)  # BUG: No FileNotFoundError handling
