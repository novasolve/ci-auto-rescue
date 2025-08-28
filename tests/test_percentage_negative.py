import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculator import Calculator


def test_percentage_negative_percent_raises_value_error():
    calc = Calculator()
    with pytest.raises(ValueError, match="percent must be non-negative"):
        calc.percentage(100, -10)



