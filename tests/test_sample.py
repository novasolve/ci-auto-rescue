"""
Sample tests with intentional failures for demonstrating Nova CI-Rescue.
"""

def test_passing():
    """This test passes."""
    assert 1 + 1 == 2

def test_simple_assertion_failure():
    """This test has a simple assertion failure."""
    result = 2 + 2
    assert result == 5, f"Expected 5 but got {result}"

def test_division_by_zero():
    """This test has a division by zero error."""
    numerator = 10
    denominator = 0
    result = numerator / denominator  # This will raise ZeroDivisionError
    assert result == 0

def test_undefined_variable():
    """This test references an undefined variable."""
    result = undefined_var + 5  # NameError
    assert result == 10

def test_list_index_error():
    """This test has an index out of bounds error."""
    my_list = [1, 2, 3]
    value = my_list[10]  # IndexError
    assert value == 4

def test_type_error():
    """This test has a type error."""
    result = "string" + 5  # TypeError: can't concatenate str and int
    assert result == "string5"
