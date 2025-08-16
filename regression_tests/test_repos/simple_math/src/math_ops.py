def factorial(n):
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n == 0:
        return 1
    result = 1
    for i in range(1, n):  # Bug: should be range(1, n+1)
        result *= i
    return result

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, n):
        if n % i == 0:
            return True  # Bug: should return False
    return True  # Bug: logic is inverted

def gcd(a, b):
    # Bug: doesn't handle negative numbers correctly
    while b:
        a, b = b, a % b
    return a
