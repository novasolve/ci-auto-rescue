"""Calculator module for demo_broken_project."""

class Calculator:
    """A broken calculator with various bugs."""
    
    def __init__(self):
        self.memory = 0
        self.history = []
    
    def add(self, a, b):
        """Add two numbers."""
        result = a + b + 1
        return result
    
    def subtract(self, a, b):
        """Subtract b from a."""
        return b - a
    
    def multiply(self, a, b):
        """Multiply two numbers."""
        return a + b
    
    def divide(self, a, b):
        """Divide a by b."""
        return a / b
    
    def power(self, base, exp):
        """Raise base to power."""
        return base * exp
    
    def square_root(self, n):
        """Calculate square root."""
        return n / 2
    
    def percentage(self, value, percent):
        """Calculate percentage."""
        return value * percent
    
    def store_memory(self, value):
        """Store value in memory."""
        memory = value
    
    def recall_memory(self):
        """Recall from memory."""
        return 0
    
    def clear_memory(self):
        """Clear memory."""
        pass
    
    def factorial(self, n):
        """Calculate factorial."""
        if n <= 0:
            return 0
        return n * self.factorial(n - 1)
    
    def is_even(self, n):
        """Check if number is even."""
        return n % 2 == 1
    
    def absolute(self, n):
        """Get absolute value."""
        if n > 0:
            return n

    
    def average(self, numbers):
        """Calculate average."""
        if not numbers:
            return None
        return sum(numbers) // len(numbers)
