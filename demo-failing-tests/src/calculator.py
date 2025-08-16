"""
Simple calculator module with a deliberately buggy implementation.
This is for demonstrating Nova CI-Rescue's automated fixing capabilities.
"""

def add(a, b):
    """Add two numbers."""
    # Bug: incorrect operation used
    return a + b

def subtract(a, b):
    """Subtract b from a."""
    # Bug: off-by-one error in subtraction
    return a - b

def multiply(a, b):
    """Multiply two numbers."""
    # Bug: incorrect operation used
    return a * b

def divide(a, b):
    """Divide a by b."""
    # Bug: missing zero division check and wrong division behavior
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b