#!/usr/bin/env bash
set -euo pipefail

# Nova CI-Rescue Demo Test Script
# This tests the demo version of Nova with a simple broken calculator

# Unset potentially conflicting environment variables
unset PYTHONPATH
unset VIRTUAL_ENV
unset NOVA_API_KEY
unset NOVA_CONFIG
unset GIT_PYTHON_REFRESH

echo "🧪 Testing Nova CI-Rescue Demo Version"
echo "======================================"
echo

# Use consistent venv directory
VENV_DIR=".venv"

# Always run setup to ensure Nova is installed and up-to-date
if [ -f "setup_nova.sh" ]; then
  echo "📦 Running setup_nova.sh to ensure Nova is installed..."
  bash setup_nova.sh "$VENV_DIR"
  echo
else
  echo "❌ setup_nova.sh not found!"
  exit 1
fi

# Activate venv
if [ -d "$VENV_DIR" ]; then
  source "$VENV_DIR/bin/activate"
  echo "✅ Using venv: $VENV_DIR"
else
  echo "❌ Failed to create venv!"
  exit 1
fi

# Verify Nova is available
if ! command -v nova &> /dev/null; then
  echo "❌ Nova command not found after setup!"
  exit 1
fi

echo "Nova version:"
nova version 2>/dev/null || echo "Nova CI-Rescue (demo version)"
echo

# Create test bugs in ALL calculator functions
echo "🐛 Introducing bugs in ALL calculator.py functions..."
# Use different sed syntax for macOS vs Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
  # Add bug: multiply instead of add
  sed -i '' 's/return a + b/return a * b  # BUG: Using multiplication instead of addition/' src/calculator.py
  # Subtract bug: add instead of subtract
  sed -i '' 's/return a - b/return a + b  # BUG: Using addition instead of subtraction/' src/calculator.py
  # Multiply bug: add instead of multiply
  sed -i '' 's/return a \* b/return a + b  # BUG: Using addition instead of multiplication/' src/calculator.py
  # Divide bug: subtract instead of divide
  sed -i '' 's/return a \/ b/return a - b  # BUG: Using subtraction instead of division/' src/calculator.py
  # Power bug: multiply instead of power
  sed -i '' 's/return a \*\* b/return a * b  # BUG: Using multiplication instead of power/' src/calculator.py
  # Square root bug: return number instead of sqrt
  sed -i '' 's/return math.sqrt(a)/return a  # BUG: Returning number instead of square root/' src/calculator.py
  # Percentage bug: wrong calculation
  sed -i '' 's/return (a \* b) \/ 100/return a + b  # BUG: Wrong percentage calculation/' src/calculator.py
  # Average bug: return sum instead of average
  sed -i '' 's/return sum(numbers) \/ len(numbers)/return sum(numbers)  # BUG: Returning sum instead of average/' src/calculator.py
else
  # Add bug: multiply instead of add
  sed -i 's/return a + b/return a * b  # BUG: Using multiplication instead of addition/' src/calculator.py
  # Subtract bug: add instead of subtract
  sed -i 's/return a - b/return a + b  # BUG: Using addition instead of subtraction/' src/calculator.py
  # Multiply bug: add instead of multiply
  sed -i 's/return a \* b/return a + b  # BUG: Using addition instead of multiplication/' src/calculator.py
  # Divide bug: subtract instead of divide
  sed -i 's/return a \/ b/return a - b  # BUG: Using subtraction instead of division/' src/calculator.py
  # Power bug: multiply instead of power
  sed -i 's/return a \*\* b/return a * b  # BUG: Using multiplication instead of power/' src/calculator.py
  # Square root bug: return number instead of sqrt
  sed -i 's/return math.sqrt(a)/return a  # BUG: Returning number instead of square root/' src/calculator.py
  # Percentage bug: wrong calculation
  sed -i 's/return (a \* b) \/ 100/return a + b  # BUG: Wrong percentage calculation/' src/calculator.py
  # Average bug: return sum instead of average
  sed -i 's/return sum(numbers) \/ len(numbers)/return sum(numbers)  # BUG: Returning sum instead of average/' src/calculator.py
fi

# Run Nova to fix it (whole-file is now default, no need to specify)
echo "🚀 Running Nova to fix ALL bugs in calculator.py..."
echo
nova fix . --pytest-args "tests/test_calculator.py"

# Check if tests pass
echo
echo "✅ Verifying fix..."
pytest tests/ -v

echo
echo "🎉 Nova successfully fixed ALL the bugs in calculator.py!"