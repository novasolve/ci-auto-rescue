#!/bin/bash

# run_static_checks.sh – Run linters and security analysis

set -e  # Exit on first error

echo "🔍 Running static analysis checks..."

# Check if tools are installed
command -v flake8 >/dev/null 2>&1 || { echo "Error: flake8 not installed. Run: pip install flake8"; exit 1; }
command -v bandit >/dev/null 2>&1 || { echo "Error: bandit not installed. Run: pip install bandit"; exit 1; }
command -v pip-audit >/dev/null 2>&1 || { echo "Error: pip-audit not installed. Run: pip install pip-audit"; exit 1; }

# Run flake8 linter for code style issues
echo "📝 Running flake8..."
flake8 src tests --max-line-length=120 --extend-ignore=E203,W503 || { 
    echo "❌ Lint errors detected"; 
    exit 1; 
}
echo "✅ Linting passed"

# Run bandit for security vulnerabilities
echo "🔒 Running bandit security analysis..."
bandit -ll -r src --format json -o bandit-report.json || true
bandit -ll -r src || { 
    echo "❌ Security issues detected by bandit"; 
    exit 1; 
}
echo "✅ Security analysis passed"

# Run pip-audit for dependency vulnerabilities
echo "📦 Running pip-audit for dependency checks..."
pip-audit || { 
    echo "❌ Vulnerable dependencies found"; 
    exit 1; 
}
echo "✅ Dependency audit passed"

echo "✅ All static analysis checks passed successfully!"
