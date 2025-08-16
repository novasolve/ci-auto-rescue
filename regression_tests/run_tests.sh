#!/bin/bash
CONFIG="${1:-test_repos.yaml}"
echo "Running regression tests with config: $CONFIG"
python regression_orchestrator.py "$CONFIG" --output regression_results --verbose
