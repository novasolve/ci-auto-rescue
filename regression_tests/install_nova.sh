#!/bin/bash
# Install Nova in the virtual environments

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "Installing Nova in virtual environments..."

# Install Nova v1.0 (uses --legacy-agent flag)
if [ -d "venvs/nova_v1_0" ]; then
    echo "Installing Nova in v1.0 environment..."
    venvs/nova_v1_0/bin/pip install -e ../
else
    echo "v1.0 environment not found. Run setup_simple.py first."
fi

# Install Nova v1.1 (uses Deep Agent by default)
if [ -d "venvs/nova_v1_1" ]; then
    echo "Installing Nova in v1.1 environment..."
    venvs/nova_v1_1/bin/pip install -e ../
else
    echo "v1.1 environment not found. Run setup_simple.py first."
fi

echo "Done!"
echo ""
echo "To run regression tests:"
echo "  export OPENAI_API_KEY='your-key-here'"
echo "  python nova_runner_wrapper.py test_repos/simple_math --version both"