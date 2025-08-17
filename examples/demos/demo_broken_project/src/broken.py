"""
Broken implementation file with intentional bugs for demonstration.
"""

def divide_numbers(a, b):
    """Divide two numbers (has a bug: no zero check)."""
    return a / b  # Bug: will crash if b is 0


def find_max(numbers):
    """Find maximum in a list (has a bug: doesn't handle empty lists)."""
    return max(numbers)  # Bug: will crash if numbers is empty


def concatenate_strings(str1, str2):
    """Concatenate two strings (has a bug: missing space)."""
    return str1 + str2  # Bug: no space between strings


def calculate_average(numbers):
    """Calculate average of numbers (has a bug: integer division)."""
    total = sum(numbers)
    count = len(numbers)
    return total // count  # Bug: using integer division instead of float


def get_first_char(text):
    """Get first character of string (has a bug: no empty check)."""
    return text[0]  # Bug: will crash if text is empty


def sort_list(items):
    """Sort a list (has a bug: modifies original list)."""
    items.sort()  # Bug: modifies the original list
    return items
