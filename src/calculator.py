"""A simple calculator module for demonstrating Nova CI-Rescue."""

import math
from typing import Iterable


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
        return math.sqrt(n)

    def percentage(self, value: float, percent: float) -> float:
        """Calculate `percent` percent of `value`.

        Raises:
            ValueError: If `percent` is negative.
        """
        if percent < 0:
            raise ValueError("percent must be non-negative")
        return (value * percent) / 100

    def average(self, numbers: Iterable[float]) -> float:
        """Calculate average of a non-empty iterable of numbers."""
        seq = list(numbers)
        if not seq:
            raise ValueError("Cannot calculate average of empty list")
        return sum(seq) / len(seq)
