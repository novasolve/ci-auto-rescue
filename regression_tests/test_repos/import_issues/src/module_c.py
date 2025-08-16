# Bug: missing import
def process_data(data):
    # Bug: using math.sqrt without importing math
    return [sqrt(x) for x in data]  # NameError: sqrt not defined
