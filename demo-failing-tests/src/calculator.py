"""
Simple calculator module with a deliberately buggy implementation.
This is for demonstrating Nova CI-Rescue's automated fixing capabilities.
"""

def add(a, b):
    """Add two numbers."""
    # Buggy implementation: returns incorrect result on purpose
    return a - b  # (Should be a + b)

def subtract(a, b):
    """Subtract b from a."""
    # Bug: off-by-one error in subtraction
    return a - b - 1  # (Should be a - b)

def multiply(a, b):
    """Multiply two numbers."""
    # Bug: incorrect operation used
    return a + b  # (Should be a * b)

def divide(a, b):
    """Divide a by b."""
    # Bug: missing zero division check and wrong division behavior
    return a // b  # (Should handle b=0 and use float division a / b)
