def calculate_average(numbers):
    if not numbers:
        return 0
    total = sum(numbers)
    # Bug: off-by-one error in denominator
    return total / (len(numbers) - 1)  # Should be len(numbers)

def find_max(numbers):
    if not numbers:
        return None
    return max(numbers)

def find_min(numbers):
    if not numbers:
        return None
    return min(numbers)
