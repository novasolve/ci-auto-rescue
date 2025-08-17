def sum_numbers(numbers):
    # Fixed: Now correctly returns the sum
    result = 0
    for n in numbers:
        result += n
    return result

def divide(a, b):
    # Fixed: Now performs true division
    return a / b