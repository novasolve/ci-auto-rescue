#!/usr/bin/env python3
"""Debug subprocess pytest issue."""

import subprocess
import sys
import os
import tempfile

print("Testing pytest subprocess issue...")
print(f"Python: {sys.executable}")
print(f"Python version: {sys.version}")

# Test 1: Direct pytest import
try:
    import pytest
    import pytest_jsonreport
    print("✓ Can import pytest and pytest_jsonreport directly")
except ImportError as e:
    print(f"✗ Import error: {e}")

# Test 2: Run pytest --version via subprocess
print("\nTest 2: pytest --version via subprocess")
result = subprocess.run([sys.executable, "-m", "pytest", "--version"], capture_output=True, text=True)
print(f"Exit code: {result.returncode}")
print(f"Stdout: {result.stdout}")
print(f"Stderr: {result.stderr}")

# Test 3: Run pytest with --json-report via subprocess
print("\nTest 3: pytest with --json-report via subprocess")
with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
    json_path = f.name

cmd = [
    sys.executable, "-m", "pytest",
    "examples/demos/demo_broken_project",
    "--json-report",
    f"--json-report-file={json_path}",
    "--maxfail=1",
    "-q"
]

print(f"Command: {' '.join(cmd)}")
result = subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy())
print(f"Exit code: {result.returncode}")
print(f"Stderr: {result.stderr[:500] if result.stderr else 'None'}")

# Check if JSON file was created
import os
if os.path.exists(json_path):
    print(f"✓ JSON report created, size: {os.path.getsize(json_path)} bytes")
else:
    print("✗ JSON report NOT created")

# Clean up
try:
    os.unlink(json_path)
except:
    pass
