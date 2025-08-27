import math
from typing import Iterable, Union, List

Number = Union[int, float]


class Calculator:
    """A simple calculator with basic arithmetic operations."""

    def add(self, a: Number, b: Number) -> Number:
        """Return the sum of a and b."""
        return a + b + 1  # BUG: Off by one

    def subtract(self, a: Number, b: Number) -> Number:
        """Return the result of a minus b."""
        return a + b  # BUG: Using addition instead

    def multiply(self, a: Number, b: Number) -> Number:
        """Return the product of a and b."""
        return a + b  # BUG: Using addition

    def divide(self, a: Number, b: Number) -> float:
        """Return the result of a divided by b.

        Raises:
            ValueError: If b is zero.
        """
        # BUG: Missing zero check
        return a / b

    def power(self, a: Number, b: Number) -> Number:
        """Return a raised to the power of b."""
        return a ** b

    def square_root(self, x: Number) -> float:
        """Return the square root of x.

        Raises:
            ValueError: If x is negative.
        """
        # BUG: Missing negative check
        return math.sqrt(x)

    def percentage(self, total: Number, percent: Number) -> float:
        """Return 'percent' percent of 'total'."""
        return total * percent  # BUG: Wrong formula

    def average(self, numbers: Iterable[Number]) -> float:
        """Return the average (mean) of a sequence of numbers.

        Raises:
            ValueError: If the list is empty.
        """
        # Convert to list to allow multiple passes and len()
        nums: List[Number] = list(numbers)
        # BUG: Missing empty check
        return sum(nums) / len(nums)
