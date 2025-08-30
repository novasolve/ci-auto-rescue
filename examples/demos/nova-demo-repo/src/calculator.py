import math
from typing import Iterable, Union, List

Number = Union[int, float]


class Calculator:
    """A simple calculator with basic arithmetic operations."""

    def add(self, a: Number, b: Number) -> Number:
        """Return the sum of a and b."""
        return a + b

    def subtract(self, a: Number, b: Number) -> Number:
        """Return the result of a minus b."""
        return a - b

    def multiply(self, a: Number, b: Number) -> Number:
        """Return the product of a and b."""
        return a * b

    def divide(self, a: Number, b: Number) -> float:
        """Return the result of a divided by b.

        Raises:
            ValueError: If b is zero.
        """
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    def power(self, a: Number, b: Number) -> Number:
        """Return a raised to the power of b."""
        return a**b

    def square_root(self, x: Number) -> float:
        """Return the square root of x.

        Raises:
            ValueError: If x is negative.
        """
        if x < 0:
            raise ValueError("Cannot calculate square root of negative number")
        return math.sqrt(x)

    def percentage(self, total: Number, percent: Number) -> float:
        """Return 'percent' percent of 'total'."""
        return (total * percent) / 100.0

    def average(self, numbers: Iterable[Number]) -> float:
        """Return the average (mean) of a sequence of numbers.

        Raises:
            ValueError: If the list is empty.
        """
        # Convert to list to allow multiple passes and len()
        nums: List[Number] = list(numbers)
        if len(nums) == 0:
            raise ValueError("Cannot calculate average of empty list")
        return sum(nums) / len(nums)
