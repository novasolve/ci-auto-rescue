# Milestone D: Demo & Release Evaluation System

This directory contains the evaluation framework for testing Nova CI-Rescue on multiple repositories automatically.

## Quick Start

### Run a quick test (30 seconds)
```bash
python verify_milestone_d.py evals/minimal_test.yaml
```

### Run standard test (3 minutes)
```bash
python verify_milestone_d.py evals/quick_test.yaml
```

### Run full suite (5-10 minutes)
```bash
python verify_milestone_d.py evals/demo_repos.yaml
```

## Configuration Files

- `demo_repos.yaml` - Full suite of 12+ demo repositories
- `quick_test.yaml` - Quick 3-repository test set
- `minimal_test.yaml` - Single repository for fast testing

## Output

### Console Output
Progress logs and a summary table showing:
- Repository name
- Success/Failure status
- Runtime in seconds
- Number of iterations

### JSON Results
Saved to `evals/results/<timestamp>.json` with detailed metrics:
```json
{
  "name": "Math Operations Demo",
  "repo": "./examples/demos/demo_math_ops",
  "success": true,
  "iterations": 3,
  "duration_seconds": 12.34
}
```

## Exit Codes

- **0**: All runs succeeded
- **1**: At least one run failed

Perfect for CI/CD integration!

## Custom Configuration

Create your own YAML config:
```yaml
runs:
  - name: "My Project"
    path: "/path/to/project"
```

## Available Demo Repositories

The system includes demos testing:
- Math operations, string processing
- Type hints, data structures
- Exception handling, file I/O
- Imports, OOP inheritance
- And more specialized test scenarios

## Requirements

- Python 3.10+
- PyYAML (`pip install PyYAML`)
- Rich (optional, for better formatting)

## CI/CD Usage

```yaml
- name: Run Nova Evaluation
  run: python verify_milestone_d.py evals/demo_repos.yaml
```
