# Nova Unified Test Suite - Complete Usage Guide

## 🚀 Quick Start

The **Nova Unified Test Suite** combines the best features from all three test suites into one powerful, flexible testing solution.

```bash
# Basic usage - run with built-in tests
./nova_unified_test_suite.py

# Generate synthetic repos and test
./nova_unified_test_suite.py --generate

# Use with configuration file
./nova_unified_test_suite.py --config test_config.yaml

# Compare two versions
./nova_unified_test_suite.py --compare --v1-cmd "nova_v1_0" --v2-cmd "nova_v1_1"
```

## 📋 Features Overview

### ✨ **Combined Best Features**

| Feature | Description | Origin |
|---------|-------------|--------|
| **Auto Environment Setup** | Creates venv, installs Nova automatically | nova_test_suite.py |
| **Version Comparison** | Compare v1.0 vs v1.1 performance | regression_orchestrator.py |
| **Edge Case Coverage** | Unfixable bugs, no-op patches, etc. | Provided harness |
| **Flexible Config** | YAML optional, built-in tests available | Provided harness |
| **Advanced Analysis** | Iteration counting, patch analysis | Provided harness |
| **Professional Output** | Tables, colors, JSON, Markdown | All three |
| **CI/CD Ready** | Proper exit codes, artifact generation | All three |

### 🎯 **10 Built-in Test Scenarios**

1. **simple_math** - Basic arithmetic bugs
2. **string_ops** - String manipulation errors  
3. **list_ops** - List operation bugs
4. **off_by_one** - Classic off-by-one errors
5. **edge_cases** - Edge case handling issues
6. **unfixable_bug** - Tests with wrong expectations ⚠️
7. **no_op_patch** - Tests that always fail ⚠️
8. **import_issues** - Import and module problems
9. **type_hints** - Type hint related failures
10. **exception_handling** - Exception handling errors

## 🔧 Installation & Setup

### Prerequisites

```bash
# Ensure Python 3.9+ is installed
python --version

# Set OpenAI API key (required for Nova)
export OPENAI_API_KEY='your-key-here'
```

### First Run

```bash
# Make executable (if not already)
chmod +x nova_unified_test_suite.py

# Run with auto-setup
./nova_unified_test_suite.py --generate
```

The suite will automatically:
1. Create a virtual environment
2. Install Nova CI-Rescue
3. Generate test repositories
4. Run all tests
5. Generate reports

## 📝 Command-Line Options

### Test Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `-c, --config FILE` | YAML configuration file | Built-in tests |
| `-g, --generate` | Generate synthetic test repos | False |
| `--timeout SECONDS` | Default timeout per test | 600 |
| `--max-iters N` | Default max iterations | 6 |

### Execution Modes

| Option | Description |
|--------|-------------|
| `--compare` | Compare two Nova versions |
| `--nova-cmd CMD` | Nova command (single mode) |
| `--v1-cmd CMD` | Nova v1 command (compare mode) |
| `--v2-cmd CMD` | Nova v2 command (compare mode) |

### Output Options

| Option | Description |
|--------|-------------|
| `-j, --json-out FILE` | Save JSON results |
| `-m, --md-out FILE` | Save Markdown report |
| `-o, --output-dir DIR` | Output directory |
| `-v, --verbose` | Verbose output |
| `--no-color` | Disable colored output |

### Environment Options

| Option | Description |
|--------|-------------|
| `--skip-venv` | Skip virtual environment creation |
| `--keep-files` | Keep temporary test files |

## 📊 Test Modes

### 1. Single Version Testing (Default)

Tests a single Nova version against all scenarios:

```bash
# Test current Nova installation
./nova_unified_test_suite.py

# Test specific Nova command
./nova_unified_test_suite.py --nova-cmd "python -m nova"

# With custom configuration
./nova_unified_test_suite.py --config my_tests.yaml
```

**Output Example:**
```
Repository          | Status    | Fixed | Iterations | Time  | Notes
--------------------|-----------|-------|------------|-------|-------
simple_math         | ✅ Passed | 3/3   | 2          | 15.3s |
string_ops          | ✅ Passed | 4/4   | 3          | 22.1s |
unfixable_bug       | ❌ Failed | 0/2   | 6          | 45.2s | max_iterations
```

### 2. Version Comparison Mode

Compares two Nova versions side-by-side:

```bash
# Compare v1.0 vs v1.1
./nova_unified_test_suite.py --compare \
  --v1-cmd "./nova_v1_0" \
  --v2-cmd "./nova_v1_1"
```

**Output Example:**
```
Test                | v1.0      | v1.1      | Outcome              | Time (v1.0/v1.1)
--------------------|-----------|-----------|----------------------|-----------------
simple_math         | ✅        | ✅        | v1_1_more_efficient  | 18.2s/12.1s
string_ops          | ❌        | ✅        | v1_1_better          | 30.5s/22.3s
unfixable_bug       | ❌        | ❌        | both_failed          | 45.1s/44.8s
```

## 🎨 Configuration File Format

### Basic Configuration

```yaml
# test_config.yaml
runs:
  - name: "my_test_1"
    path: "./path/to/repo"
    max_iters: 6
    timeout: 600
    description: "Test description"
    
  - name: "my_test_2"
    url: "https://github.com/user/repo.git"
    branch: "main"
    max_iters: 10
    timeout: 900
```

### Advanced Configuration with Comparison

```yaml
# comparison_config.yaml
nova_v1_cmd: "./nova_v1_0"
nova_v2_cmd: "./nova_v1_1"

runs:
  - name: "simple_bugs"
    path: "./test_repos/simple"
    max_iters: 5
    timeout: 300
    expected_failures: 3
    difficulty: "easy"
    
  - name: "complex_refactor"
    path: "./test_repos/complex"
    max_iters: 15
    timeout: 1200
    expected_failures: 8
    difficulty: "hard"
```

## 📈 Understanding Results

### Success Criteria

- **Single Mode:** ≥70% success rate across all tests
- **Comparison Mode:** No regressions (v1.1 must not perform worse than v1.0)

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All tests passed / Success criteria met |
| 1 | Tests failed / Regressions detected |
| 2 | Below success threshold |
| 130 | User interrupted (Ctrl+C) |

### Metrics Explained

- **Tests Fixed:** Number of failing tests that Nova successfully fixed
- **Iterations:** Number of fix attempts Nova made
- **Patches Applied:** Number of patch files generated
- **Error Types:**
  - `timeout` - Test exceeded time limit
  - `max_iterations` - Hit iteration limit without fixing all tests
  - `patch_failure` - Patch application failed
  - `no_api_key` - OpenAI API key not configured

## 🔍 Advanced Usage Examples

### 1. Full Regression Test with Reports

```bash
./nova_unified_test_suite.py \
  --generate \
  --config regression_tests/test_repos.yaml \
  --json-out results/data.json \
  --md-out results/report.md \
  --verbose
```

### 2. Quick Smoke Test

```bash
# Test only simple scenarios
./nova_unified_test_suite.py \
  --timeout 300 \
  --max-iters 3
```

### 3. CI/CD Pipeline Integration

```bash
#!/bin/bash
# ci_test.sh

# Run tests
./nova_unified_test_suite.py \
  --generate \
  --json-out artifacts/results.json \
  --md-out artifacts/report.md \
  --no-color

# Check exit code
if [ $? -eq 0 ]; then
  echo "✅ Tests passed"
  exit 0
else
  echo "❌ Tests failed"
  exit 1
fi
```

### 4. Development Testing

```bash
# Skip venv setup when testing repeatedly
./nova_unified_test_suite.py \
  --skip-venv \
  --keep-files \
  --verbose
```

### 5. Edge Case Focus

```bash
# Create config for edge cases only
cat > edge_cases.yaml << EOF
runs:
  - name: "unfixable_bug"
    path: "./test_repos/unfixable_bug"
    max_iters: 3
    timeout: 300
    
  - name: "no_op_patch"
    path: "./test_repos/no_op_patch"
    max_iters: 2
    timeout: 300
EOF

./nova_unified_test_suite.py --config edge_cases.yaml
```

## 🐛 Troubleshooting

### Common Issues

#### 1. "No module named 'nova'"
```bash
# Solution: Let the suite install Nova
./nova_unified_test_suite.py  # Don't use --skip-venv
```

#### 2. "OPENAI_API_KEY not set"
```bash
# Solution: Export your API key
export OPENAI_API_KEY='sk-...'
```

#### 3. "Permission denied"
```bash
# Solution: Make script executable
chmod +x nova_unified_test_suite.py
```

#### 4. Tests timing out
```bash
# Solution: Increase timeout
./nova_unified_test_suite.py --timeout 1200
```

## 📊 Sample Output

### Successful Run
```
================================================================================
                     Nova CI-Rescue Unified Test Suite
                         Best of All Worlds Edition
================================================================================

Setting Up Test Environment
✅ Virtual environment created
✅ Nova installed

Running tests...

Testing: simple_math
Description: Simple mathematical operations with basic bugs
✅ Success! Fixed 3 tests in 2 iterations (15.3s)

Testing: string_ops
Description: String manipulation with encoding issues
✅ Success! Fixed 4 tests in 3 iterations (22.1s)

...

================================================================================
Test Results Summary
================================================================================

Repository     | Status    | Fixed | Iterations | Time  | Notes
---------------|-----------|-------|------------|-------|------
simple_math    | ✅ Passed | 3/3   | 2          | 15.3s |
string_ops     | ✅ Passed | 4/4   | 3          | 22.1s |
list_ops       | ✅ Passed | 5/5   | 2          | 18.7s |

Summary Statistics:
Total Scenarios: 10
Successful: 8 (80.0%)
Tests Fixed: 35/40 (87.5%)

✅ Success criteria met! (80.0% >= 70%)
```

## 🔄 Migration from Old Test Suites

### From `nova_test_suite.py`
```bash
# Old way
python nova_test_suite.py --verbose

# New way (equivalent)
./nova_unified_test_suite.py --verbose
```

### From `regression_orchestrator.py`
```bash
# Old way
python regression_tests/regression_orchestrator.py test_repos.yaml

# New way (equivalent)
./nova_unified_test_suite.py --compare \
  --config test_repos.yaml \
  --v1-cmd "./nova_v1_0" \
  --v2-cmd "./nova_v1_1"
```

### From provided harness
```bash
# Old way
python nova_regression_test.py --generate -j results.json

# New way (equivalent)
./nova_unified_test_suite.py --generate --json-out results.json
```

## 🎯 Best Practices

1. **Start Simple:** Run without options first to test basic functionality
2. **Generate Fresh:** Use `--generate` to ensure clean test repos
3. **Save Artifacts:** Always use `--json-out` and `--md-out` in CI/CD
4. **Set Timeouts:** Use reasonable timeouts to prevent hanging
5. **Review Failures:** Check unfixable_bug and no_op_patch results - they should fail
6. **Version Testing:** Use comparison mode before major upgrades

## 📚 Additional Resources

- [Nova CI-Rescue Documentation](./docs/)
- [Test Configuration Examples](./examples/)
- [Regression Test Guide](./regression_tests/README.md)

## 🤝 Contributing

To add new test scenarios:

1. Add a generator method in `SyntheticRepoGenerator` class
2. Include it in the `generate_all()` method
3. Test with: `./nova_unified_test_suite.py --generate`

## 📄 License

This test suite is part of the Nova CI-Rescue project.
