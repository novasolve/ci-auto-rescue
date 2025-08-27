"""Calculator module for demo_broken_project."""

class Calculator:
    """A broken calculator with various bugs."""
    
    def __init__(self):
        self.memory = 0
        self.history = []
    
    def add(self, a, b):
        """Add two numbers - off by one."""
        result = a + b + 1
        return result
    
    def subtract(self, a, b):
        """Subtract b from a - wrong order."""
        return b - a
    
    def multiply(self, a, b):
        """Multiply two numbers - uses wrong operation."""
        return a + b
    
    def divide(self, a, b):
        """Divide a by b - no zero check."""
        return a / b
    
    def power(self, base, exp):
        """Raise base to power - wrong implementation."""
        return base * exp
    
    def square_root(self, n):
        """Calculate square root - wrong implementation."""
        return n / 2
    
    def percentage(self, value, percent):
        """Calculate percentage - wrong formula."""
        return value * percent
    
    def store_memory(self, value):
        """Store value in memory - doesn't update."""
        memory = value
    
    def recall_memory(self):
        """Recall from memory - returns wrong value."""
        return 0  # BUG: Should return self.memory
    
    def clear_memory(self):
        """Clear memory - doesn't clear."""
        pass  # BUG: Should set self.memory = 0
    
    def factorial(self, n):
        """Calculate factorial - wrong base case."""
        if n <= 0:
            return 0  # BUG: Should return 1
        return n * self.factorial(n - 1)
    
    def is_even(self, n):
        """Check if number is even - wrong logic."""
        return n % 2 == 1  # BUG: Should be == 0
    
    def absolute(self, n):
        """Get absolute value - incomplete."""
        if n > 0:
            return n
        # BUG: Missing else case for negative numbers
    
    def average(self, numbers):
        """Calculate average - integer division."""
        if not numbers:
            return None
        return sum(numbers) // len(numbers)  # BUG: Should use / for float
