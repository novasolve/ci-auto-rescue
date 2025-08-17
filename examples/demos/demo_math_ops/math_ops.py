def sum_numbers(numbers):
    # Bug: Incorrectly returns the product instead of the sum
    result = 1
    for n in numbers:
        result *= n
    return result

def divide(a, b):
    # Bug: Performs integer division instead of true division
    return a // b
