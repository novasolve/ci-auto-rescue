# Nova CI-Rescue - Limitations and Known Issues

## Overview

This document provides a comprehensive list of Nova CI-Rescue v1.0's current limitations, known issues, and scenarios where manual intervention is required. Understanding these limitations helps set proper expectations and ensures successful adoption.

## Version Scope

**Current Version:** v1.0 - Happy Path Edition  
**Release Focus:** Simple, straightforward test failures with clear fixes

## Current Limitations

### 1. Language Support

#### ✅ Supported

- **Python** (3.8, 3.9, 3.10, 3.11, 3.12)
- **Test Framework:** pytest (primary), unittest (basic support)

#### ❌ Not Yet Supported

- JavaScript/TypeScript (planned for v1.1)
- Java (planned for v1.2)
- Go (planned for v1.2)
- Ruby (planned for v1.3)
- C/C++ (planned for v2.0)
- Other languages (roadmap TBD)

### 2. Test Framework Limitations

#### Fully Supported

- pytest with standard assertions
- unittest basic test cases
- Simple fixtures and setup/teardown

#### Limited Support

- Complex pytest fixtures with dependencies
- Parameterized tests (partial support)
- Class-based test hierarchies
- Custom test runners

#### Not Supported

- Jest, Mocha, Jasmine (JavaScript)
- JUnit, TestNG (Java)
- RSpec (Ruby)
- Integration test frameworks
- E2E test frameworks (Selenium, Cypress, Playwright)

### 3. Types of Test Failures

#### ✅ Can Fix

- **Simple Errors**
  - TypeError (wrong type passed)
  - AttributeError (missing attribute)
  - KeyError (missing dictionary key)
  - IndexError (list index out of range)
  - ValueError (incorrect value)
- **Logic Errors**

  - Off-by-one errors
  - Missing null/None checks
  - Incorrect boolean conditions
  - Wrong operator usage (+/-, </>, etc.)
  - Missing return statements

- **Assertion Failures**
  - Incorrect expected values
  - Wrong assertion types
  - Missing assertions

#### ⚠️ Limited Success

- **Complex Logic**

  - Multi-step algorithms
  - Recursive functions with edge cases
  - Complex state machines
  - Concurrency issues

- **Data Issues**
  - Complex data transformations
  - Database-related failures
  - File I/O with specific formats
  - Network-dependent tests

#### ❌ Cannot Fix

- **Environmental Issues**
  - Missing dependencies
  - Incorrect Python version
  - OS-specific failures
  - Hardware-dependent tests
- **External Dependencies**

  - API endpoint failures
  - Database connection issues
  - Third-party service outages
  - Authentication/authorization failures

- **Flaky Tests**
  - Race conditions
  - Time-dependent tests
  - Random/probabilistic failures
  - Order-dependent test suites

### 4. Code Complexity Limitations

#### Single File Changes

- **Optimal:** Changes within 1-2 functions
- **Good:** Changes within single module
- **Success Rate:** 70-85%

#### Multi-File Changes

- **Limited:** 2-3 file modifications
- **Challenge:** Maintaining consistency across files
- **Success Rate:** 40-60%

#### Large Refactoring

- **Not Supported:** Major architectural changes
- **Not Supported:** API redesigns
- **Not Supported:** Database schema migrations

### 5. Performance Limitations

#### Time Constraints

- **Default Timeout:** 20 minutes total
- **Per Test Run:** 10 minutes max
- **Per Iteration:** ~2-5 minutes typical

#### Iteration Limits

- **Default Max:** 6 iterations
- **Recommended:** 3-4 iterations
- **Diminishing Returns:** After 4 iterations

#### Scale Limitations

- **Test Suite Size:** Best with <100 tests
- **Failure Count:** Optimal for 1-5 failures
- **File Size:** Best with files <1000 lines

### 6. Safety and Security Limitations

#### Cannot Modify

- CI/CD configuration files
- Deployment scripts
- Environment configuration
- Security-sensitive files
- Package lock files
- Database migrations

#### Change Limits (per iteration)

- Maximum 200 lines changed
- Maximum 10 files modified
- No binary file modifications
- No large file creation (>1MB)

## Known Issues

### 1. False Positives

**Issue:** Nova may report success when tests pass for wrong reasons  
**Example:** Test passes because exception is caught, not because logic is correct  
**Workaround:** Always review Nova's changes before merging

### 2. Partial Fixes

**Issue:** Nova fixes some tests but breaks others  
**Frequency:** ~5-10% of cases  
**Workaround:** Use `git add -p` to selectively apply good changes

### 3. Over-Specific Fixes

**Issue:** Nova may fix symptoms rather than root causes  
**Example:** Hardcoding expected values instead of fixing calculation  
**Workaround:** Review fix logic, not just test results

### 4. Import Resolution

**Issue:** Complex import paths may confuse Nova  
**Example:** Relative imports in nested packages  
**Workaround:** Use absolute imports where possible

### 5. Test Isolation

**Issue:** Nova assumes tests are independent  
**Problem:** Shared state between tests can cause issues  
**Workaround:** Ensure proper test isolation before running Nova

## Scenarios Requiring Manual Intervention

### 1. Dependency Issues

```python
# Nova CANNOT fix:
ImportError: No module named 'unavailable_package'
# Solution: Install missing package manually
```

### 2. Environment Configuration

```python
# Nova CANNOT fix:
KeyError: 'DATABASE_URL' not in os.environ
# Solution: Set up environment variables
```

### 3. External Service Failures

```python
# Nova CANNOT fix:
requests.exceptions.ConnectionError: Failed to connect to API
# Solution: Mock external services or fix connectivity
```

### 4. Complex Business Logic

```python
# Nova MAY STRUGGLE with:
def complex_calculation(data):
    # 100+ lines of domain-specific logic
    # Multiple interdependent calculations
    # Industry-specific rules
```

### 5. Schema/API Changes

```python
# Nova CANNOT automatically handle:
# - Database schema migrations
# - API contract changes
# - Breaking changes in dependencies
```

## Workarounds and Best Practices

### 1. Preparation for Nova

#### Before Running Nova

- ✅ Commit all changes
- ✅ Ensure tests run (even if failing)
- ✅ Check dependencies are installed
- ✅ Set up environment variables

#### Repository Setup

```bash
# Good setup for Nova
git status  # Clean working directory
pip install -r requirements.txt  # Dependencies installed
pytest --collect-only  # Tests discoverable
```

### 2. Optimizing Success Rate

#### Start Simple

- Fix one test type at a time
- Run Nova on focused test files
- Use `--max-iters 3` initially

#### Provide Context

```bash
# Better: Run on specific test file
nova fix . --test-file tests/test_calculator.py

# Rather than: Running on entire suite
nova fix .
```

### 3. When Nova Struggles

#### Incremental Approach

1. Let Nova attempt the fix
2. Review and apply partial fixes
3. Manually complete remaining issues
4. Run Nova again if needed

#### Debugging Nova's Attempts

```bash
# Check what Nova tried
cat .nova/latest/trace.jsonl | jq '.event_type'

# Review each patch attempt
for patch in .nova/latest/diffs/*.patch; do
    echo "=== $patch ==="
    cat "$patch"
done
```

### 4. Integration Tips

#### CI/CD Pipeline

```yaml
# Run Nova only on PR branches, not main
on:
  pull_request:
    branches: ["!main"]

# Set conservative limits
env:
  NOVA_MAX_ITERS: 3
  NOVA_TIMEOUT: 300 # 5 minutes
```

#### Team Workflow

1. Developer pushes code with failing tests
2. Nova attempts fixes in CI
3. Developer reviews Nova's suggestions
4. Manual refinement if needed
5. Merge when satisfied

## Future Roadmap

### v1.1 (Q2 2024)

- JavaScript/TypeScript support
- Better multi-file coordination
- Improved complex logic handling

### v1.2 (Q3 2024)

- Java and Go support
- Integration test support
- Custom test framework adapters

### v2.0 (Q4 2024)

- Large refactoring capabilities
- Learning from previous fixes
- Team-specific customization

## Getting Help with Limitations

### Documentation

- Check this document first
- Review [FAQ](./14-faq.md)
- See [Troubleshooting Guide](./15-troubleshooting.md)

### Community Support

- Discord: Ask in #nova-limitations
- GitHub: Label issues with `limitation`
- Email: support@joinnova.com

### Feature Requests

If you're hitting a limitation frequently:

1. Check if it's on our roadmap
2. Vote on existing feature requests
3. Submit new request with use case

## Summary

Nova CI-Rescue v1.0 is intentionally focused on the "happy path" - simple, clear test failures that can be fixed with targeted changes. While this means certain complex scenarios are out of scope, it also means Nova is reliable and predictable for the cases it handles.

By understanding these limitations, you can:

- Set appropriate expectations
- Use Nova effectively within its capabilities
- Know when manual intervention is needed
- Plan for future improvements

Remember: Nova is designed to be a helpful assistant, not a complete replacement for developer debugging. Use it to handle the routine fixes so you can focus on the complex problems that require human creativity and domain knowledge.
