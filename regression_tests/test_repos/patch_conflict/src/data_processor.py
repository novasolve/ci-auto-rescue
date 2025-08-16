# Data Processor Module
# This file has specific formatting that might cause patch conflicts

def process_data(data):
    # This function has a bug
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)  # Bug: should be item * 3
    return result

def validate_data(data):
    # This function is correct
    if not isinstance(data, list):
        raise TypeError("Data must be a list")
    for item in data:
        if not isinstance(item, (int, float)):
            raise TypeError("All items must be numeric")
    return True

def transform_data(data):
    # Another function with a bug
    validated = validate_data(data)
    if validated:
        processed = process_data(data)
        # Bug: should filter out values > 100
        return processed
    return []
