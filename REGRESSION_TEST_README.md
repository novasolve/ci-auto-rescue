# Nova CI-Rescue Regression Test Suite

A single Python script that comprehensively tests Nova's Deep Agent (v1.1) against the Legacy Agent (v1.0) to ensure no regressions.

## Key Features

- **Single Script Solution**: Everything runs from one Python file
- **Automatic Environment Setup**: Creates isolated virtual environment
- **Test Repository Generation**: Creates synthetic failing tests
- **Side-by-Side Comparison**: Runs both agents on the same problems
- **Regression Detection**: Identifies when v1.1 fails where v1.0 succeeds
- **Comprehensive Reporting**: Generates detailed Markdown and JSON reports

## How It Works

The script uses the **same Nova codebase** for both v1.0 and v1.1:
- **v1.0 (Legacy Agent)**: Runs `nova fix --legacy-agent`
- **v1.1 (Deep Agent)**: Runs `nova fix` (default behavior)

## Prerequisites

- Python 3.8+
- Git repository with Nova CI-Rescue
- OpenAI API key

## Usage

### Quick Start

```bash
# Set your API key
export OPENAI_API_KEY='your-key-here'

# Run the regression test suite
python nova_regression_test.py
```

### Command Line Options

```bash
# Verbose output
python nova_regression_test.py --verbose

# Keep test files after completion
python nova_regression_test.py --keep-files

# Specify Nova workspace directory
python nova_regression_test.py --workspace /path/to/nova
```

## What It Tests

The script creates several test repositories with intentional bugs:

1. **Simple Math Operations** - Basic arithmetic functions with bugs
2. **String Operations** - String manipulation with incorrect implementations
3. **List Operations** - Array/list handling with logic errors

Each repository is tested with both agents to compare:
- Success rate
- Number of iterations needed
- Time to fix
- Overall effectiveness

## Success Criteria

The test suite validates:
- ✅ Fix success rate ≥ 70%
- ✅ No performance regression vs v1.0
- ✅ Proper handling of edge cases

## Output

The script generates:

1. **Console Output** - Real-time progress and results
2. **Markdown Report** - `regression_test_run/results/regression_report.md`
3. **JSON Results** - `regression_test_run/results/all_results.json`
4. **Individual Test Results** - JSON file for each test repository

## Example Output

```
============================================================
Nova CI-Rescue Regression Test Suite
============================================================

✅ Directories created
✅ Virtual environment created
✅ Nova installed

============================================================
Running Regression Tests
============================================================

Testing: simple_math
Running Legacy Agent (v1.0) on simple_math...
✅ Legacy Agent (v1.0): ✅ Success | Iterations: 2 | Time: 15.3s

Running Deep Agent (v1.1) on simple_math...
✅ Deep Agent (v1.1): ✅ Success | Iterations: 1 | Time: 12.1s

Winner: v1_1_more_efficient
```

## Clean Up

The script automatically cleans up all test files unless `--keep-files` is specified.

## Troubleshooting

### OPENAI_API_KEY not set
```bash
export OPENAI_API_KEY='sk-...'
```

### Module not found errors
Ensure you're in the Nova CI-Rescue directory when running the script.

### Permission denied
```bash
chmod +x nova_regression_test.py
```

## Benefits of Single Script Approach

1. **Simplicity** - No complex setup or multiple files to manage
2. **Portability** - Easy to share and run anywhere
3. **Self-contained** - All logic in one place
4. **Maintainable** - Single file to update and version control
5. **CI/CD Ready** - Can be easily integrated into pipelines

## Integration with CI/CD

```yaml
# Example GitHub Actions workflow
- name: Run Regression Tests
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    python nova_regression_test.py
```

## License

Part of Nova CI-Rescue project.
