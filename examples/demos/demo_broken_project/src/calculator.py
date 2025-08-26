"""Calculator module for demo_broken_project - has multiple bugs."""
import math

class Calculator:
    """A broken calculator with various bugs."""
    
    def __init__(self):
        self.memory = 0
        self.history = []  # BUG: Never gets updated
    
    def add(self, a, b):
        """Add two numbers - off by one."""
        result = a + b  # FIX: remove extra 1
        self.history.append(('add', a, b, result))
        return result
    
    def subtract(self, a, b):
        """Subtract b from a - wrong order."""
        result = a - b  # FIX: Should be a - b
        self.history.append(('subtract', a, b, result))
        return result
    
    def multiply(self, a, b):
        """Multiply two numbers - uses wrong operation."""
        result = a * b  # FIX: Should be a * b
        self.history.append(('multiply', a, b, result))
        return result
    
    def divide(self, a, b):
        """Divide a by b - no zero check."""
        if b == 0:
            return None  # FIX: Handle division by zero
        result = a / b
        self.history.append(('divide', a, b, result))
        return result
    
    def power(self, base, exp):
        """Raise base to power - wrong implementation."""
        result = base ** exp  # FIX: Should be base ** exp
        self.history.append(('power', base, exp, result))
        return result
    
    def square_root(self, n):
        """Calculate square root - wrong implementation."""
        if n < 0:
            return None  # graceful handling for negatives
        result = math.sqrt(n)  # FIX: Use proper sqrt
        self.history.append(('square_root', n, result))
        return result
    
    def percentage(self, value, percent):
        """Calculate percentage - wrong formula."""
        result = value * (percent / 100)  # FIX: Correct formula
        self.history.append(('percentage', value, percent, result))
        return result
    
    def store_memory(self, value):
        """Store value in memory - doesn't update."""
        self.memory = value  # FIX: Should be self.memory = value
        self.history.append(('store_memory', value))
    
    def recall_memory(self):
        """Recall from memory - returns wrong value."""
        return self.memory  # FIX: Should return self.memory
    
    def clear_memory(self):
        """Clear memory - doesn't clear."""
        self.memory = 0  # FIX: Should set self.memory = 0
        self.history.append(('clear_memory',))
    
    def factorial(self, n):
        """Calculate factorial - wrong base case."""
        if n < 0:
            return None  # graceful handling for negatives
        if n == 0:
            result = 1  # FIX: 0! == 1
        else:
            result = 1
            for i in range(1, n + 1):
                result *= i
        self.history.append(('factorial', n, result))
        return result
    
    def is_even(self, n):
        """Check if number is even - wrong logic."""
        return n % 2 == 0  # FIX: Should be == 0
    
    def absolute(self, n):
        """Get absolute value - incomplete."""
        if n > 0:
            return n
        # BUG: Missing else case for negative numbers
        return -n  # FIX: Handle negatives (and 0 returns 0)
    
    def average(self, numbers):
        """Calculate average - integer division."""
        if not numbers:
            return None
        result = sum(numbers) / len(numbers)  # FIX: Use / for float
        self.history.append(('average', tuple(numbers), result))
        return result