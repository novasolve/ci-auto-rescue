# Bug: importing from wrong module
from .module_a import helper_a  # Creates circular dependency

def function_b(x):
    return helper_a(x) * 3

def helper_b(x):
    return x - 1
