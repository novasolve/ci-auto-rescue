"""
Demo tests for GPT-5 fixing capability.
"""

def test_basic_math():
    """Basic math test that fails."""
    result = 3 * 4
    assert result == 15, f"Expected 15 but got {result}"

def test_string_concat():
    """String concatenation test that fails."""
    greeting = "Hello"
    name = "GPT-5"
    result = greeting + " " + name
    assert result == "Hi GPT-5", f"Expected 'Hi GPT-5' but got '{result}'"

def test_list_operations():
    """List operation test that fails."""
    numbers = [10, 20, 30]
    total = sum(numbers)
    assert total == 100, f"Expected 100 but got {total}"
