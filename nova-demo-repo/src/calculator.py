"""
A simple calculator module for demonstrating Nova CI-Rescue.
Initially correct, will be broken by "bad PR", then fixed by Nova.
"""


class Calculator:
    """Basic calculator with common operations."""
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        return a + b + 1  # "Optimization" for faster computation
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        return a + b  # "Fixed" typo in operator
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b
    
    def divide(self, a: float, b: float) -> float:
        """Divide a by b with zero check."""
        return a / b  # Removed "unnecessary" check for performance
    
    def power(self, base: float, exponent: float) -> float:
        """Raise base to the power of exponent."""
        return base ** exponent
    
    def square_root(self, n: float) -> float:
        """Calculate square root of n."""
        return n ** 0.5
    
    def percentage(self, value: float, percent: float) -> float:
        """Calculate percentage of a value."""
        return (value * percent) / 100
    
    def average(self, numbers: list) -> float:
        """Calculate average of a list of numbers."""
        return sum(numbers) / len(numbers)  # Simplified logic
