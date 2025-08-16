# Nova CI-Rescue Deep Agent Test Suite

A streamlined test suite for validating Nova's Deep Agent performance - no legacy comparison, just pure Deep Agent testing.

## Key Differences from Previous Approaches

### Their Code (Complex)
- Assumes separate `nova_v1_0` and `nova_v1_1` installations
- Requires YAML config with real repositories
- Complex metrics and regression detection
- Focuses on v1.0 vs v1.1 comparison

### Our Code (Simple)
- **Single Nova installation** - just the latest version
- **No legacy agent** - only tests Deep Agent
- **Self-contained** - creates test scenarios on the fly
- **Simple metrics** - success rate, tests fixed, time

## What This Tests

The Deep Agent is tested on various synthetic scenarios:

1. **Simple Math** - Basic arithmetic bugs
2. **String Operations** - Text manipulation errors  
3. **List Operations** - Array handling issues
4. **Edge Cases** - Error handling and special cases

## Usage

```bash
# Set your API key
export OPENAI_API_KEY='your-key-here'

# Run the test suite
python nova_deep_agent_test.py

# With options
python nova_deep_agent_test.py --verbose --timeout 600
```

## Success Criteria

- ✅ **70% Success Rate** - Deep Agent should fix at least 70% of scenarios
- ✅ **All Tests Fixed** - When successful, all failing tests should be fixed

## Output

```
============================================================
Nova CI-Rescue Deep Agent Test Suite
============================================================

✅ Virtual environment created
✅ Nova installed

Testing: simple_math
Description: Simple arithmetic bugs
Initial failing tests: 3
Running Nova Deep Agent...
✅ Success! Fixed all 3 failing tests in 2 iterations (15.3s)

Testing: string_ops
Description: String manipulation bugs
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
```

## Files Generated

```
nova_test_run/
├── venv/                    # Virtual environment
├── test_repos/              # Generated test scenarios
│   ├── simple_math/
│   ├── string_ops/
│   ├── list_ops/
│   └── edge_cases/
└── results/
    ├── test_report.md       # Human-readable report
    ├── all_results.json     # Complete test data
    └── *_result.json        # Individual test results
```

## Why This Approach?

1. **Focus on What Matters** - Tests the actual Deep Agent, not legacy comparisons
2. **Simplicity** - One script, one Nova version, clear results
3. **Reproducible** - Synthetic tests ensure consistent benchmarking
4. **Fast** - No need to maintain multiple Nova versions

## Integration with CI/CD

```yaml
# GitHub Actions
- name: Test Deep Agent
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    python nova_deep_agent_test.py
    if [ $? -ne 0 ]; then
      echo "Deep Agent tests failed"
      exit 1
    fi
```

## Command Line Options

- `--verbose`: Show detailed output
- `--keep-files`: Don't clean up test files
- `--timeout N`: Set timeout per test (default: 300s)
- `--workspace PATH`: Nova workspace location

This is the simplest, most focused approach to testing Nova's Deep Agent!
