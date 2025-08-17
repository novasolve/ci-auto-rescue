"""
Demo file for type hints and type annotations.
"""

from typing import (
    List, Dict, Tuple, Set, Optional, Union, Any, Callable,
    TypeVar, Generic, Protocol, Literal, Final, cast, overload
)
from dataclasses import dataclass
from enum import Enum


# Basic type hints
def add_numbers(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def concatenate_strings(s1: str, s2: str) -> str:
    """Concatenate two strings."""
    return s1 + s2


def calculate_average(numbers: List[float]) -> float:
    """Calculate average of a list of numbers."""
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


# Optional and Union types
def find_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Find a user by ID, returns None if not found."""
    users = {
        1: {"name": "Alice", "age": 30},
        2: {"name": "Bob", "age": 25}
    }
    return users.get(user_id)


def process_value(value: Union[int, str]) -> str:
    """Process a value that can be either int or str."""
    if isinstance(value, int):
        return f"Number: {value}"
    return f"String: {value}"


# Type aliases
Coordinate = Tuple[float, float]
Matrix = List[List[float]]


def calculate_distance(p1: Coordinate, p2: Coordinate) -> float:
    """Calculate Euclidean distance between two points."""
    x1, y1 = p1
    x2, y2 = p2
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def transpose_matrix(matrix: Matrix) -> Matrix:
    """Transpose a matrix."""
    if not matrix:
        return []
    return [[matrix[j][i] for j in range(len(matrix))] 
            for i in range(len(matrix[0]))]


# Generic types
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


def first_element(items: List[T]) -> Optional[T]:
    """Return the first element of a list."""
    return items[0] if items else None


def merge_dicts(dict1: Dict[K, V], dict2: Dict[K, V]) -> Dict[K, V]:
    """Merge two dictionaries."""
    result = dict1.copy()
    result.update(dict2)
    return result


# Callable types
def apply_operation(
    numbers: List[float],
    operation: Callable[[float], float]
) -> List[float]:
    """Apply an operation to each number in a list."""
    return [operation(n) for n in numbers]


def create_multiplier(factor: float) -> Callable[[float], float]:
    """Create a multiplier function."""
    def multiplier(x: float) -> float:
        return x * factor
    return multiplier


# Dataclasses with type hints
@dataclass
class Point:
    x: float
    y: float
    
    def distance_to(self, other: 'Point') -> float:
        """Calculate distance to another point."""
        return ((other.x - self.x) ** 2 + (other.y - self.y) ** 2) ** 0.5


@dataclass
class Person:
    name: str
    age: int
    email: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


# Enums with type hints
class Status(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"


def process_status(status: Status) -> str:
    """Process a status enum."""
    return f"Status is: {status.value}"


# Protocol (structural subtyping)
class Drawable(Protocol):
    def draw(self) -> str:
        ...


class Circle:
    def __init__(self, radius: float):
        self.radius = radius
    
    def draw(self) -> str:
        return f"Drawing circle with radius {self.radius}"


class Square:
    def __init__(self, side: float):
        self.side = side
    
    def draw(self) -> str:
        return f"Drawing square with side {self.side}"


def render_shape(shape: Drawable) -> str:
    """Render any drawable shape."""
    return shape.draw()


# Literal types
def set_log_level(level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]) -> str:
    """Set logging level."""
    return f"Log level set to: {level}"


# Final annotation
API_VERSION: Final[str] = "1.0.0"


# Overloaded functions
@overload
def process_data(data: str) -> str: ...

@overload
def process_data(data: int) -> int: ...

@overload
def process_data(data: List[str]) -> List[str]: ...

def process_data(data: Union[str, int, List[str]]) -> Union[str, int, List[str]]:
    """Process different types of data."""
    if isinstance(data, str):
        return data.upper()
    elif isinstance(data, int):
        return data * 2
    else:  # List[str]
        return [s.upper() for s in data]


# Generic class
class Stack(Generic[T]):
    """A generic stack implementation."""
    
    def __init__(self) -> None:
        self._items: List[T] = []
    
    def push(self, item: T) -> None:
        """Push an item onto the stack."""
        self._items.append(item)
    
    def pop(self) -> T:
        """Pop an item from the stack."""
        if not self._items:
            raise IndexError("Stack is empty")
        return self._items.pop()
    
    def peek(self) -> Optional[T]:
        """Peek at the top item without removing it."""
        return self._items[-1] if self._items else None
    
    def is_empty(self) -> bool:
        """Check if the stack is empty."""
        return len(self._items) == 0


# Type casting
def safe_int_conversion(value: Any) -> Optional[int]:
    """Safely convert a value to int."""
    try:
        return cast(int, int(value))
    except (ValueError, TypeError):
        return None
