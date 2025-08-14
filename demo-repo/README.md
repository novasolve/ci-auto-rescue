# Nova CI-Rescue Demo Repository

This is a demonstration repository for testing the **Nova CI-Rescue** GitHub Action. It contains a simple Python calculator module with intentional bugs that Nova can automatically detect and fix.

## 🎯 Purpose

This demo repository showcases how Nova CI-Rescue can:

- Detect failing tests in your CI pipeline
- Analyze the failures and understand the root cause
- Generate patches to fix the issues
- Apply the fixes and verify they work
- Create artifacts and reports for review

## 🐛 Intentional Bugs

The `src/calculator.py` module contains several intentional bugs:

1. **Subtraction Bug**: Uses addition operator instead of subtraction
2. **Division Bug**: Missing zero division check
3. **Power Bug**: Uses multiplication instead of exponentiation
4. **Square Root Bug**: Doesn't handle negative numbers
5. **Factorial Bug**: Off-by-one error in the range
6. **Fibonacci Bug**: Wrong initial values for sequence
7. **Prime Check Bug**: Inefficient algorithm checking up to n

## 📁 Project Structure

```
demo-repo/
├── src/
│   ├── __init__.py
│   └── calculator.py      # Calculator module with bugs
├── tests/
│   ├── __init__.py
│   └── test_calculator.py # Test suite that exposes the bugs
├── .gitignore
├── pyproject.toml         # Project configuration
├── requirements.txt       # Test dependencies
└── README.md             # This file
```

## 🚀 Running the Demo

### Local Testing

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Run tests to see failures:**

   ```bash
   pytest tests/ -v
   ```

   You should see multiple test failures due to the intentional bugs.

3. **Run Nova CI-Rescue locally:**

   ```bash
   # Install Nova CI-Rescue
   pip install -e /path/to/nova-ci-rescue

   # Run Nova fix
   nova fix . --max-iters 6 --timeout 1200 --verbose
   ```

### GitHub Actions

1. **Manual Trigger:**

   - Go to the Actions tab in your GitHub repository
   - Select "Nova CI Rescue" workflow
   - Click "Run workflow"
   - Configure parameters:
     - Max iterations (default: 6)
     - Timeout in seconds (default: 1200)
     - Verbose output (default: false)
     - Python version (default: 3.11)

2. **View Results:**
   - Check the workflow run summary
   - Download artifacts:
     - `nova-telemetry-*`: Complete telemetry logs and traces
     - `nova-workdir-*`: Nova working directory files
     - `test-reports-*`: JUnit XML test reports
     - `patches-*`: All generated patches

## 📊 Expected Results

When Nova CI-Rescue runs on this demo repository, it should:

1. **Detect 7-8 failing tests** in the initial test run
2. **Generate patches** to fix each bug:

   - Change `a + b` to `a - b` in subtract method
   - Add zero division check in divide method
   - Change `base * exponent` to `base ** exponent` in power method
   - Add negative number check in square_root method
   - Fix range to `range(1, n+1)` in factorial method
   - Fix initial Fibonacci values
   - Optimize prime checking algorithm

3. **Apply fixes** and verify all tests pass
4. **Create artifacts** with detailed logs and patches

## 🔧 Configuration

### Environment Variables

For the GitHub Action to work with LLM providers, set these secrets in your repository:

- `OPENAI_API_KEY`: For OpenAI GPT models
- `ANTHROPIC_API_KEY`: For Anthropic Claude models

### Workflow Configuration

The workflow accepts these inputs:

| Parameter        | Description               | Default | Range            |
| ---------------- | ------------------------- | ------- | ---------------- |
| `max_iterations` | Maximum fix attempts      | 6       | 1-20             |
| `timeout`        | Overall timeout (seconds) | 1200    | 60-7200          |
| `verbose`        | Enable detailed output    | false   | true/false       |
| `python_version` | Python version to use     | 3.11    | 3.10, 3.11, 3.12 |

## 📈 Success Metrics

A successful Nova CI-Rescue run will show:

- ✅ All tests passing after fixes
- 📝 Generated patches for each bug
- 📊 Test reports showing before/after results
- 🔍 Detailed telemetry logs
- 💾 Saved artifacts for audit trail

## 🧪 Test Coverage

The test suite covers:

- Basic arithmetic operations (add, subtract, multiply, divide)
- Advanced operations (power, square root, factorial)
- Edge cases (division by zero, negative numbers)
- Utility functions (Fibonacci, prime checking, GCD)
- History tracking and management

## 📝 Notes

- This is a simplified demo for testing purposes
- In real scenarios, Nova CI-Rescue handles more complex codebases
- The bugs are intentionally simple to demonstrate the concept
- Nova uses LLMs to understand and fix the issues contextually

## 🔗 Links

- [Nova CI-Rescue Documentation](https://github.com/novasolve/ci-auto-rescue)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pytest Documentation](https://docs.pytest.org/)

## 📄 License

This demo repository is part of the Nova CI-Rescue project.

---

**Created for demonstrating Nova CI-Rescue capabilities**
