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
    """Divide two numbers with proper exception handling."""
    # Validate argument types
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both arguments must be numbers")
    # Handle division by zero with a clear message
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b


def validate_age(age):
    """Validate age with custom exceptions."""
    if not isinstance(age, int):
        raise ValidationError("Age must be an integer", code="INVALID_TYPE")
    if age < 0:
        raise ValidationError("Age cannot be negative", code="NEGATIVE_AGE")
    # Consider extremely high ages unrealistic
    if age > 150:
        raise ValidationError("Age seems unrealistic", code="UNREALISTIC_AGE")
    return True


def process_data(data):
    """Process data with multiple exception types."""
    if data is None:
        raise ValueError("Data cannot be None")
    # Expect a sequence (list or tuple)
    if not isinstance(data, (list, tuple)):
        raise TypeError("Data must be a sequence")
    if len(data) == 0:
        raise ValueError("Data cannot be empty")
    result = []
    for item in data:
        if not isinstance(item, (int, float)):
            # Raise TypeError with info about the invalid item type
            raise TypeError(f"Invalid item type: {type(item).__name__}")
        result.append(item * 2)
    return result


class FileProcessor:
    """Class demonstrating exception handling in file operations."""
    
    def __init__(self, filename):
        self.filename = filename
    
    def read_file(self):
        """Read file with exception handling."""
        try:
            with open(self.filename, 'r') as f:
                return f.read()
        except FileNotFoundError:
            # Raise with a clearer message expected by tests
            raise FileNotFoundError(f"File '{self.filename}' not found")
    
    def write_file(self, content):
        """Write file with exception handling."""
        if not isinstance(content, str):
            raise TypeError("Content must be a string")
        with open(self.filename, 'w') as f:
            f.write(content)


def safe_conversion(value, target_type):
    """Safely convert value to target type."""
    if target_type == int:
        try:
            return int(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert {value!r} to int") from e
    elif target_type == float:
        try:
            return float(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert {value!r} to float") from e
    elif target_type == str:
        return str(value)
    else:
        # Unsupported target type
        raise ValueError(f"Unsupported target type: {target_type!r}")
