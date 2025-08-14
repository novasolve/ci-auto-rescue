# Nova CI-Rescue — Quickstart Guide

## Installation

### Prerequisites

- Python 3.8+
- Git
- OpenAI or Anthropic API key

### Install Nova

```bash
pip install -e .
```

## Configuration

### Option 1: Environment Variable

```bash
export OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Option 2: .env File

Create a `.env` file in your project root:

```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# Optional
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOVA_MAX_ITERS=3
NOVA_RUN_TIMEOUT_SEC=600
```

## Running Nova

### Basic Usage

```bash
nova fix /path/to/repo
```

### With Options

```bash
nova fix . --max-iters 3 --timeout 600
```

### With YAML Configuration

Create a configuration file (e.g., `config.yaml`):

```yaml
# Nova CI-Rescue Configuration
model: gpt-4 # LLM model to use
timeout: 1800 # Overall timeout in seconds
max_iters: 8 # Maximum fix iterations
max_changed_lines: 500 # Safety limit: max lines per patch
max_changed_files: 10 # Safety limit: max files per patch

# Paths that should not be modified
blocked_paths:
  - "*.env"
  - ".git/*"
  - "node_modules/*"
  - "__pycache__/*"
```

Then use it:

```bash
# For single fix
nova fix --config config.yaml

# CLI flags override config values
nova fix --config config.yaml --max-iters 3  # Uses 3, not 8
```

### Batch Evaluation

```bash
nova eval repos.yaml

# With configuration
nova eval repos.yaml --config config.yaml
```

## Inspecting Results

### View Artifacts

```bash
tree .nova/<run>/
# Expected structure:
# .nova/20250813T201234Z/
# ├── trace.jsonl       # Complete execution log
# ├── diffs/           # Patches for each iteration
# │   ├── step-1.patch
# │   └── step-2.patch
# └── reports/         # Test results
#     ├── step-1.xml
#     └── step-2.xml
```

### Check Test Results

```bash
# View the final test report
cat .nova/<latest>/reports/final.xml
```

## Resetting After a Run

### Reset to Original State

```bash
git reset --hard HEAD
```

### Clean Working Directory

```bash
git clean -fd
```

## Troubleshooting

### Issue: API Key Not Found

**Solution:** Ensure your API key is set in environment or .env file

### Issue: Tests Still Failing After Max Iterations

**Solution:** Increase `--max-iters` or check if the failure is beyond automated fixing

### Issue: Timeout Reached

**Solution:** Increase `--timeout` value or optimize test suite

### Issue: Permission Denied

**Solution:** Ensure you have write permissions in the repository

## Getting Help

- Check logs: `.nova/<run>/trace.jsonl`
- Join Discord: [discord.gg/nova-solve]
- Email support: support@joinnova.com
