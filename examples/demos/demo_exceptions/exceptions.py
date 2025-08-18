"""
Demo file for exception handling.
"""

class CustomError(Exception):
    """Custom exception class for demo purposes."""
    pass


class ValidationError(Exception):
    """Exception raised for validation errors."""
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


def divide_numbers(a, b):
    """Divide two numbers with proper exception handling (intentionally buggy)."""
    return a / b


def validate_age(age):
    """Validate age with custom exceptions (intentionally buggy)."""
    return True


def process_data(data):
    """Process data with multiple exception types (intentionally buggy)."""
    result = []
    for item in data:
        result.append(item * 2)
    return result


class FileProcessor:
    """Class demonstrating exception handling in file operations (intentionally buggy)."""
    
    def __init__(self, filename):
        self.filename = filename
    
    def read_file(self):
        """Read file with exception handling (intentionally buggy)."""
        with open(self.filename, 'r') as f:
            return f.read()
    
    def write_file(self, content):
        """Write file with exception handling (intentionally buggy)."""
        with open(self.filename, 'w') as f:
            f.write(content)


def safe_conversion(value, target_type):
    """Safely convert value to target type (intentionally buggy)."""
    if target_type == int:
        return int(value)
    elif target_type == float:
        return float(value)
    elif target_type == str:
        return str(value)
    else:
        return target_type(value)