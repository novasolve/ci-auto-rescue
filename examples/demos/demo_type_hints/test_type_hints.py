"""
Test file for type hints and type annotations.
"""

import pytest
from typing import get_type_hints, List
from type_hints import (
    add_numbers, concatenate_strings, calculate_average, find_user,
    process_value, calculate_distance, transpose_matrix, first_element,
    merge_dicts, apply_operation, create_multiplier, Point, Person,
    Status, process_status, Circle, Square, render_shape, set_log_level,
    API_VERSION, process_data, Stack, safe_int_conversion
)


def test_basic_type_hints():
    """Test basic type hint functions."""
    # Test add_numbers
    assert add_numbers(5, 3) == 8
    assert add_numbers(-2, 10) == 8
    assert add_numbers(0, 0) == 0
    
    # Test concatenate_strings
    assert concatenate_strings("Hello, ", "World!") == "Hello, World!"
    assert concatenate_strings("", "Test") == "Test"
    
    # Test calculate_average
    assert calculate_average([1.0, 2.0, 3.0]) == 2.0
    assert calculate_average([5.5]) == 5.5
    assert calculate_average([]) == 0.0


def test_optional_and_union():
    """Test Optional and Union type functions."""
    # Test find_user
    user1 = find_user(1)
    assert user1 is not None
    assert user1["name"] == "Alice"
    assert user1["age"] == 30
    
    user_none = find_user(999)
    assert user_none is None
    
    # Test process_value
    assert process_value(42) == "Number: 42"
    assert process_value("hello") == "String: hello"


def test_coordinate_functions():
    """Test functions using type aliases."""
    # Test calculate_distance
    p1 = (0.0, 0.0)
    p2 = (3.0, 4.0)
    assert calculate_distance(p1, p2) == 5.0
    
    p3 = (1.0, 1.0)
    p4 = (1.0, 1.0)
    assert calculate_distance(p3, p4) == 0.0
    
    # Test transpose_matrix
    matrix = [[1, 2, 3], [4, 5, 6]]
    transposed = transpose_matrix(matrix)
    assert transposed == [[1, 4], [2, 5], [3, 6]]
    
    assert transpose_matrix([]) == []


def test_generic_functions():
    """Test generic type functions."""
    # Test first_element
    assert first_element([1, 2, 3]) == 1
    assert first_element(["a", "b", "c"]) == "a"
    assert first_element([]) is None
    
    # Test merge_dicts
    dict1 = {"a": 1, "b": 2}
    dict2 = {"b": 3, "c": 4}
    merged = merge_dicts(dict1, dict2)
    assert merged == {"a": 1, "b": 3, "c": 4}


def test_callable_functions():
    """Test functions using Callable types."""
    # Test apply_operation
    numbers = [1.0, 2.0, 3.0]
    squared = apply_operation(numbers, lambda x: x ** 2)
    assert squared == [1.0, 4.0, 9.0]
    
    # Test create_multiplier
    double = create_multiplier(2.0)
    assert double(5.0) == 10.0
    assert double(3.5) == 7.0


def test_point_dataclass():
    """Test Point dataclass."""
    p1 = Point(0.0, 0.0)
    p2 = Point(3.0, 4.0)
    
    assert p1.x == 0.0
    assert p1.y == 0.0
    assert p1.distance_to(p2) == 5.0


def test_person_dataclass():
    """Test Person dataclass."""
    # Test with all fields
    person1 = Person("Alice", 30, "alice@example.com", ["developer", "python"])
    assert person1.name == "Alice"
    assert person1.age == 30
    assert person1.email == "alice@example.com"
    assert person1.tags == ["developer", "python"]
    
    # Test with default values
    person2 = Person("Bob", 25)
    assert person2.email is None
    assert person2.tags == []


def test_status_enum():
    """Test Status enum and related functions."""
    assert process_status(Status.PENDING) == "Status is: pending"
    assert process_status(Status.ACTIVE) == "Status is: active"
    assert process_status(Status.COMPLETED) == "Status is: completed"


def test_protocol_shapes():
    """Test protocol with shapes."""
    circle = Circle(5.0)
    square = Square(4.0)
    
    assert render_shape(circle) == "Drawing circle with radius 5.0"
    assert render_shape(square) == "Drawing square with side 4.0"


def test_literal_types():
    """Test literal type function."""
    assert set_log_level("DEBUG") == "Log level set to: DEBUG"
    assert set_log_level("INFO") == "Log level set to: INFO"
    assert set_log_level("WARNING") == "Log level set to: WARNING"
    assert set_log_level("ERROR") == "Log level set to: ERROR"


def test_final_annotation():
    """Test final annotation."""
    assert API_VERSION == "1.0.0"


def test_overloaded_function():
    """Test overloaded process_data function."""
    # Test with string
    assert process_data("hello") == "HELLO"
    
    # Test with int
    assert process_data(5) == 10
    
    # Test with list of strings
    assert process_data(["hello", "world"]) == ["HELLO", "WORLD"]


def test_generic_stack():
    """Test generic Stack class."""
    # Test with integers
    int_stack = Stack[int]()
    assert int_stack.is_empty() == True
    
    int_stack.push(1)
    int_stack.push(2)
    int_stack.push(3)
    
    assert int_stack.peek() == 3
    assert int_stack.pop() == 3
    assert int_stack.pop() == 2
    assert int_stack.peek() == 1
    
    # Test with strings
    str_stack = Stack[str]()
    str_stack.push("hello")
    str_stack.push("world")
    
    assert str_stack.pop() == "world"
    assert str_stack.peek() == "hello"
    
    # Test empty stack exception
    empty_stack = Stack[int]()
    with pytest.raises(IndexError) as exc_info:
        empty_stack.pop()
    assert "Stack is empty" in str(exc_info.value)


def test_safe_int_conversion():
    """Test safe integer conversion."""
    assert safe_int_conversion("123") == 123
    assert safe_int_conversion(45.7) == 45
    assert safe_int_conversion("invalid") is None
    assert safe_int_conversion(None) is None
    assert safe_int_conversion([1, 2, 3]) is None


def test_type_hints_introspection():
    """Test that type hints are properly defined."""
    # Check add_numbers type hints
    hints = get_type_hints(add_numbers)
    assert hints['a'] == int
    assert hints['b'] == int
    assert hints['return'] == int
    
    # Check calculate_average type hints
    hints = get_type_hints(calculate_average)
    assert hints['numbers'] == List[float]
    assert hints['return'] == float
