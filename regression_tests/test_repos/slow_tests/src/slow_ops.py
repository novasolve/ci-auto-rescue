import time

def slow_fibonacci(n):
    # Intentionally inefficient implementation
    if n <= 1:
        return n
    return slow_fibonacci(n-1) + slow_fibonacci(n-2)

def process_large_data(data):
    # Bug: infinite loop condition
    result = []
    i = 0
    while i < len(data):
        time.sleep(0.1)  # Simulate slow processing
        result.append(data[i] * 2)
        # Bug: forgot to increment i (causes infinite loop)
    return result

def timeout_operation(timeout_seconds):
    # This will definitely timeout
    time.sleep(timeout_seconds * 2)
    return "completed"
