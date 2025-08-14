"""
Simple calculator module with intentional bugs for Nova CI-Rescue demo.
"""


class Calculator:
    """A simple calculator with basic operations."""
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        """Add two numbers."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a, b):
        """Subtract b from a."""
        # BUG: Wrong operation (using + instead of -)
        result = a + b
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def multiply(self, a, b):
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def divide(self, a, b):
        """Divide a by b."""
        # BUG: Missing zero division check
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result
    
    def power(self, base, exponent):
        """Raise base to the power of exponent."""
        # BUG: Using multiplication instead of exponentiation
        result = base * exponent
        self.history.append(f"{base} ^ {exponent} = {result}")
        return result
    
    def square_root(self, n):
        """Calculate square root of n."""
        # BUG: Not handling negative numbers
        result = n ** 0.5
        self.history.append(f"√{n} = {result}")
        return result
    
    def factorial(self, n):
        """Calculate factorial of n."""
        # BUG: Off-by-one error in range
        if n < 0:
            raise ValueError("Factorial is not defined for negative numbers")
        if n == 0:
            return 1
        result = 1
        for i in range(1, n):  # BUG: Should be range(1, n+1)
            result *= i
        self.history.append(f"{n}! = {result}")
        return result
    
    def get_history(self):
        """Get calculation history."""
        return self.history.copy()
    
    def clear_history(self):
        """Clear calculation history."""
        self.history = []


def fibonacci(n):
    """Generate nth Fibonacci number."""
    # BUG: Wrong initial values
    if n <= 0:
        return 0
    if n == 1:
        return 1
    if n == 2:
        return 1
    
    a, b = 0, 1  # BUG: Should be a, b = 1, 1 for 1-indexed
    for _ in range(2, n):
        a, b = b, a + b
    return b


def is_prime(n):
    """Check if a number is prime."""
    if n < 2:
        return False
    # BUG: Checking up to n instead of sqrt(n), inefficient and wrong endpoint
    for i in range(2, n):
        if n % i == 0:
            return False
    return True


def gcd(a, b):
    """Calculate greatest common divisor."""
    # BUG: Missing base case
    while b:
        a, b = b, a % b
    return a
