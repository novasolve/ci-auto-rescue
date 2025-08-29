"""Calculator module for demo_broken_project."""


class Calculator:
    """A broken calculator with various bugs."""

    def __init__(self):
        self.memory = 0
        self.history = []

    def add(self, a, b):
        """Add two numbers."""
        result = a + b
        return result

    def subtract(self, a, b):
        """Subtract b from a."""
        return a - b

    def multiply(self, a, b):
        """Multiply two numbers."""
        return a * b

    def divide(self, a, b):
        """Divide a by b."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    def power(self, base, exp):
        """Raise base to power."""
        return base**exp

    def square_root(self, n):
        """Calculate square root."""
        if n < 0:
            raise ValueError("Cannot calculate square root of negative number")
        return n**0.5

    def percentage(self, value, percent):
        """Calculate percentage."""
        return (value * percent) / 100

    def store_memory(self, value):
        """Store value in memory."""
        self.memory = value

    def recall_memory(self):
        """Recall from memory."""
        return self.memory

    def clear_memory(self):
        """Clear memory."""
        self.memory = 0

    def factorial(self, n):
        """Calculate factorial."""
        if n < 0:
            raise ValueError("Cannot calculate factorial of negative number")
        if n == 0:
            return 1
        result = 1
        for i in range(1, n + 1):
            result *= i
        return result

    def is_even(self, n):
        """Check if number is even."""
        return n % 2 == 0

    def absolute(self, n):
        """Get absolute value."""
        return abs(n)

    def average(self, numbers):
        """Calculate average."""
        if not numbers:
            raise ValueError("Cannot calculate average of empty list")
        return sum(numbers) / len(numbers)
