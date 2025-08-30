"""
Tests for invalid inputs and error messages.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from calculator import Calculator


@pytest.fixture
def calc():
    return Calculator()


def test_average_empty_list_raises(calc):
    with pytest.raises(ValueError, match="Cannot calculate average of empty list"):
        calc.average([])


def test_average_non_numeric_raises(calc):
    with pytest.raises(ValueError, match="All elements must be numbers"):
        calc.average([1, "2", 3])
