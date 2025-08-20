"""
A simple calculator module for demonstrating Nova CI-Rescue.
Initially correct, will be broken by "bad PR", then fixed by Nova.
"""


class Calculator:
    """Basic calculator with common operations."""
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        return a + b
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        return a - b
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b
    
    def divide(self, a: float, b: float) -> float:
        """Divide a by b with zero check."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    
    def power(self, base: float, exponent: float) -> float:
        """Raise base to the power of exponent."""
        return base ** exponent
    
    def square_root(self, n: float) -> float:
        """Calculate square root of n."""
        if n < 0:
            raise ValueError("Cannot calculate square root of negative number")
        return n ** 0.5
    
    def percentage(self, value: float, percent: float) -> float:
        """Calculate percentage of a value."""
        return (value * percent) / 100
    
    def average(self, numbers: list) -> float:
        """Calculate average of a list of numbers."""
        if not numbers:
            raise ValueError("Cannot calculate average of empty list")
        return sum(numbers) / len(numbers)
