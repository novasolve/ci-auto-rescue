class CustomError(Exception):
    pass

def divide_numbers(a, b):
    # Bug: doesn't raise proper exception
    if b == 0:
        return None  # Should raise ZeroDivisionError or custom exception
    return a / b

def parse_number(s):
    # Bug: doesn't handle ValueError properly
    return int(s)  # Should catch and re-raise or handle

def validate_input(data):
    # Bug: raises wrong exception type
    if not isinstance(data, dict):
        raise ValueError("Input must be a dict")  # Should be TypeError
    if "required_field" not in data:
        raise Exception("Missing field")  # Should be KeyError or custom
    return True

def safe_operation(func, *args):
    # Bug: catches too broad exception
    try:
        return func(*args)
    except:  # Should catch specific exceptions
        return None
