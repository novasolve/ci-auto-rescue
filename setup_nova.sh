#!/usr/bin/env bash
set -euo pipefail

# Nova CI-Rescue Demo Setup Script
# This installs the demo version with GPT-5 and optimized settings

# Location of your repo venv (can be overridden by first argument)
VENV_DIR="${1:-.venv}"

# Path to ci-auto-rescue .env file (adjust if you move it)
ENV_FILE="$HOME/clone-repos/ci-auto-rescue/.env"

# Ensure venv exists
if [ ! -d "$VENV_DIR" ]; then
  echo "⚠️  Virtualenv $VENV_DIR not found. Creating..."
  python3 -m venv "$VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

echo "✅ Using Python: $(which python)"
echo "✅ Using Pip:    $(which pip)"

# Load .env if available
if [ -f "$ENV_FILE" ]; then
  echo "📦 Sourcing env vars from $ENV_FILE"
  # Export key=value pairs, ignore comments/blank lines
  set -a
  source "$ENV_FILE"
  set +a
else
  echo "⚠️  No .env file found at $ENV_FILE (skipping)"
fi

# Upgrade pip & wheel (quiet in CI)
if [ -n "${CI:-}" ]; then
  pip install --quiet --upgrade pip wheel
else
  pip install --upgrade pip wheel
fi

# Install demo dependencies if available
if [ -f "demo-requirements.txt" ]; then
  echo "📦 Installing demo dependencies..."
  if [ -n "${CI:-}" ]; then
    pip install --quiet -r demo-requirements.txt
  else
    pip install -r demo-requirements.txt
  fi
fi

# Install/upgrade Nova from demo branch
if [ -n "${CI:-}" ]; then
  pip install --quiet --upgrade "git+https://github.com/novasolve/ci-auto-rescue.git@demo"
else
  pip install --upgrade "git+https://github.com/novasolve/ci-auto-rescue.git@demo"
fi

# Show nova version
echo
nova version || true

# Ready to use Nova demo version!
echo
echo "✨ Nova demo version installed successfully!"
echo "   - GPT-5 model with high reasoning effort"
echo "   - Temperature set to 1.0"
echo "   - No warnings or frequency caps"
echo ""
echo "Try running: nova fix <path-to-repo> --whole-file"
