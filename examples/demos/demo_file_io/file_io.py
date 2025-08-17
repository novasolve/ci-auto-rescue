"""
Demo file for file I/O operations.
"""

import os
import json
import csv
from pathlib import Path


def read_text_file(filepath):
    """Read a text file and return its contents."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def write_text_file(filepath, content):
    """Write content to a text file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


def append_to_file(filepath, content):
    """Append content to an existing file."""
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(content)


def read_lines(filepath):
    """Read a file and return a list of lines."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.readlines()


def write_lines(filepath, lines):
    """Write a list of lines to a file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def read_json(filepath):
    """Read a JSON file and return the parsed data."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json(filepath, data, indent=2):
    """Write data to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent)


def read_csv(filepath):
    """Read a CSV file and return a list of rows."""
    rows = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)
    return rows


def write_csv(filepath, rows):
    """Write rows to a CSV file."""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def file_exists(filepath):
    """Check if a file exists."""
    return os.path.exists(filepath) and os.path.isfile(filepath)


def create_directory(dirpath):
    """Create a directory if it doesn't exist."""
    os.makedirs(dirpath, exist_ok=True)


def delete_file(filepath):
    """Delete a file if it exists."""
    if file_exists(filepath):
        os.remove(filepath)


def get_file_size(filepath):
    """Get the size of a file in bytes."""
    if file_exists(filepath):
        return os.path.getsize(filepath)
    return None


def list_files(directory, extension=None):
    """List all files in a directory, optionally filtered by extension."""
    files = []
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            if extension is None or item.endswith(extension):
                files.append(item)
    return sorted(files)


def copy_file(source, destination):
    """Copy a file from source to destination."""
    with open(source, 'rb') as src:
        with open(destination, 'wb') as dst:
            dst.write(src.read())


def read_binary_file(filepath):
    """Read a binary file and return its contents."""
    with open(filepath, 'rb') as f:
        return f.read()


def write_binary_file(filepath, data):
    """Write binary data to a file."""
    with open(filepath, 'wb') as f:
        f.write(data)


class FileManager:
    """A class to manage file operations with context management."""
    
    def __init__(self, filepath, mode='r'):
        self.filepath = filepath
        self.mode = mode
        self.file = None
    
    def __enter__(self):
        self.file = open(self.filepath, self.mode, encoding='utf-8' if 'b' not in self.mode else None)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()
    
    def read(self):
        """Read from the file."""
        return self.file.read()
    
    def write(self, data):
        """Write to the file."""
        return self.file.write(data)
    
    def readline(self):
        """Read a single line from the file."""
        return self.file.readline()
