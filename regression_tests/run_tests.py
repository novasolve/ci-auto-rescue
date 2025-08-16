#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path

config_file = sys.argv[1] if len(sys.argv) > 1 else "/Users/seb/GPT5/working/ci-auto-rescue/regression_tests/test_repos.yaml"

print(f"Starting regression tests with config: {config_file}")

result = subprocess.run([
    sys.executable,
    "/Users/seb/GPT5/working/ci-auto-rescue/regression_tests/regression_orchestrator.py",
    config_file,
    "--output", "/Users/seb/GPT5/working/ci-auto-rescue/regression_tests/regression_results",
    "--verbose"
])

if result.returncode == 0:
    print("✓ Regression tests completed successfully")
    print(f"Results available in: /Users/seb/GPT5/working/ci-auto-rescue/regression_tests/regression_results/")
else:
    print("✗ Regression tests failed or found regressions")
    print(f"Check results in: /Users/seb/GPT5/working/ci-auto-rescue/regression_tests/regression_results/")
    sys.exit(1)
