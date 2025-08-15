# Nova CI-Rescue

<div align="center">
  <h3>🚀 AI-Powered Automated Test Fixing for CI/CD Pipelines</h3>
  <p><strong>v1.0 - Happy Path Edition</strong></p>
  
  [![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
  [![License](https://img.shields.io/badge/license-Proprietary-red)](LICENSE)
  [![Status](https://img.shields.io/badge/status-v1.0%20Happy%20Path-green)]()
</div>

---

## ⚠️ Important: Happy Path v1.0 Disclaimer

**Nova CI-Rescue v1.0 is optimized for the "Happy Path" - straightforward test failures with simple fixes.** This initial release is designed to handle common, single-issue test failures that can be resolved with targeted code changes.

### ✅ What Nova v1.0 CAN Do:

- Fix simple failing unit tests (TypeError, AttributeError, etc.)
- Handle single-file fixes with clear error messages
- Correct off-by-one errors, missing null checks, incorrect assertions
- Work with Python/pytest projects
- Complete fixes in 30-120 seconds for simple issues

### ❌ What Nova v1.0 CANNOT Do (Yet):

- Handle multiple complex failures simultaneously
- Fix integration tests requiring external services
- Work with non-Python languages (JavaScript/TypeScript coming soon)
- Support non-pytest frameworks
- Fix tests requiring specific environment setup or dependencies
- Handle flaky tests or race conditions
- Perform large-scale refactoring

**Expected Success Rate:** 70-85% on simple test failures, 40-50% on complex multi-file issues

---

## 🎯 Description

Nova CI-Rescue is an automated test fixing agent powered by LLM and LangGraph technology. It acts as your AI pair programmer, automatically detecting and fixing failing tests in your CI/CD pipeline. When tests fail, Nova analyzes the errors, generates targeted fixes, and verifies the solutions - all without human intervention.

## 📸 Nova in Action

<details>
<summary>🎬 Click to see Nova fixing tests in real-time</summary>

![Nova CLI Demo](docs/assets/nova-cli-demo.gif)
_Nova fixing 3 failing tests in under 2 minutes_

![PR Comment Scorecard](docs/assets/pr-comment-scorecard.png)
_Nova's automated PR comment with fix metrics_

</details>

## 🚀 Installation

### Prerequisites

- Python >= 3.10
- Git
- pytest >= 7.0.0
- OpenAI or Anthropic API key

### Install via pip

```bash
pip install nova-ci-rescue
```

### Verify Installation

```bash
nova --version
# Expected output: nova-ci-rescue v1.0.0
```

## 🎓 Quick Start Guide

### Step 1: Set Up Your API Key

```bash
# Option 1: Environment variable
export OPENAI_API_KEY="sk-..."

# Option 2: Create .env file
echo "OPENAI_API_KEY=sk-..." > .env
```

### Step 2: Try the Demo Repository

```bash
# Clone our demo repo with intentionally failing tests
git clone https://github.com/nova-solve/demo-failing-tests
cd demo-failing-tests

# See the failing tests
pytest
# Expected: 3 failed, 7 passed

# Let Nova fix them!
nova fix . --max-iters 3

# Verify all tests pass
pytest
# Expected: 10 passed, 0 failed
```

### Step 3: Use on Your Own Project

```bash
# Navigate to your project
cd /path/to/your/project

# Run Nova when tests are failing
nova fix .

# Nova will:
# 1. Detect failing tests
# 2. Analyze error messages
# 3. Generate and apply fixes
# 4. Re-run tests to verify
# 5. Report results
```

## 📊 Usage Examples

### Example 1: Simple Test Fix

```bash
# Terminal output when Nova fixes a test
$ nova fix .
🔍 Nova CI-Rescue v1.0 starting...
📋 Found 3 failing tests

Iteration 1/3:
  🧠 Planning fix for test_calculator.py::test_division
  💡 Identified issue: Missing zero division check
  🔧 Applying patch to calculator.py
  ✅ test_calculator.py::test_division now passing!

Iteration 2/3:
  🧠 Planning fix for test_calculator.py::test_negative_numbers
  💡 Identified issue: Incorrect sign handling
  🔧 Applying patch to calculator.py
  ✅ test_calculator.py::test_negative_numbers now passing!

✨ All tests fixed successfully!
📈 Metrics: 2 iterations | 42 seconds | 2 files changed | 15 lines modified
```

### Example 2: GitHub Actions Integration

```yaml
# .github/workflows/nova-autofix.yml
name: Nova Auto-Fix

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  autofix:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install Nova
        run: pip install nova-ci-rescue

      - name: Run Nova Auto-Fix
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: nova fix . --max-iters 3 --timeout 300
```

### Example 3: PR Comment Output

Nova automatically posts results to your PR:

---

### 🤖 Nova CI-Rescue Results

✅ **Successfully fixed 3/3 failing tests**

#### 📊 Metrics

| Metric         | Value |
| -------------- | ----- |
| Tests Fixed    | 3     |
| Iterations     | 2     |
| Time Taken     | 42s   |
| Files Changed  | 2     |
| Lines Modified | 15    |
| Model Used     | gpt-4 |

#### 🔧 Changes Made

1. Added zero division check in `calculator.py:45`
2. Fixed sign handling in `calculator.py:67`
3. Corrected assertion in test case

<details>
<summary>View detailed patches</summary>

```diff
--- a/calculator.py
+++ b/calculator.py
@@ -44,6 +44,8 @@ def divide(a, b):
+    if b == 0:
+        raise ValueError("Cannot divide by zero")
     return a / b
```

</details>

---

## 🎯 Interpreting Nova's Scorecard

The scorecard shows key metrics to help you understand what Nova did:

- **Tests Fixed**: Number of previously failing tests now passing
- **Iterations**: How many fix attempts Nova made
- **Time Taken**: Total runtime (typical: 30-120 seconds)
- **Files Changed**: Number of files modified (safety limit: 10)
- **Lines Modified**: Total lines added/removed (safety limit: 200)

### Success Indicators

- ✅ All tests passing
- 📈 Low iteration count (1-3)
- ⚡ Quick completion (<2 minutes)
- 📝 Minimal changes

### Warning Signs

- ⚠️ Some tests still failing
- 🔄 High iteration count (>4)
- ⏰ Timeout reached
- 📚 Large number of changes

## 🚨 What to Do When Nova Can't Fix a Test

If Nova reaches its limits without fixing all tests:

### 1. Check Nova's Analysis

```bash
# View Nova's detailed logs
cat .nova/latest/trace.jsonl | grep "reflect"

# See what patches were attempted
ls -la .nova/latest/diffs/
```

### 2. Common Reasons for Failure

| Issue                         | Solution                                             |
| ----------------------------- | ---------------------------------------------------- |
| **Complex business logic**    | Manual review needed - Nova's hints in logs can help |
| **Missing dependencies**      | Install required packages and re-run                 |
| **Environment-specific**      | Check test configuration and environment variables   |
| **Multi-file changes needed** | Increase `--max-iters` or fix manually               |
| **External service issues**   | Mock external dependencies or fix service            |

### 3. Manual Intervention Steps

```bash
# 1. Review Nova's attempted fixes
git diff HEAD~1

# 2. Check Nova's reasoning
cat .nova/latest/reports/final.xml

# 3. Apply partial fixes if helpful
git add -p  # Selectively stage Nova's good changes

# 4. Complete the fix manually
# Nova's analysis often provides valuable clues!
```

## ⚙️ Configuration

### Basic Configuration

```yaml
# nova-config.yaml
model: gpt-4
timeout: 600
max_iters: 5
max_changed_lines: 200
max_changed_files: 10

blocked_paths:
  - "*.env"
  - ".github/workflows/*"
  - "secrets/*"
```

### Advanced Settings

```bash
# Environment variables
export NOVA_MAX_ITERS=3
export NOVA_RUN_TIMEOUT_SEC=300
export NOVA_TEST_TIMEOUT_SEC=60
export NOVA_TELEMETRY_DIR=".nova"
```

## 📈 Performance Expectations

| Scenario                        | Success Rate | Avg Time | Iterations |
| ------------------------------- | ------------ | -------- | ---------- |
| Simple TypeError/AttributeError | 85-95%       | 30-60s   | 1-2        |
| Missing null checks             | 80-90%       | 45-90s   | 1-3        |
| Off-by-one errors               | 75-85%       | 60-120s  | 2-3        |
| Logic errors (single file)      | 70-80%       | 90-180s  | 2-4        |
| Multi-file issues               | 40-60%       | 120-300s | 3-6        |
| Complex integration tests       | 20-30%       | 180-600s | 4-6        |

## 🔒 Security & Safety

Nova includes multiple safety mechanisms:

- **Change Limits**: Max 200 lines, 10 files per iteration
- **Blocked Paths**: Never modifies configs, secrets, or CI files
- **Timeout Protection**: Stops after configured time limit
- **Sandboxed Execution**: Tests run in isolated environment
- **Review Required**: All changes visible in git diff

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📚 Documentation

- [Complete Documentation](docs/nova-v1-documentation.md)
- [Quickstart Guide](docs/06-quickstart-guide.md)
- [Safety & Limits](docs/safety-limits.md)
- [GitHub Actions Setup](docs/github-action-setup.md)
- [Architecture Overview](docs/02-architecture-diagram.md)

## 🆘 Getting Help

- 💬 [Discord Community](https://discord.gg/nova-solve)
- 📧 Email: support@joinnova.com
- 🐛 [GitHub Issues](https://github.com/nova-solve/ci-auto-rescue/issues)
- 📖 [Documentation](https://docs.joinnova.com)

## License

Proprietary - NovaSolve

## Author

NovaSolve (dev@novasolve.ai)
