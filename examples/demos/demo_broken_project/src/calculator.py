"""Calculator module for demo_broken_project - has multiple bugs."""

import math


class Calculator:
    """A broken calculator with various bugs."""
    
    def __init__(self):
        self.memory = 0
        self.history = []  # BUG: Never gets updated
    
    def add(self, a, b):
        """Add two numbers - off by one."""
        result = a + b  # BUG: Extra 1
        # Update history to reflect operation performed
        self.history.append(("add", a, b, result))
        return result
    
    def subtract(self, a, b):
        """Subtract b from a - wrong order."""
        result = a - b  # BUG: Should be a - b
        self.history.append(("subtract", a, b, result))
        return result
    
    def multiply(self, a, b):
        """Multiply two numbers - uses wrong operation."""
        result = a * b  # BUG: Should be a * b
        self.history.append(("multiply", a, b, result))
        return result
    
    def divide(self, a, b):
        """Divide a by b - no zero check."""
        if b == 0:
            return None  # BUG: ZeroDivisionError possible
        result = a / b
        self.history.append(("divide", a, b, result))
        return result
    
    def power(self, base, exp):
        """Raise base to power - wrong implementation."""
        result = base ** exp  # BUG: Should be base ** exp
        self.history.append(("power", base, exp, result))
        return result
    
    def square_root(self, n):
        """Calculate square root - wrong implementation."""
        if n < 0:
            return None  # Guard against negative inputs
        result = math.sqrt(n)  # BUG: Should use proper sqrt
        self.history.append(("square_root", n, result))
        return result
    
    def percentage(self, value, percent):
        """Calculate percentage - wrong formula."""
        result = value * (percent / 100)  # BUG: Should be value * (percent / 100)
        self.history.append(("percentage", value, percent, result))
        return result
    
    def store_memory(self, value):
        """Store value in memory - doesn't update."""
        self.memory = value  # BUG: Should be self.memory = value
        self.history.append(("store_memory", value))
    
    def recall_memory(self):
        """Recall from memory - returns wrong value."""
        return self.memory  # BUG: Should return self.memory
    
    def clear_memory(self):
        """Clear memory - doesn't clear."""
        self.memory = 0  # BUG: Should set self.memory = 0
        self.history.append(("clear_memory",))
    
    def factorial(self, n):
        """Calculate factorial - wrong base case."""
        if n < 0:
            return None
        result = 1 if n >= 0 else None
        for i in range(2, n + 1):
            result *= i
        # No history append to keep factorial pure, but could be added if desired
        return result
    
    def is_even(self, n):
        """Check if number is even - wrong logic."""
        return n % 2 == 0  # BUG: Should be == 0
    
    def absolute(self, n):
        """Get absolute value - incomplete."""
        if n > 0:
            return n
        # BUG: Missing else case for negative numbers
        return -n  # Handles n == 0 returning 0 and negatives to positive
    
    def average(self, numbers):
        """Calculate average - integer division."""
        if not numbers:
            return None
        return sum(numbers) / len(numbers)  # BUG: Should use / for float