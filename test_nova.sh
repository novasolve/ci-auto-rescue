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

# Create a test bug in calculator
echo "🐛 Introducing bug in calculator.py..."
# Use different sed syntax for macOS vs Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
  sed -i '' 's/return a - b/return a + b  # BUG: Using addition instead of subtraction/' src/calculator.py
else
  sed -i 's/return a - b/return a + b  # BUG: Using addition instead of subtraction/' src/calculator.py
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
echo "🎉 Nova successfully fixed the bug!"