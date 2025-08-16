#!/bin/bash
CONFIG_FILE="${1:-/Users/seb/GPT5/working/ci-auto-rescue/regression_tests/test_repos.yaml}"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file not found: $CONFIG_FILE"
    echo "Usage: $0 [config_file]"
    exit 1
fi

echo "Starting regression tests with config: $CONFIG_FILE"
python3 "/Users/seb/GPT5/working/ci-auto-rescue/regression_tests/regression_orchestrator.py" "$CONFIG_FILE" \
    --output "/Users/seb/GPT5/working/ci-auto-rescue/regression_tests/regression_results" \
    --verbose

if [ $? -eq 0 ]; then
    echo -e "\033[0;32m✓ Regression tests completed successfully\033[0m"
    echo "Results available in: /Users/seb/GPT5/working/ci-auto-rescue/regression_tests/regression_results/"
else
    echo -e "\033[0;31m✗ Regression tests failed or found regressions\033[0m"
    echo "Check results in: /Users/seb/GPT5/working/ci-auto-rescue/regression_tests/regression_results/"
    exit 1
fi
