"""Exception handling module with intentional bugs for Nova CI-Rescue demo."""

def divide_numbers(a, b):
    """Divide two numbers - no zero check."""
    return a / b  # BUG: No ZeroDivisionError handling

def get_list_item(lst, index):
    """Get item from list - no bounds check."""
    return lst[index]  # BUG: No IndexError handling

def convert_to_int(value):
    """Convert to integer - no error handling."""
    return int(value)  # BUG: No ValueError handling

def access_dict_key(data, key):
    """Access dictionary key - no key check."""
    return data[key]  # BUG: No KeyError handling

def open_and_read(filename):
    """Open and read file - no error handling."""
    with open(filename, 'r') as f:
        return f.read()  # BUG: No FileNotFoundError handling

def parse_json(json_string):
    """Parse JSON string - no error handling."""
    import json
    return json.loads(json_string)  # BUG: No JSONDecodeError handling

def recursive_function(n):
    """Recursive function - no base case protection."""
    if n == 0:
        return 1
    return n * recursive_function(n)  # BUG: Infinite recursion (should be n-1)

def validate_age(age):
    """Validate age - wrong exception type."""
    if age < 0:
        raise ValueError  # BUG: No error message
    if age > 150:
        return False  # BUG: Should raise exception
    return True

def process_data(data):
    """Process data - catches wrong exception."""
    try:
        result = data.upper()
        return result
    except KeyError:  # BUG: Should catch AttributeError
        return "Error processing data"

def safe_divide(a, b):
    """Safe division - wrong exception order."""
    try:
        return a / b
    except Exception:  # BUG: Too broad, should be specific
        return 0

def get_nested_value(data, keys):
    """Get nested dictionary value - incomplete error handling."""
    result = data
    for key in keys:
        result = result[key]  # BUG: No KeyError handling for nested access
    return result

def calculate_percentage(value, total):
    """Calculate percentage - multiple potential errors."""
    return (value / total) * 100  # BUG: No zero check, no type validation

def custom_exception_handler():
    """Demonstrate custom exception - wrong usage."""
    class CustomError(Exception):
        pass
    
    raise CustomError  # BUG: No error message or context

def cleanup_resources(resource):
    """Cleanup resources - no finally block."""
    resource.open()
    data = resource.process()  # BUG: If this fails, close() won't be called
    resource.close()
    return data
