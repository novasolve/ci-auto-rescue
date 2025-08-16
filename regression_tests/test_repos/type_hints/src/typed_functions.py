from typing import List, Dict, Optional, Union

def add_numbers(a: int, b: int) -> int:
    # Bug: returns float for division
    return (a + b) / 2  # Should return (a + b) or use // for int division

def process_list(items: List[int]) -> List[str]:
    # Bug: returns List[int] not List[str]
    return [x * 2 for x in items]  # Should convert to strings

def get_value(data: Dict[str, int], key: str) -> Optional[int]:
    # Bug: doesn't handle missing key properly
    return data[key]  # Should use data.get(key)

def combine_values(x: Union[int, str], y: Union[int, str]) -> str:
    # Bug: doesn't handle all type combinations
    return x + y  # Will fail if types don't match
