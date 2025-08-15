"""
Test file for mathematical operations - contains intentional failures for Nova to fix.
"""

def test_basic_arithmetic():
    """Test basic arithmetic operations."""
    # Bug: wrong operator
    result = 10 - 5  # Should be addition
    assert result == 15

def test_division():
    """Test division operations."""
    # Bug: integer division instead of float
    result = 10 // 3  # Should be / for float division
    assert result == 3.333333333333333
