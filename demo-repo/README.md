# Nova CI-Rescue Demo Repository

This repository demonstrates Nova CI-Rescue in action. It contains a simple Python calculator module with deliberately failing tests that Nova CI-Rescue can automatically fix.

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- An LLM API key (OpenAI or Anthropic)
- Nova CI-Rescue installed (`pip install nova-ci-rescue`)

### Repository Structure

```
demo-repo/
├── src/
│   └── calc.py           # Calculator module with intentional bugs
├── tests/
│   └── test_calc.py       # Test suite that will fail initially
├── .github/
│   └── workflows/
│       └── nova.yml       # GitHub Actions workflow for automated fixes
└── README.md              # This file
```

## 🔧 Running Nova CI-Rescue Locally

### Step 1: Set up the environment

```bash
# Clone this demo repository
git clone <repo-url>
cd demo-repo

# Install dependencies
pip install pytest nova-ci-rescue

# Set your LLM API key
export OPENAI_API_KEY="your-api-key-here"
# OR
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Step 2: Verify the tests are failing

```bash
# Run tests to see the failures
pytest tests/
```

You should see multiple test failures:

- `test_addition` fails because `add()` returns `a - b` instead of `a + b`
- `test_multiplication` fails because `multiply()` returns `a + b` instead of `a * b`
- `test_division` fails because `divide()` uses integer division instead of float division

### Step 3: Run Nova CI-Rescue

```bash
# Run Nova to automatically fix the failing tests
nova fix .

# You can also specify options:
nova fix . --max-iters 5 --timeout 300 --verbose
```

Nova will:

1. 🔍 Discover the failing tests
2. 🤔 Analyze the test failures and source code
3. 🔧 Generate patches to fix the bugs
4. ✅ Apply the patches and verify tests pass
5. 📝 Create a fix branch with the changes

### Step 4: Verify the fixes

```bash
# Run tests again - they should all pass now!
pytest tests/

# Check what changes Nova made
git diff
```

## 🤖 GitHub Actions Integration

This repository includes a GitHub Actions workflow that automatically runs Nova CI-Rescue when tests fail.

### Setup

1. **Add API Key Secret**:

   - Go to Settings → Secrets and variables → Actions
   - Add a secret named `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

2. **Enable GitHub Actions**:

   - Go to Actions tab
   - Enable workflows for this repository

3. **Create a Pull Request**:
   - Make any change that causes tests to fail
   - Open a pull request
   - Nova will automatically run and attempt to fix the tests
   - If successful, it will commit the fixes to your PR

### Workflow Features

- **Automatic Triggering**: Runs on PRs and pushes to main/develop
- **Smart Detection**: Only runs Nova if tests are actually failing
- **Fix Commits**: Automatically commits fixes back to the PR
- **Status Reports**: Posts check runs and PR comments with results
- **Safety Limits**: Configured with reasonable timeouts and iteration limits

## 📊 Understanding Nova's Output

When Nova runs, it provides detailed information about its process:

### Console Output

```
Nova CI-Rescue 🚀
Repository: /path/to/demo-repo
Max iterations: 5
Timeout: 300s

🔍 Discovering failing tests...
Found 3 failing test(s):
┌─────────────────────┬──────────────────┬─────────────────┐
│ Test Name           │ Location         │ Error           │
├─────────────────────┼──────────────────┼─────────────────┤
│ test_addition       │ test_calc.py:15  │ assert 5 == -1  │
│ test_multiplication │ test_calc.py:21  │ assert 12 == 7  │
│ test_division       │ test_calc.py:27  │ assert 5.0 == 5 │
└─────────────────────┴──────────────────┴─────────────────┘

━━━ Iteration 1/5 ━━━
📋 Planning fix strategy...
🔧 Generating patch...
✓ Patch approved by critic
📝 Applying patch...
🧪 Running tests...
✅ All tests passing!
```

### Artifacts

Nova creates a `.nova/` directory with detailed logs and artifacts:

```
.nova/
└── 20250814-163320/     # Timestamp of the run
    ├── trace.jsonl      # Detailed execution trace
    ├── patches/         # Generated patches
    │   └── patch_1.diff
    ├── test_results/    # Test results after each iteration
    │   ├── before.xml
    │   └── after_1.xml
    └── reports/
        └── summary.md   # Run summary report
```

## 🛡️ Safety Features

Nova CI-Rescue includes several safety features to prevent unintended changes:

- **File Limits**: Won't modify more than 10 files in a single run
- **Line Limits**: Patches are limited to 500 lines of changes
- **Protected Files**: Won't modify CI configs, build files, or documentation
- **Timeout Protection**: Stops after the configured timeout (default: 20 minutes)
- **Iteration Limits**: Stops after max iterations (default: 6)

## 🧪 Experimenting with Nova

Try these experiments to see Nova in action:

### 1. Break Different Things

- Modify `calc.py` to introduce new bugs
- Add new test cases that fail
- See how Nova adapts to different failure patterns

### 2. Complex Scenarios

- Add multiple related bugs
- Create test dependencies
- Introduce edge cases

### 3. Configuration Options

- Adjust `--max-iters` to control fix attempts
- Use `--verbose` for detailed output
- Try different LLM models via config

## 📖 Documentation

For more information about Nova CI-Rescue:

- [Main Documentation](../docs/README.md)
- [Quickstart Guide](../docs/06-quickstart-guide.md)
- [Safety Limits](../docs/safety-limits.md)
- [GitHub Integration](../docs/github-action-setup.md)

## 🤝 Contributing

This is a demo repository for Nova CI-Rescue. To contribute to Nova itself:

- Report issues at [Nova CI-Rescue Issues](https://github.com/nova-ci-rescue/issues)
- See the main repository for contribution guidelines

## 📄 License

This demo repository is provided as-is for demonstration purposes.
Nova CI-Rescue is proprietary software - see the main repository for license details.

---

**Note**: This demo intentionally contains bugs to showcase Nova's capabilities. In a real project, you would not deliberately introduce bugs! 😄
