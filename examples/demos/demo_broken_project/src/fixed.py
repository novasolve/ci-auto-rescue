"""
Fixed implementation file with bugs corrected.
"""

def divide_numbers(a, b):
    """Divide two numbers safely."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def find_max(numbers):
    """Find maximum in a list safely."""
    if not numbers:
        raise ValueError("Cannot find max of empty list")
    return max(numbers)


def concatenate_strings(str1, str2, separator=" "):
    """Concatenate two strings with a separator."""
    return f"{str1}{separator}{str2}"


def calculate_average(numbers):
    """Calculate average of numbers correctly."""
    if not numbers:
        return 0.0
    total = sum(numbers)
    count = len(numbers)
    return total / count  # Using float division


def get_first_char(text):
    """Get first character of string safely."""
    if not text:
        return ""
    return text[0]


def sort_list(items):
    """Sort a list without modifying the original."""
    return sorted(items)  # Returns a new sorted list
