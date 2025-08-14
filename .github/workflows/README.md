# CI-Auto-Rescue GitHub Actions

This directory contains GitHub Action workflows for automatically fixing failing tests using Nova CI-Rescue.

## Available Workflows

### 1. `ci-auto-rescue.yml` (Full Featured)

Complete workflow with all features including:

- GitHub check runs with detailed metrics
- PR comments with fix summaries
- Artifact uploads
- Multiple trigger options
- Comprehensive error handling

### 2. `ci-auto-rescue-simple.yml` (Quick Start)

Simplified workflow for quick setup:

- Basic test fixing functionality
- Minimal configuration required
- Good for trying out the tool

## Setup Instructions

### Step 1: Choose a Workflow

Copy either workflow file to your repository's `.github/workflows/` directory.

### Step 2: Configure API Keys

Add your AI API key to repository secrets:

1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add either:
   - Name: `OPENAI_API_KEY`, Value: Your OpenAI API key
   - Name: `ANTHROPIC_API_KEY`, Value: Your Anthropic API key

### Step 3: Customize Triggers

Edit the `on:` section to match your needs:

```yaml
on:
  # Run when tests fail
  workflow_run:
    workflows: ["Your Test Workflow Name"]
    types: [completed]

  # Run on pull requests
  pull_request:
    types: [opened, synchronize]

  # Manual trigger
  workflow_dispatch:
```

### Step 4: Install Nova CI-Rescue

Ensure your repository has Nova CI-Rescue installed. Add to your requirements:

```
nova-ci-rescue>=0.1.0
```

## Features

### GitHub Check Runs

The workflow creates check runs that appear on PRs and commits:

- Shows pass/fail status
- Displays runtime and iteration metrics
- Links to detailed logs

### PR Comments

Automatically posts/updates PR comments with:

- Test fix summary
- Performance metrics table
- Links to artifacts and logs

### Artifacts

Uploads debugging artifacts including:

- Nova execution logs
- Test results (before/after)
- Generated patches
- Telemetry data

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: OpenAI API key for GPT models
- `ANTHROPIC_API_KEY`: Anthropic API key for Claude models
- `GITHUB_TOKEN`: Automatically provided by GitHub

### Workflow Parameters

- `max_iterations`: Maximum fix attempts (default: 3)
- `timeout`: Timeout in seconds (default: 300)
- `repo_path`: Repository path (default: current directory)

## Examples

### Running on Test Failures

```yaml
on:
  workflow_run:
    workflows: ["CI", "Test Suite"]
    types: [completed]
    branches: [main, develop]
```

### Running on Specific Labels

```yaml
jobs:
  auto-rescue:
    if: contains(github.event.pull_request.labels.*.name, 'auto-fix')
```

### Custom Test Commands

```yaml
- name: Run Nova CI-Rescue
  run: |
    nova fix . --test-cmd "npm test" --max-iters 5
```

## Troubleshooting

### No API Key Error

Ensure you've added the API key to repository secrets (not variables).

### Permission Denied

Add required permissions to the workflow:

```yaml
permissions:
  contents: write
  checks: write
  pull-requests: write
```

### Tests Still Failing

- Check artifacts for detailed logs
- Increase `max_iterations` or `timeout`
- Review generated patches for issues

## Support

For issues or questions:

- Open an issue in [nova-ci/nova-ci-rescue](https://github.com/nova-ci/nova-ci-rescue)
- Check the [documentation](https://nova-ci.github.io/docs)
- Join our [Discord community](https://discord.gg/nova-ci)
