# Bug: importing from wrong module
from .module_b import helper_b  # Creates circular dependency

def function_a(x):
    return helper_b(x) * 2

def helper_a(x):
    return x + 1
