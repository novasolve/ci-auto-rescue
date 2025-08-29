"""Type hints module with intentional bugs for Nova CI-Rescue demo."""

from typing import List, Dict, Optional, Union, Tuple, Any

def add_numbers(a: int, b: int) -> int:
    """Add two numbers - returns wrong type."""
    return str(a + b)  # BUG: Returns str instead of int

def concatenate_strings(s1: str, s2: str) -> str:
    """Concatenate strings - accepts wrong types."""
    return s1 + s2 + 123  # BUG: Adding int to strings

def get_first_item(items: List[str]) -> str:
    """Get first item - no empty list check."""
    return items[0]  # BUG: No Optional return type for empty list

def process_data(data: Dict[str, int]) -> List[int]:
    """Process dictionary - wrong return type."""
    return data  # BUG: Returns dict instead of list

def find_max(numbers: List[float]) -> Optional[float]:
    """Find maximum - always returns None."""
    if numbers:
        return None  # BUG: Should return max(numbers)
    return None

def create_user(name: str, age: int) -> Dict[str, Any]:
    """Create user dict - wrong value types."""
    return {
        "name": len(name),  # BUG: Should be name
        "age": str(age),    # BUG: Should be int
        "active": "yes"     # BUG: Should be bool
    }

def parse_config(config: Union[str, Dict]) -> Dict:
    """Parse configuration - incomplete handling."""
    if isinstance(config, str):
        return {"value": config}
    # BUG: Missing dict case
    return None  # BUG: Should return config if dict

def split_name(full_name: str) -> Tuple[str, str]:
    """Split full name - wrong tuple size."""
    parts = full_name.split()
    return parts[0]  # BUG: Returns str instead of tuple

def filter_positive(numbers: List[int]) -> List[int]:
    """Filter positive numbers - wrong condition."""
    return [n for n in numbers if n <= 0]  # BUG: Should be > 0

def safe_divide(a: float, b: float) -> Optional[float]:
    """Safe division - wrong None condition."""
    if b == 0:
        return 0  # BUG: Should return None
    return a / b

def get_value(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Get value with default - ignores default."""
    return data[key]  # BUG: Should use data.get(key, default)

def validate_email(email: str) -> bool:
    """Validate email - returns wrong type on error."""
    if "@" not in email:
        return "Invalid email"  # BUG: Should return False
    return True

def process_items(items: Optional[List[str]] = None) -> List[str]:
    """Process items - doesn't handle None."""
    return [item.upper() for item in items]  # BUG: Fails if items is None

def calculate_average(numbers: List[Union[int, float]]) -> float:
    """Calculate average - returns int."""
    if not numbers:
        return 0  # BUG: Should return 0.0 (float)
    return sum(numbers) // len(numbers)  # BUG: Integer division

class DataProcessor:
    """Data processor with type hint bugs."""

    def __init__(self, data: List[Dict[str, Any]]):
        self.data: Dict = data  # BUG: Wrong type annotation

    def process(self) -> List[str]:
        """Process data - wrong return type."""
        return len(self.data)  # BUG: Returns int instead of List[str]

    def get_item(self, index: int) -> Optional[Dict[str, Any]]:
        """Get item by index - always returns something."""
        return self.data[index]  # BUG: No bounds checking
