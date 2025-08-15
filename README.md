# Nova CI-Rescue

Nova CI-Rescue: automated test fixing agent (MVP)

## Description

Nova CI-Rescue is an automated test fixing agent powered by LLM and LangGraph technology. It automatically detects and fixes failing tests in your CI/CD pipeline, saving developers time and improving productivity.

## Installation

```bash
pip install nova-ci-rescue
```

## Quick Start

After installation, the `nova` command will be available globally:

```bash
# Show help
nova --help

# Fix failing tests in a repository
nova fix /path/to/repo

# Dry run mode (no changes applied)
nova fix /path/to/repo --dry-run
```

## Features

- Automated test failure detection
- Intelligent patch generation using LLM
- Integration with pytest test suite
- Support for Python projects
- Safe execution with sandboxing
- Detailed telemetry and logging

## Requirements

- Python >= 3.10
- pytest >= 7.0.0

## License

Proprietary - NovaSolve

## Author

NovaSolve (dev@novasolve.ai)
