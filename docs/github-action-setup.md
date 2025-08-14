# CI-Auto-Rescue GitHub Action Setup Guide

## Overview

CI-Auto-Rescue automatically fixes failing tests in your CI pipeline and provides detailed reports as GitHub check runs and PR comments.

## Features

- 🔧 **Automatic Test Fixing**: Detects and fixes failing tests using AI
- 📊 **Detailed Reporting**: Posts results as GitHub check runs and PR comments
- ⏱️ **Performance Metrics**: Tracks runtime, iterations, and files changed
- 📝 **Comprehensive Logs**: Uploads artifacts for debugging
- 🔄 **Smart Triggers**: Runs on PR updates or when other workflows fail

## Quick Start

### 1. Add the Workflow File

Create `.github/workflows/ci-auto-rescue.yml` in your repository:

```yaml
name: CI-Auto-Rescue

on:
  pull_request:
    types: [opened, synchronize]
  workflow_run:
    workflows: ["CI", "Tests"] # Names of your test workflows
    types: [completed]
    branches: [main, develop]

permissions:
  contents: write
  checks: write
  pull-requests: write

jobs:
  auto-rescue:
    name: Auto-Fix Failing Tests
    runs-on: ubuntu-latest
    if: |
      (github.event_name == 'workflow_run' && github.event.workflow_run.conclusion == 'failure') ||
      (github.event_name == 'pull_request')

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: "3.12"

      - name: Install Nova CI-Rescue
        run: pip install nova-ci-rescue

      - name: Run Auto-Rescue
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          nova fix . --max-iters 3 --timeout 300
```

### 2. Configure Secrets

Add these secrets to your repository (Settings → Secrets and variables → Actions):

- **Required:**

  - `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`: Your AI API key

- **Optional:**
  - `GITHUB_TOKEN`: Automatically provided by GitHub Actions

### 3. Customize Triggers

#### Run on Test Failure

```yaml
on:
  workflow_run:
    workflows: ["Test Suite", "CI Pipeline"] # Your workflow names
    types: [completed]
```

#### Run on Pull Requests

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]
```

#### Manual Trigger

```yaml
on:
  workflow_dispatch:
    inputs:
      max_iterations:
        description: "Maximum fix iterations"
        default: "3"
```

## Configuration Options

### Workflow Inputs

| Parameter        | Description                    | Default |
| ---------------- | ------------------------------ | ------- |
| `max_iterations` | Maximum number of fix attempts | 3       |
| `timeout`        | Timeout in seconds             | 300     |
| `repo_path`      | Repository path to fix         | .       |

### Environment Variables

| Variable            | Description                  | Required |
| ------------------- | ---------------------------- | -------- |
| `OPENAI_API_KEY`    | OpenAI API key               | Yes\*    |
| `ANTHROPIC_API_KEY` | Anthropic API key            | Yes\*    |
| `GITHUB_TOKEN`      | GitHub token (auto-provided) | Yes      |

\*At least one AI API key is required

## Output Format

### GitHub Check Run

The action creates a check run with:

- ✅/❌ Pass/fail status
- Runtime and iteration metrics
- Summary of tests fixed
- Link to detailed logs

Example:

```
✅ CI-Auto-Rescue Report

Status: SUCCESS
Runtime: ⏱ 2m 15s
Iterations: 🔁 2
Files Changed: 📝 3

Test Results:
- Initial Failures: 5
- Tests Fixed: 5
- Remaining Failures: 0
```

### Pull Request Comment

The action posts/updates a PR comment with:

```markdown
## ✅ CI-Auto-Rescue Results

| Metric           | Value   |
| ---------------- | ------- |
| ⏱ Runtime        | 2m 15s  |
| 🔁 Iterations    | 2       |
| 📝 Files Changed | 3       |
| 🧪 Tests Fixed   | 5/5     |
| ✅ Outcome       | SUCCESS |

### 📊 Summary

Successfully fixed 5 failing tests! 🎉
All tests are now passing.
```

## Advanced Usage

### Custom Test Commands

Override the default pytest command:

```yaml
- name: Run Auto-Rescue
  run: |
    nova fix . --test-cmd "npm test" --max-iters 3
```

### Conditional Execution

Only run for specific file changes:

```yaml
jobs:
  auto-rescue:
    if: contains(github.event.pull_request.labels.*.name, 'auto-fix')
```

### Multiple Language Support

```yaml
strategy:
  matrix:
    language: [python, javascript, go]
steps:
  - name: Run Auto-Rescue
    run: |
      nova fix . --language ${{ matrix.language }}
```

## Artifacts

The action uploads these artifacts:

- `nova_output.log`: Complete Nova execution log
- `initial_test_results.json`: Test results before fix
- `final_test_results.json`: Test results after fix
- `report.json`: Structured report data
- `.nova/`: Nova telemetry and state files

Access artifacts from the Actions tab → Select workflow run → Artifacts section

## Troubleshooting

### Common Issues

1. **No API Key Error**

   ```
   Error: OPENAI_API_KEY environment variable not set
   ```

   **Solution**: Add the API key to repository secrets

2. **Permission Denied**

   ```
   Error: Resource not accessible by integration
   ```

   **Solution**: Ensure workflow has required permissions:

   ```yaml
   permissions:
     contents: write
     checks: write
     pull-requests: write
   ```

3. **Tests Still Failing**
   - Check the uploaded artifacts for detailed logs
   - Increase `max_iterations` or `timeout`
   - Review the generated patches in `.nova/artifacts/`

### Debug Mode

Enable verbose logging:

```yaml
- name: Run Auto-Rescue
  run: |
    nova fix . --verbose --debug
```

## Security Considerations

1. **API Keys**: Store as encrypted secrets, never in code
2. **Permissions**: Use minimal required permissions
3. **Branch Protection**: Consider requiring manual approval for auto-fixes
4. **Code Review**: Always review generated fixes before merging

## Example Repositories

See CI-Auto-Rescue in action:

1. [Simple Python Project](https://github.com/example/python-demo)
2. [Multi-Language Monorepo](https://github.com/example/monorepo-demo)
3. [Complex Test Suite](https://github.com/example/complex-tests)

## Support

- 📖 [Documentation](https://nova-ci.github.io/docs)
- 🐛 [Issue Tracker](https://github.com/nova-ci/nova-ci-rescue/issues)
- 💬 [Discussions](https://github.com/nova-ci/nova-ci-rescue/discussions)
- 📧 [Email Support](mailto:support@nova-ci.dev)

## License

CI-Auto-Rescue is licensed under the MIT License. See [LICENSE](LICENSE) for details.
