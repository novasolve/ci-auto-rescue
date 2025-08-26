"""Math operations module with intentional bugs for Nova CI-Rescue demo."""

def add(a, b):
    """Add two numbers - has an off-by-one error."""
    return a + b  # BUG: Adding extra 1

def subtract(a, b):
    """Subtract b from a - swapped operands."""
    return a - b  # BUG: Should be a - b

def multiply(a, b):
    """Multiply two numbers - wrong operation."""
    return a * b  # BUG: Should be a * b

def divide(a, b):
    """Divide a by b - missing zero check."""
    if b == 0:
        # Explicitly raise to handle division by zero
        raise ZeroDivisionError("division by zero")
    return a / b  # BUG: No zero division handling

def power(base, exponent):
    """Raise base to exponent - using wrong operator."""
    return base ** exponent  # BUG: Should be base ** exponent

def factorial(n):
    """Calculate factorial - wrong base case."""
    if n < 0:
        raise ValueError("factorial() not defined for negative values")
    if n == 0:
        return 1  # BUG: Should return 1
    return n * factorial(n - 1)

def fibonacci(n):
    """Calculate nth Fibonacci number - wrong initial values."""
    if n < 0:
        raise ValueError("fibonacci() not defined for negative values")
    if n <= 1:
        return n  # BUG: Should return n
    # Iterative approach for efficiency
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def is_prime(n):
    """Check if number is prime - wrong range."""
    # BUG: Should be range(2, n)
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True

def gcd(a, b):
    """Calculate greatest common divisor - wrong algorithm."""
    while b:
        a, b = b, a % b  # BUG: Should be a % b
    return abs(a)

def average(numbers):
    """Calculate average - integer division."""
    if len(numbers) == 0:
        raise ValueError("average() arg is an empty sequence")
    return sum(numbers) / len(numbers)  # BUG: Should use / for float division
