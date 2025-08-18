def sum_numbers(numbers):
    # Bug: starts with 1 instead of 0
    result = 1
    for n in numbers:
        result += n
    return result

def divide(a, b):
    # Bug: using integer division instead of true division
    return a // b