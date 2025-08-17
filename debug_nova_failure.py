#!/usr/bin/env python3
"""Debug why Nova isn't finding failing tests."""

import json
import subprocess
import tempfile
from pathlib import Path

# Run pytest with JSON report like Nova does
json_report_path = "/tmp/debug_nova.json"
junit_report_path = "/tmp/debug_nova.xml"

test_path = Path("examples/demos/demo_broken_project")
cmd = [
    "python", "-m", "pytest",
    str(test_path),
    "--json-report",
    f"--json-report-file={json_report_path}",
    f"--junit-xml={junit_report_path}",
    "--tb=short",
    "--maxfail=5",
    "-q",
    "--no-header",
    "--no-summary",
    "-rN",
]

print(f"Running from: {Path.cwd()}")
print(f"Test path: {test_path}")
print(f"Running: {' '.join(cmd)}")
result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
print(f"Exit code: {result.returncode}")
print(f"Stdout: {result.stdout}")
print(f"Stderr: {result.stderr}")

# Check if JSON report exists
if Path(json_report_path).exists():
    print(f"\nJSON report exists at {json_report_path}")
    with open(json_report_path) as f:
        report = json.load(f)
    
    print(f"Summary: {report.get('summary', {})}")
    print(f"Number of tests: {len(report.get('tests', []))}")
    
    # Check test outcomes
    outcomes = {}
    for test in report.get('tests', []):
        outcome = test.get('outcome', 'unknown')
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
        if outcome in ['failed', 'error']:
            print(f"  Failed test: {test.get('nodeid')} - {outcome}")
    
    print(f"\nOutcome summary: {outcomes}")
else:
    print(f"\nJSON report NOT found at {json_report_path}")

# Also check if it's an import error or something
print("\n\nTrying direct pytest import...")
try:
    import pytest
    print(f"pytest version: {pytest.__version__}")
    print(f"pytest location: {pytest.__file__}")
except ImportError as e:
    print(f"Failed to import pytest: {e}")
