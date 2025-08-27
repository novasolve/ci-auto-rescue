# Nova CI-Rescue Demo - CI Integration Guide

This demo shows how Nova CI-Rescue can automatically fix failing tests in your CI pipeline.

## What's Included

- `setup_nova.sh` - Installs Nova and sets up the environment
- `test_nova.sh` - Basic demo that fixes a calculator bug
- `test_nova_verbose.sh` - Verbose demo that fixes a string utils validation bug
- `.github/workflows/nova-demo-ci.yml` - GitHub Actions workflow

## Running in CI

The demo is configured to run automatically in GitHub Actions:

1. **On push to main/demo branches** - Tests run automatically
2. **On pull requests** - Tests validate the fixes
3. **Manual trigger** - Use workflow_dispatch in GitHub UI

### Required Secrets

Add these secrets to your GitHub repository:
- `OPENAI_API_KEY` - For GPT models
- `ANTHROPIC_API_KEY` - For Claude models (optional)

## Running Locally

```bash
# Basic test
./test_nova.sh

# Verbose test with detailed output
./test_nova_verbose.sh
```

## How It Works

1. **Setup Phase**: Installs Nova from the demo branch with optimized settings
2. **Bug Introduction**: Intentionally breaks the code
3. **Nova Fix**: Nova analyzes failing tests and fixes the bugs
4. **Verification**: Runs tests again to confirm the fix

## CI Features

- **Cross-platform**: Works on macOS and Linux
- **Environment isolation**: Unsets conflicting env vars
- **Quiet mode**: Reduces output noise in CI
- **Parallel jobs**: Basic and verbose tests run independently
- **Summary report**: Shows test results in GitHub UI

## Example Output

```
🧪 Testing Nova CI-Rescue Demo Version
📦 Running setup_nova.sh to ensure Nova is installed...
✅ Using venv: .venv
🐛 Introducing bug in calculator.py...
🚀 Running Nova to fix ALL bugs in calculator.py...
✅ Verifying fix...
🎉 Nova successfully fixed the bug!
```
