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


# Ensure Python symlink exists (fix for macOS Python version issues)
if [ -d "$VENV_DIR" ] && [ ! -e "$VENV_DIR/bin/python3.12" ]; then
  PYTHON_VERSION=$(python3 -c 'import sys; print(f"python{sys.version_info.major}.{sys.version_info.minor}")')
  if [ -e "$VENV_DIR/bin/$PYTHON_VERSION" ]; then
    ln -sf "$PYTHON_VERSION" "$VENV_DIR/bin/python3.12"
  fi
fi

# Activate venv
source "$VENV_DIR/bin/activate"

echo "✅ Using Python: $(which python)"
echo "✅ Using Pip:    $(which pip)"

# Remove pyenv shim for nova if present in PATH
if command -v nova &>/dev/null; then
  NOVA_PATH="$(command -v nova)"
  if [[ "$NOVA_PATH" == *".pyenv/shims/nova"* ]]; then
    echo "⚠️  Removing pyenv shim for nova from PATH for this session."
    # Remove pyenv shims from PATH for this session
    export PATH="$(echo "$PATH" | tr ':' '\n' | grep -v '\.pyenv/shims' | paste -sd: -)"
    hash -r
  fi
fi

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
  pip install openai
else
  pip install --upgrade pip wheel
fi

# Uninstall any existing nova first to ensure clean install
pip uninstall -y nova nova-ci-rescue 2>/dev/null || true

# Install/upgrade Nova from demo branch (force reinstall, no cache)
if [ -n "${CI:-}" ]; then
  pip install --quiet --force-reinstall --no-cache-dir "git+https://github.com/novasolve/nova-ci-rescue.git@demo/latest"
else
  pip install --force-reinstall --no-cache-dir "git+https://github.com/novasolve/nova-ci-rescue.git@demo/latest"
fi

# Show nova version (ensure using venv's nova)
echo
if [ -x "$VENV_DIR/bin/nova" ]; then
  "$VENV_DIR/bin/nova" version || true
else
  nova version || true
fi

# Ready to use Nova demo version!
# echo
# echo "✨ Nova demo version installed successfully!"
# echo "   - GPT-5 model with high reasoning effort"
# echo "   - Temperature set to 1.0"
# echo "   - No warnings or frequency caps"
# echo ""
# echo "Try running: nova fix <path-to-repo> --whole-file"
