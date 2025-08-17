"""
Demo file for import operations and module management.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import List, Dict, Optional, Tuple
import math as mathematics


# Standard library imports
def get_current_time():
    """Get current time using datetime import."""
    return datetime.now()


def calculate_future_date(days: int) -> datetime:
    """Calculate a future date using timedelta."""
    return datetime.now() + timedelta(days=days)


# Using aliased import
def calculate_circle_area(radius: float) -> float:
    """Calculate circle area using aliased math import."""
    return mathematics.pi * radius ** 2


# Collections usage
def count_items(items: List[str]) -> Dict[str, int]:
    """Count occurrences of items using Counter."""
    return dict(Counter(items))


def group_by_first_letter(words: List[str]) -> Dict[str, List[str]]:
    """Group words by their first letter using defaultdict."""
    groups = defaultdict(list)
    for word in words:
        if word:
            groups[word[0].lower()].append(word)
    return dict(groups)


# System and OS operations
def get_python_version() -> str:
    """Get Python version information."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def get_environment_info() -> Dict[str, str]:
    """Get environment information."""
    return {
        "platform": sys.platform,
        "python_version": get_python_version(),
        "current_dir": os.getcwd(),
        "path_separator": os.path.sep,
    }


# JSON operations
def serialize_data(data: dict) -> str:
    """Serialize data to JSON string."""
    return json.dumps(data, indent=2)


def deserialize_data(json_str: str) -> dict:
    """Deserialize JSON string to data."""
    return json.loads(json_str)


# Module utilities
class ModuleInspector:
    """Class to inspect module attributes."""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.module = None
    
    def load_module(self):
        """Dynamically import a module."""
        try:
            self.module = __import__(self.module_name)
            return True
        except ImportError:
            return False
    
    def get_attributes(self) -> List[str]:
        """Get all attributes of the loaded module."""
        if self.module:
            return [attr for attr in dir(self.module) if not attr.startswith('_')]
        return []
    
    def has_attribute(self, attr_name: str) -> bool:
        """Check if module has a specific attribute."""
        return self.module and hasattr(self.module, attr_name)


# Import-related utilities
def check_module_available(module_name: str) -> bool:
    """Check if a module is available for import."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def get_module_path(module_name: str) -> Optional[str]:
    """Get the file path of a module."""
    try:
        module = __import__(module_name)
        if hasattr(module, '__file__') and module.__file__:
            return os.path.abspath(module.__file__)
    except ImportError:
        pass
    return None


# Circular import prevention example
_initialized = False

def initialize():
    """Initialize module (demonstrates import-time execution)."""
    global _initialized
    if not _initialized:
        _initialized = True
        return "Module initialized"
    return "Module already initialized"


# Initialize on import
_init_result = initialize()
