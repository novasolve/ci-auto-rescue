# Nova CI-Rescue Test Suite

A single, consolidated Python script for testing Nova's Deep Agent performance.

## ✅ What's Fixed

- **Fixed `env` parameter error** - `run_command()` now properly accepts environment variables
- **Consolidated into one file** - Single `nova_test_suite.py` instead of multiple scripts
- **Focus on Deep Agent only** - No legacy agent comparison, just tests what matters

## 🎯 Purpose

Tests Nova's Deep Agent on synthetic test scenarios to validate:
- Bug fixing capability
- Success rate across different problem types
- Performance metrics (time, iterations)

## 🚀 Quick Start

```bash
# Set your API key
export OPENAI_API_KEY='your-key-here'

# Run the test suite
python nova_test_suite.py

# With options
python nova_test_suite.py --verbose --timeout 600 --keep-files
```

## 📊 Test Scenarios

The suite creates 4 synthetic test scenarios:

1. **Simple Math** - Arithmetic operations with bugs (easy)
2. **String Operations** - Text manipulation errors (easy)  
3. **List Operations** - Array/list handling bugs (easy)
4. **Edge Cases** - Special case handling (medium)

Each scenario includes:
- Buggy implementation code
- Failing test cases
- Expected difficulty level

## 🎯 Success Criteria

- **≥70% Success Rate** - Deep Agent must fix at least 70% of scenarios
- **All Tests Fixed** - When successful, all failing tests should pass

## 📁 Output Structure

```
nova_test_run/
├── venv/                    # Isolated virtual environment
├── test_repos/              # Generated test scenarios
│   ├── simple_math/
│   ├── string_ops/
│   ├── list_ops/
│   └── edge_cases/
└── results/
    ├── test_report.md       # Human-readable report
    ├── all_results.json     # Complete test data
    └── *_result.json        # Individual scenario results
```

## 📈 Sample Output

```
============================================================
Nova CI-Rescue Deep Agent Test Suite
============================================================

Setting Up Test Environment
✅ Virtual environment created
✅ Nova installed

Creating Test Scenarios
✅ Created scenario: simple_math
✅ Created scenario: string_ops
✅ Created scenario: list_ops
✅ Created scenario: edge_cases

Running Deep Agent Tests

Testing: simple_math
Initial failing tests: 3
Running Nova Deep Agent...
✅ Success! Fixed all 3 failing tests in 2 iterations (15.3s)

Testing: string_ops
Initial failing tests: 3
Running Nova Deep Agent...
✅ Success! Fixed all 3 failing tests in 1 iterations (12.1s)

============================================================
Test Results
============================================================

## Summary Statistics
- Success Rate: 4/4 scenarios (100.0%)
- Tests Fixed: 12/12 (100.0%)
- Average Time: 13.7 seconds
- Average Iterations: 1.5

✅ Test suite PASSED! Success rate: 100.0%
```

## 🔧 Command Line Options

| Option | Description | Default |
|--------|------------|---------|
| `--verbose`, `-v` | Show detailed output and commands | False |
| `--keep-files` | Don't clean up test files after completion | False |
| `--timeout SECONDS` | Timeout for each Nova run | 300 |
| `--workspace PATH` | Path to Nova workspace | Current directory |

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
- name: Test Nova Deep Agent
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    python nova_test_suite.py
    if [ $? -ne 0 ]; then
      echo "Deep Agent tests failed"
      exit 1
    fi
```

### GitLab CI

```yaml
test-deep-agent:
  script:
    - export OPENAI_API_KEY=$OPENAI_API_KEY
    - python nova_test_suite.py
  allow_failure: false
```

## 🧪 How It Works

1. **Environment Setup**
   - Creates isolated virtual environment
   - Installs Nova from current directory
   - Sets up test directories

2. **Scenario Generation**
   - Creates synthetic repositories with bugs
   - Each has failing pytest tests
   - Covers different difficulty levels

3. **Test Execution**
   - Runs pytest to count initial failures
   - Executes Nova Deep Agent on each scenario
   - Measures success, iterations, and time

4. **Report Generation**
   - Calculates success metrics
   - Generates Markdown and JSON reports
   - Determines pass/fail based on criteria

5. **Cleanup**
   - Removes test files (unless `--keep-files`)
   - Preserves reports in results directory

## 🔍 Troubleshooting

### OPENAI_API_KEY not set
```bash
export OPENAI_API_KEY='sk-...'
```

### Module not found
Ensure you're in the Nova CI-Rescue directory when running the script.

### Permission denied
```bash
chmod +x nova_test_suite.py
```

### Timeout issues
Increase timeout for complex scenarios:
```bash
python nova_test_suite.py --timeout 600
```

## 📋 Exit Codes

- `0` - Test suite passed (≥70% success rate)
- `1` - Test suite failed or error occurred
- `130` - Interrupted by user (Ctrl+C)

## 🎯 Design Philosophy

- **Single File** - Everything in one consolidated script
- **Self-Contained** - Creates its own test scenarios
- **Reproducible** - Synthetic tests ensure consistency
- **Fast** - No need for multiple Nova versions
- **Clear Metrics** - Simple pass/fail with detailed stats

## 📝 License

Part of Nova CI-Rescue project.
