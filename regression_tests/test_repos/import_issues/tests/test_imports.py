import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest

def test_function_a():
    from src.module_a import function_a
    assert function_a(5) == 8  # (5-1)*2
    
def test_function_b():
    from src.module_b import function_b
    assert function_b(5) == 18  # (5+1)*3
    
def test_module_c():
    from src.module_c import process_data
    import math
    result = process_data([4, 9, 16])
    assert result == [2.0, 3.0, 4.0]
