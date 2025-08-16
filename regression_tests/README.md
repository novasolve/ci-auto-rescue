# Nova CI-Rescue v1.1 Deep Agent Integration - Regression Test Suite

## Overview

This comprehensive regression test suite validates Nova CI-Rescue v1.1 (with Deep Agent integration) against v1.0 (legacy agent) to ensure the new version meets or exceeds performance requirements without introducing regressions.

## 🎯 Success Criteria

The v1.1 Deep Agent must meet ALL of the following criteria:

1. **≥70% fix success rate** on failing tests
2. **Equal or better performance** on all test repositories compared to v1.0
3. **No regressions** (no repo where v1.1 fails but v1.0 succeeds)
4. **Graceful edge case handling** (no crashes/hangs in tricky scenarios)
5. **Stable operation** with <5% error rate

## 📁 Directory Structure

```
regression_tests/
├── regression_orchestrator.py      # Main test orchestrator
├── test_repos.yaml                # Test repository configuration
├── regression_report_generator.py  # Report generation utilities
├── edge_case_generator.py          # Creates test repositories
├── setup_environments.py           # Cross-platform environment setup
├── setup_environments.sh           # Unix environment setup script
├── nova_runner_wrapper.py          # Version compatibility wrapper
├── validate_results.py             # Results validation & decision logic
├── README.md                       # This file
│
├── venvs/                         # Virtual environments
│   ├── nova_v1_0/                # v1.0 environment
│   └── nova_v1_1/                # v1.1 environment
│
├── test_repos/                    # Generated test repositories
│   ├── simple_math/              # Simple one-line fixes
│   ├── multi_file_fix/           # Complex multi-file fixes
│   ├── edge_no_failures/         # No failing tests scenario
│   ├── edge_patch_conflict/      # Patch conflict scenario
│   ├── edge_timeout/             # Timeout scenario
│   └── ...                       # More test cases
│
├── regression_results/            # Test results
│   └── <timestamp>/              # Results for each run
│       ├── v1_0/                # v1.0 results
│       ├── v1_1/                # v1.1 results
│       ├── regression_results.json
│       ├── REGRESSION_REPORT.md
│       └── comparison_chart.png
│
└── requirements/                  # Python requirements
    ├── nova_v1_0.txt
    └── nova_v1_1.txt
```

## 🚀 Quick Start

### 1. Setup Environment

#### Option A: Python Setup (Cross-platform)

```bash
cd regression_tests
python setup_environments.py
```

#### Option B: Shell Setup (Unix/Linux/Mac)

```bash
cd regression_tests
chmod +x setup_environments.sh
./setup_environments.sh
```

### 2. Set API Keys

```bash
export OPENAI_API_KEY="your-key-here"
# or
export ANTHROPIC_API_KEY="your-key-here"
```

### 3. Run Regression Tests

```bash
# Using the run script
python run_tests.py

# Or directly
python regression_orchestrator.py test_repos.yaml --output regression_results --verbose
```

### 4. Validate Results

```bash
# Check if v1.1 meets criteria
python validate_results.py regression_results/<timestamp>/regression_results.json
```

## 📊 Test Scenarios

### Real-World Repositories (10+)

1. **simple_math_fixes** - Basic mathematical operations
2. **string_operations** - String manipulation with encoding issues
3. **data_structures** - Complex data structure implementations
4. **web_framework_basic** - Small web framework with routing
5. **async_operations** - Async/await with race conditions
6. **database_orm** - Simple ORM with SQL generation bugs
7. **file_parser** - File parsing with edge cases
8. **api_client** - REST API client issues
9. **algorithm_lib** - Algorithm implementations with logic errors
10. **config_parser** - Configuration parsing with validation bugs

### Edge Cases

1. **No Failing Tests** - Repository with all tests passing
2. **Patch Conflict** - Designed to cause patch application failures
3. **Max Iterations** - Requires more iterations than allowed
4. **Timeout** - Tests that exceed time limits
5. **One-Line Fix** - Simple off-by-one error
6. **Multi-File Fix** - Changes required across multiple files
7. **Major Refactor** - Significant code restructuring needed

### Special Test Cases

- **Import Issues** - Module resolution and circular imports
- **Type Hints** - Type annotation related failures
- **Exception Handling** - Error propagation issues

## 🔧 Configuration

### test_repos.yaml

The main configuration file defines:

- Nova command paths for each version
- Test repository specifications
- Timeout and iteration limits
- Expected failures for each test

Example:

```yaml
nova_v1_0_cmd: "python -m nova_v1_0"
nova_v1_1_cmd: "python -m nova"

runs:
  - name: "simple_math_fixes"
    path: "./test_repos/simple_math"
    max_iters: 6
    timeout: 600
    expected_failures: 2
```

### Customization

You can add custom test repositories:

```yaml
- name: "custom_test"
  url: "https://github.com/user/repo.git"
  branch: "test-branch"
  max_iters: 10
  timeout: 1800
```

## 📈 Metrics Collected

For each test run, we collect:

- **Success/Failure Status** - Did all tests pass?
- **Tests Fixed** - Number of failing tests that were fixed
- **Iterations Used** - How many fix attempts were made
- **Execution Time** - Total time taken
- **Patches Applied** - Number of code changes
- **Error Conditions** - Timeouts, crashes, patch failures

## 📝 Reports Generated

### 1. JSON Results

- `regression_results.json` - Complete test data
- Individual test results in JSON format

### 2. Markdown Report

- Executive summary with pass/fail status
- Detailed test-by-test comparison
- Edge case analysis
- Performance metrics
- Recommendations

### 3. Visual Charts

- Success rate comparison bar chart
- Test outcome distribution pie chart
- Performance comparison graphs

## 🎯 Validation & Decision Making

The `validate_results.py` script performs comprehensive validation:

### Validation Checks

1. **Success Rate Check** - v1.1 must achieve ≥70%
2. **Regression Check** - No tests where v1.0 succeeds but v1.1 fails
3. **Performance Check** - Comparable execution time and iterations
4. **Edge Case Check** - Required edge cases handled properly
5. **Stability Check** - Error rate <5%

### Decision Outcomes

- **✅ ADOPT** - All criteria met, ready for production
- **⚠️ CONDITIONAL** - Some improvements needed
- **❌ REJECT** - Critical failures requiring fixes

## 🔄 Continuous Integration

To run in CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run Nova Regression Tests
  run: |
    cd regression_tests
    python setup_environments.py
    python run_tests.py
    python validate_results.py regression_results/*/regression_results.json
```

## 🐛 Troubleshooting

### Common Issues

1. **API Key Not Set**

   ```bash
   export OPENAI_API_KEY="your-key"
   ```

2. **Python Version**

   - Requires Python 3.8+
   - Check with: `python --version`

3. **Missing Dependencies**

   ```bash
   pip install -r requirements/nova_v1_1.txt
   ```

4. **Test Repository Generation Failed**

   ```bash
   python edge_case_generator.py
   ```

5. **Nova Source Not Found**
   - Ensure Nova v1.0 is in `../releases/v0.1.0-alpha/`
   - Ensure Nova v1.1 is in `../src/`

## 📚 Advanced Usage

### Running Specific Tests

```python
from nova_runner_wrapper import NovaRunnerWrapper

wrapper = NovaRunnerWrapper("v1_1")
results = wrapper.run_fix(
    repo_path="./test_repos/simple_math",
    max_iters=10,
    timeout=600,
    verbose=True
)
```

### Comparing Versions Directly

```python
from nova_runner_wrapper import compare_versions

comparison = compare_versions(
    "./test_repos/complex_refactor",
    max_iters=10,
    verbose=True
)
print(f"Winner: {comparison['winner']}")
```

### Custom Validation Criteria

```python
from validate_results import RegressionValidator

validator = RegressionValidator("results.json")
validator.MIN_SUCCESS_RATE = 80.0  # Stricter requirement
passed, report = validator.validate_all()
```

## 🤝 Harrison Chase's DeepAgents Comparison

The suite includes analysis comparing our Deep Agent with Harrison Chase's `deepagents` framework:

```bash
python validate_results.py results.json --compare-deepagents
```

This helps decide whether to:

- Continue with our in-house Deep Agent
- Adopt techniques from deepagents
- Switch to the deepagents framework

## 📊 Expected Outcomes

Based on the test plan, we anticipate:

- **v1.1 Success Rate**: 75-85% (exceeding 70% requirement)
- **Performance**: Comparable or better than v1.0
- **Regressions**: 0 (all v1.0 successes maintained)
- **Edge Cases**: All handled gracefully
- **Recommendation**: ADOPT v1.1 as default

## 🚦 Next Steps

After successful validation:

1. **Merge v1.1** to main branch
2. **Deprecate v1.0** legacy code
3. **Update documentation** to reflect single CLI path
4. **Release v1.1** as the default version
5. **Monitor production** performance

## 📄 License

This test suite is part of Nova CI-Rescue and follows the same license.

## 🙏 Acknowledgments

- Nova CI-Rescue team for v1.0 foundation
- Deep Agent integration developers
- Harrison Chase for deepagents inspiration
- Open source community for test repositories

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: Production Ready
