#!/bin/bash
# Setup a clean demo environment for Nova CI-Rescue

echo "🔧 Setting up demo environment..."

# Create demo directory
rm -rf nova_demo_workspace 2>/dev/null
mkdir -p nova_demo_workspace
cd nova_demo_workspace

# Initialize git repo
git init -q

# Create a simple Python module with intentional bugs
cat > calculator.py << 'EOF'
def add(a, b):
    """Add two numbers - has a bug!"""
    return a + b - 1  # Bug: subtracts 1

def multiply(a, b):
    """Multiply two numbers - has a bug!"""
    return a + b  # Bug: adds instead of multiplying

def divide(a, b):
    """Divide two numbers - missing error handling!"""
    return a / b  # Bug: no zero check
EOF

# Create tests that will fail
cat > test_calculator.py << 'EOF'
"""Tests for calculator module."""
import pytest
from calculator import add, multiply, divide

def test_addition():
    """Test addition function."""
    assert add(2, 3) == 5, "2 + 3 should equal 5"
    assert add(10, -5) == 5, "10 + (-5) should equal 5"

def test_multiplication():
    """Test multiplication function."""
    assert multiply(3, 4) == 12, "3 * 4 should equal 12"
    assert multiply(5, 0) == 0, "5 * 0 should equal 0"

def test_division():
    """Test division function."""
    assert divide(10, 2) == 5, "10 / 2 should equal 5"
    # Should raise exception for divide by zero
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)
EOF

# Commit the buggy code
git add .
git commit -m "Initial commit with buggy calculator" -q

echo "✅ Demo environment ready at: nova_demo_workspace/"
echo ""
echo "📊 Running tests to show failures..."
python -m pytest test_calculator.py -v --tb=short 2>&1 | grep -E "(FAILED|PASSED|test_)"

echo ""
echo "Ready to run Nova CI-Rescue!"
echo "Command: nova fix nova_demo_workspace --max-iters 3 --timeout 120"
