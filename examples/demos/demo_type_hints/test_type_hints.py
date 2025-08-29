"""Tests for type hints - all will fail due to bugs."""

from type_hints import (
    add_numbers,
    concatenate_strings,
    get_first_item,
    process_data,
    find_max,
    create_user,
    parse_config,
    split_name,
    filter_positive,
    safe_divide,
    get_value,
    validate_email,
    process_items,
    calculate_average,
    DataProcessor,
)


def test_add_numbers_type():
    """Test add_numbers return type."""
    result = add_numbers(2, 3)
    assert isinstance(result, int)
    assert result == 5


def test_concatenate_strings():
    """Test string concatenation."""
    result = concatenate_strings("Hello, ", "World!")
    assert isinstance(result, str)
    assert result == "Hello, World!"


def test_get_first_item():
    """Test getting first item with proper handling."""
    assert get_first_item(["a", "b", "c"]) == "a"
    # Should return None for empty list
    assert get_first_item([]) is None


def test_process_data():
    """Test data processing return type."""
    data = {"a": 1, "b": 2, "c": 3}
    result = process_data(data)
    assert isinstance(result, list)
    assert result == [1, 2, 3]  # Values as list


def test_find_max():
    """Test finding maximum."""
    assert find_max([1.5, 2.7, 0.3]) == 2.7
    assert find_max([]) is None
    assert find_max([-1, -5, -3]) == -1


def test_create_user():
    """Test user creation with correct types."""
    user = create_user("John Doe", 30)
    assert user["name"] == "John Doe"
    assert isinstance(user["name"], str)
    assert user["age"] == 30
    assert isinstance(user["age"], int)
    assert user["active"] == True
    assert isinstance(user["active"], bool)


def test_parse_config():
    """Test config parsing for both types."""
    # String input
    result = parse_config("value")
    assert result == {"value": "value"}

    # Dict input
    config = {"key": "value", "num": 42}
    result = parse_config(config)
    assert result == config


def test_split_name():
    """Test name splitting."""
    first, last = split_name("John Doe")
    assert first == "John"
    assert last == "Doe"

    # Single name should return tuple with empty last
    first, last = split_name("Madonna")
    assert first == "Madonna"
    assert last == ""


def test_filter_positive():
    """Test filtering positive numbers."""
    numbers = [-2, -1, 0, 1, 2, 3]
    result = filter_positive(numbers)
    assert result == [1, 2, 3]


def test_safe_divide():
    """Test safe division."""
    assert safe_divide(10, 2) == 5.0
    assert safe_divide(7, 2) == 3.5
    assert safe_divide(10, 0) is None


def test_get_value():
    """Test getting value with default."""
    data = {"name": "John", "age": 30}
    assert get_value(data, "name") == "John"
    assert get_value(data, "email", "none@example.com") == "none@example.com"


def test_validate_email():
    """Test email validation return type."""
    assert validate_email("user@example.com") is True
    assert validate_email("invalid") is False
    # Check return type is always bool
    assert isinstance(validate_email("test"), bool)


def test_process_items():
    """Test processing optional items."""
    assert process_items(["hello", "world"]) == ["HELLO", "WORLD"]
    assert process_items(None) == []
    assert process_items([]) == []


def test_calculate_average():
    """Test average calculation returns float."""
    result = calculate_average([1, 2, 3, 4])
    assert isinstance(result, float)
    assert result == 2.5

    result = calculate_average([])
    assert isinstance(result, float)
    assert result == 0.0


class TestDataProcessor:
    """Test DataProcessor class."""

    def test_init_type(self):
        """Test initialization with correct type."""
        data = [{"id": 1}, {"id": 2}]
        processor = DataProcessor(data)
        assert isinstance(processor.data, list)

    def test_process_return_type(self):
        """Test process method return type."""
        data = [{"name": "item1"}, {"name": "item2"}]
        processor = DataProcessor(data)
        result = processor.process()
        assert isinstance(result, list)
        assert all(isinstance(item, str) for item in result)

    def test_get_item_bounds(self):
        """Test get_item with bounds checking."""
        data = [{"id": 1}, {"id": 2}]
        processor = DataProcessor(data)
        assert processor.get_item(0) == {"id": 1}
        assert processor.get_item(10) is None  # Out of bounds
