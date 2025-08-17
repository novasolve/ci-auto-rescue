# Test Suite Comparison: Existing vs Provided Regression Harness

## Executive Summary

Your workspace contains **three different test suites**:

1. **nova_test_suite.py** - A simplified, self-contained test suite
2. **regression_tests/regression_orchestrator.py** - A comprehensive regression testing framework comparing v1.0 vs v1.1
3. **The provided regression harness script** (nova_regression_test.py) - A comprehensive standalone test harness for v1.1 Deep Agent

## Detailed Comparison

### 1. Your Current Test Suite (`nova_test_suite.py`)

**Purpose:** Single consolidated script for testing Nova Deep Agent

**Key Features:**

- ✅ Self-contained with virtual environment creation
- ✅ Generates synthetic test repositories on-the-fly
- ✅ Color-coded terminal output with ANSI codes
- ✅ Runs Nova in a controlled environment
- ✅ Generates Markdown reports and JSON results
- ✅ 4 predefined test scenarios (simple_math, string_ops, list_ops, edge_cases)

**Architecture:**

```python
NovaTestSuite Class:
├── setup_environment()      # Creates venv, installs Nova
├── create_test_repository() # Generates test repos
├── create_test_scenarios()  # 4 built-in scenarios
├── run_nova_on_scenario()   # Executes Nova fix
├── generate_report()        # Creates reports
└── cleanup()               # Removes temp files
```

**Strengths:**

- Simple to run and understand
- Good for quick smoke testing
- Automatic environment setup
- Built-in test generation

**Limitations:**

- Only 4 hardcoded test scenarios
- No support for external repos via YAML config
- No comparison between versions
- Limited edge case coverage
- No timeout/max iteration testing

---

### 2. Your Regression Test Orchestrator (`regression_tests/`)

**Purpose:** Compare Nova v1.0 (legacy) vs v1.1 (Deep Agent) performance

**Key Features:**

- ✅ Runs tests on BOTH v1.0 and v1.1 versions
- ✅ YAML configuration support
- ✅ Detailed comparison metrics
- ✅ Report generation with charts
- ✅ Supports both eval mode and individual mode
- ✅ Handles remote Git repositories

**Architecture:**

```python
RegressionTestOrchestrator:
├── _run_version_tests()     # Tests each version
├── _run_eval_mode()         # Nova eval command
├── _run_individual_mode()   # Individual repo testing
├── _compare_results()       # Version comparison
├── _generate_summary()      # Statistics
└── _generate_reports()      # MD + charts
```

**Test Configuration (`test_repos.yaml`):**

- 15+ test scenarios defined
- Real-world repository tests
- Edge case scenarios
- Complexity-based tests
- Environment configurations for each version

**Strengths:**

- Version comparison capabilities
- Extensive test coverage
- Professional reporting
- CI/CD ready
- Configurable via YAML

**Limitations:**

- More complex setup required
- Requires both v1.0 and v1.1 installed
- Heavier resource usage

---

### 3. The Provided Regression Harness Script

**Purpose:** Comprehensive regression test harness specifically for Nova v1.1 Deep Agent

**Key Features:**

- ✅ YAML configuration support OR built-in test list
- ✅ Synthetic repo generation with `SyntheticRepoGenerator` class
- ✅ Detailed result parsing (iterations, patches, exit reasons)
- ✅ Edge case handling (timeout, max iterations, patch conflicts)
- ✅ JSON and Markdown output formats
- ✅ CI-friendly exit codes
- ✅ Isolated test runs using temporary directories

**Architecture:**

```python
Main Components:
├── SyntheticRepoGenerator   # Creates 6 test repo types
│   ├── off_by_one_repo()
│   ├── unfixable_repo()
│   ├── no_op_patch_repo()
│   ├── list_ops_repo()
│   ├── simple_math_repo()
│   └── string_ops_repo()
├── run_nova_fix()           # Execute Nova with params
├── analyze_nova_output()    # Parse results
├── print_results_table()    # Terminal output
├── write_results_json()     # JSON export
└── write_summary_markdown() # MD report
```

**Unique Features Not in Your Current Suites:**

1. **Unfixable bug scenario** - Test with incorrect expected values
2. **No-op patch scenario** - Tests that always fail regardless of code changes
3. **Better iteration counting** - Regex parsing of Nova output
4. **Patch counting** - Examines `.nova/*/diffs/*.patch` files
5. **Exit reason classification** - Detects timeout vs max iterations vs patch errors
6. **Flexible repo input** - YAML config OR built-in defaults
7. **Command-line flags** for generation, output paths

**Command-line Interface:**

```bash
python nova_regression_test.py \
  --generate           # Auto-generate test repos
  --config repos.yaml  # Optional YAML config
  --json-out results.json
  --md-out summary.md
```

---

## Key Differences Summary

| Feature                  | Your nova_test_suite.py  | Your regression_orchestrator.py | Provided Harness           |
| ------------------------ | ------------------------ | ------------------------------- | -------------------------- |
| **Purpose**              | Quick Deep Agent testing | v1.0 vs v1.1 comparison         | Comprehensive v1.1 testing |
| **Test Scenarios**       | 4 hardcoded              | 15+ in YAML                     | 6 built-in + YAML support  |
| **Version Support**      | v1.1 only                | Both v1.0 and v1.1              | v1.1 only                  |
| **Configuration**        | Command-line args        | YAML required                   | YAML optional              |
| **Edge Cases**           | Basic                    | Extensive                       | Extensive                  |
| **Unfixable Tests**      | ❌                       | ❌                              | ✅                         |
| **No-op Patches**        | ❌                       | ❌                              | ✅                         |
| **Patch Counting**       | ❌                       | ✅                              | ✅                         |
| **Exit Reason Analysis** | Basic                    | Basic                           | Advanced                   |
| **Report Types**         | MD + JSON                | MD + JSON + Charts              | MD + JSON + Table          |
| **CI Integration**       | Basic                    | Advanced                        | Advanced                   |
| **Test Isolation**       | ✅                       | ✅                              | ✅ (temp dirs)             |
| **Auto-generate Repos**  | Always                   | No                              | Optional flag              |

---

## What the Provided Harness Adds

### 1. **Better Edge Case Coverage**

- **Unfixable bugs**: Tests where the code is correct but test expectations are wrong
- **No-op patches**: Scenarios where no code change can fix the test
- **Off-by-one errors**: Specific common bug patterns

### 2. **More Sophisticated Analysis**

```python
# Better iteration extraction
for line in stdout.splitlines():
    match = re.search(r'iteration\s+(\d+)', line, flags=re.IGNORECASE)
    if match:
        iter_num = int(match.group(1))
```

### 3. **Cleaner Test Isolation**

```python
with tempfile.TemporaryDirectory() as tmpdir:
    dest_path = Path(tmpdir) / "repo"
    shutil.copytree(path, dest_path)
    # Run tests in isolated copy
```

### 4. **Flexible Configuration**

- Can run without any config file (uses built-in tests)
- Supports both approaches: config-driven and code-driven

### 5. **Better Output Formatting**

```python
# Professional table output with dynamic column widths
col_widths = [len(h) for h in headers]
for res in results:
    col_widths[0] = max(col_widths[0], len(res["name"]))
    # ... adjust all columns
```

---

## Recommendations

### If You Want to Adopt the Provided Harness:

1. **Integration Path:**

   ```bash
   # Place it alongside your existing tests
   cp nova_regression_test.py regression_tests/nova_deep_agent_harness.py
   ```

2. **Combine Strengths:**

   - Use your orchestrator for v1.0 vs v1.1 comparison
   - Use the provided harness for deep v1.1 testing
   - Keep nova_test_suite.py for quick smoke tests

3. **Enhance Your Current Suite:**
   Add these features from the provided harness to your `nova_test_suite.py`:

   - Unfixable bug scenarios
   - No-op patch scenarios
   - Better iteration counting regex
   - Optional YAML config support
   - `--generate` flag for repo creation

4. **Create a Unified Test Strategy:**

   ```yaml
   # test_strategy.yaml
   smoke_tests:
     script: nova_test_suite.py
     purpose: Quick validation

   deep_tests:
     script: nova_regression_test.py # The provided one
     purpose: Comprehensive v1.1 testing

   regression_tests:
     script: regression_orchestrator.py
     purpose: v1.0 vs v1.1 comparison
   ```

### Best Practices to Adopt:

1. **From the provided harness:**

   - Temporary directory isolation for each test
   - Regex-based metric extraction
   - Exit reason classification

2. **Missing in all suites:**
   - Test result caching to avoid re-running
   - Parallel test execution
   - Test result diffing between runs
   - Performance benchmarking over time

---

## Quick Migration Guide

To use the provided harness immediately:

```bash
# 1. Save the provided script
cat > regression_tests/nova_regression_test.py << 'EOF'
# [Paste the provided script here]
EOF

# 2. Make it executable
chmod +x regression_tests/nova_regression_test.py

# 3. Generate test repos and run
cd regression_tests
python nova_regression_test.py --generate \
  --json-out results.json \
  --md-out summary.md

# 4. Or use with your existing YAML config
python nova_regression_test.py \
  --config test_repos.yaml \
  --json-out results.json
```

---

## Conclusion

The provided regression harness offers **more sophisticated edge case testing** and **better output analysis** compared to your current `nova_test_suite.py`, while being **simpler and more focused** than your `regression_orchestrator.py` which handles version comparison.

**Best approach**: Use all three for different purposes:

- **nova_test_suite.py** → Quick smoke testing
- **Provided harness** → Deep v1.1 validation
- **regression_orchestrator.py** → Version migration decisions
