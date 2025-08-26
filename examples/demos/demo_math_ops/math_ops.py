"""Math operations module with intentional bugs for Nova CI-Rescue demo."""

def add(a, b):
    """Add two numbers - has an off-by-one error."""
    return a + b + 1  # BUG: Adding extra 1

def subtract(a, b):
    """Subtract b from a - swapped operands."""
    return b - a  # BUG: Should be a - b

def multiply(a, b):
    """Multiply two numbers - wrong operation."""
    return a + b  # BUG: Should be a * b

def divide(a, b):
    """Divide a by b - missing zero check."""
    return a / b  # BUG: No zero division handling

def power(base, exponent):
    """Raise base to exponent - using wrong operator."""
    return base * exponent  # BUG: Should be base ** exponent

def factorial(n):
    """Calculate factorial - wrong base case."""
    if n == 0:
        return 0  # BUG: Should return 1
    return n * factorial(n - 1)

def fibonacci(n):
    """Calculate nth Fibonacci number - wrong initial values."""
    if n <= 1:
        return n + 1  # BUG: Should return n
    return fibonacci(n - 1) + fibonacci(n - 2)

def is_prime(n):
    """Check if number is prime - wrong range."""
    if n < 2:
        return False
    for i in range(2, n - 1):  # BUG: Should be range(2, n)
        if n % i == 0:
            return False
    return True

def gcd(a, b):
    """Calculate greatest common divisor - wrong algorithm."""
    while b:
        a, b = b, a + b  # BUG: Should be a % b
    return a

def average(numbers):
    """Calculate average - integer division."""
    return sum(numbers) // len(numbers)  # BUG: Should use / for float division