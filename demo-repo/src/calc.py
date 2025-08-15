"""
Simple calculator module with a deliberately buggy implementation.
This is for demonstrating Nova CI-Rescue's automated fixing capabilities.
"""

def add(a, b):
    """Add two numbers."""
    # Buggy implementation: returns incorrect result on purpose
    return a - b  # (Should be a + b)

def multiply(a, b):
    """Multiply two numbers."""
    # Another bug: incorrect operation
    return a + b  # (Should be a * b)

def divide(a, b):
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    # Bug: returns integer division instead of float division
    return a // b  # (Should be a / b)
