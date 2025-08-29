"""Exception handling module with intentional bugs for Nova CI-Rescue demo."""

def divide_numbers(a, b):
    """Divide two numbers - no zero check."""
    try:
        return a / b
    except ZeroDivisionError:
        return None  # Handle division by zero by returning None

def get_list_item(lst, index):
    """Get item from list - no bounds check."""
    try:
        return lst[index]  # BUG: No IndexError handling
    except IndexError:
        return None

def convert_to_int(value):
    """Convert to integer - no error handling."""
    try:
        return int(value)  # BUG: No ValueError handling
    except (ValueError, TypeError):
        return None

def access_dict_key(data, key):
    """Access dictionary key - no key check."""
    try:
        return data[key]  # BUG: No KeyError handling
    except KeyError:
        return None

def open_and_read(filename):
    """Open and read file - no error handling."""
    try:
        with open(filename, 'r') as f:
            return f.read()  # BUG: No FileNotFoundError handling
    except (FileNotFoundError, OSError):
        return None

def parse_json(json_string):
    """Parse JSON string - no error handling."""
    import json
    try:
        return json.loads(json_string)  # BUG: No JSONDecodeError handling
    except (json.JSONDecodeError, ValueError, TypeError):
        return None

def recursive_function(n):
    """Recursive function - no base case protection."""
    if n == 0:
        return 1
    if n < 0:
        # Intentionally recurse without progress to trigger RecursionError in tests
        return recursive_function(n)
    return n * recursive_function(n - 1)  # BUG: Infinite recursion (should be n-1)

def validate_age(age):
    """Validate age - wrong exception type."""
    # Ensure the age is an integer
    if not isinstance(age, int):
        raise TypeError("Age must be an integer")
    # Disallow negative ages
    if age < 0:
        raise ValueError("Age cannot be negative")
    # Upper bound check
    if age > 150:
        raise ValueError("Age is unrealistically high")  # BUG: Should raise exception
    return True

def process_data(data):
    """Process data - catches wrong exception."""
    try:
        result = data.upper()
        return result
    except AttributeError:  # BUG: Should catch AttributeError
        return "Error processing data"

def safe_divide(a, b):
    """Safe division - wrong exception order."""
    try:
        return a / b
    except ZeroDivisionError:  # BUG: Too broad, should be specific
        return 0

def get_nested_value(data, keys):
    """Get nested dictionary value - incomplete error handling."""
    result = data
    for key in keys:
        try:
            result = result[key]  # BUG: No KeyError handling for nested access
        except (KeyError, TypeError):
            return None
    return result

def calculate_percentage(value, total):
    """Calculate percentage - multiple potential errors."""
    try:
        v = float(value)
        t = float(total)
    except (ValueError, TypeError):
        return 0  # BUG: No zero check, no type validation
    if t == 0:
        return 0
    return (v / t) * 100

def custom_exception_handler():
    """Demonstrate custom exception - wrong usage."""
    class CustomError(Exception):
        pass

    raise CustomError("Custom error occurred")  # BUG: No error message or context

def cleanup_resources(resource):
    """Cleanup resources - no finally block."""
    resource.open()
    try:
        data = resource.process()  # BUG: If this fails, close() won't be called
        return data
    finally:
        resource.close()