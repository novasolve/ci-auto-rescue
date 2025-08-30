#!/usr/bin/env bash
set -euo pipefail

# Nova CI-Rescue Demo Test Script - String Utils Truncate Bug
# This tests the demo version of Nova with a missing validation bug in verbose mode

# Unset potentially conflicting environment variables
unset PYTHONPATH
unset VIRTUAL_ENV
unset NOVA_API_KEY
unset NOVA_CONFIG
unset GIT_PYTHON_REFRESH

echo "🧪 Testing Nova CI-Rescue Demo Version - String Utils Bug (Verbose Mode)"
echo "======================================================================"
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

# Create a test bug in string_utils - remove validation in truncate_string
echo "🐛 Introducing validation bug in string_utils.py..."
echo "   Removing the max_length validation from truncate_string method..."

# First, let's see the current state
echo "Current truncate_string method:"
grep -A 5 "def truncate_string" src/string_utils.py || true
echo

# Remove the validation check from truncate_string method
# Use different sed syntax for macOS vs Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
  sed -i '' '/def truncate_string/,/return text\[:max_length/{
      /if max_length <= 0:/d
      /raise ValueError/d
  }' src/string_utils.py

  # Since there's no validation in the original, let's modify the method to not handle zero/negative length
  sed -i '' 's/if len(text) <= max_length:/# BUG: Missing validation for max_length/' src/string_utils.py
else
  sed -i '/def truncate_string/,/return text\[:max_length/{
      /if max_length <= 0:/d
      /raise ValueError/d
  }' src/string_utils.py

  # Since there's no validation in the original, let's modify the method to not handle zero/negative length
  sed -i 's/if len(text) <= max_length:/# BUG: Missing validation for max_length/' src/string_utils.py
fi

echo "Modified truncate_string method:"
grep -A 5 "def truncate_string" src/string_utils.py || true
echo

# Run Nova to fix it in verbose mode
# Target the specific test that checks zero length validation
echo "🚀 Running Nova in VERBOSE mode to fix the string utils bug..."
echo "   Targeting: tests/test_string_utils.py::TestStringProcessor::test_truncate_string_zero_length"
echo
nova fix . --verbose --pytest-args "tests/test_string_utils.py::TestStringProcessor::test_truncate_string_zero_length"

# Check if the specific test passes
echo
echo "✅ Verifying fix..."
pytest tests/test_string_utils.py::TestStringProcessor::test_truncate_string_zero_length -v

echo
echo "🎉 Nova successfully fixed the string utils validation bug!"
