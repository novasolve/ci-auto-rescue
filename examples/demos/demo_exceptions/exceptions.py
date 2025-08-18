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
    # Validate types
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both arguments must be numbers")
    # Handle division by zero with custom message
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b


def validate_age(age):
    """Validate age with custom exceptions (intentionally buggy)."""
    if not isinstance(age, int):
        raise ValidationError("Age must be an integer", code="INVALID_TYPE")
    if age < 0:
        raise ValidationError("Age cannot be negative", code="NEGATIVE_AGE")
    if age > 150:
        raise ValidationError("Age seems unrealistic", code="UNREALISTIC_AGE")
    return True


def process_data(data):
    """Process data with multiple exception types (intentionally buggy)."""
    if data is None:
        raise ValueError("Data cannot be None")
    if not isinstance(data, (list, tuple)):
        raise TypeError("Data must be a sequence")
    if len(data) == 0:
        raise ValueError("Data cannot be empty")
    result = []
    for item in data:
        if not isinstance(item, (int, float)):
            raise TypeError(f"Invalid item type: {type(item).__name__}")
        result.append(item * 2)
    return result


class FileProcessor:
    """Class demonstrating exception handling in file operations (intentionally buggy)."""
    
    def __init__(self, filename):
        self.filename = filename
    
    def read_file(self):
        """Read file with exception handling (intentionally buggy)."""
        try:
            with open(self.filename, 'r') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File '{self.filename}' not found")
    
    def write_file(self, content):
        """Write file with exception handling (intentionally buggy)."""
        if not isinstance(content, str):
            raise TypeError("Content must be a string")
        with open(self.filename, 'w') as f:
            f.write(content)


def safe_conversion(value, target_type):
    """Safely convert value to target type (intentionally buggy)."""
    if target_type == int:
        try:
            return int(value)
        except (ValueError, TypeError):
            raise ValueError(f"Cannot convert '{value}' to int")
    elif target_type == float:
        try:
            return float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Cannot convert '{value}' to float")
    elif target_type == str:
        return str(value)
    else:
        raise ValueError(f"Unsupported target type: {target_type}")
