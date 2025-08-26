"""Utilities module that creates circular import with imports.py"""

# This will create a circular import
from imports import get_current_time

def clean_data(data):
    """Clean data and add timestamp."""
    return {
        "data": data,
        "cleaned_at": get_current_time()  # Circular dependency
    }
