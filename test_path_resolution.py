#!/usr/bin/env python3
"""Test script to understand the path resolution bug"""

from pathlib import Path

# Simulate the scenario
repo_path = Path("/Users/seb/GPT5/working/ci-auto-rescue/examples/demos/demo_math_ops")
nodeid = "examples/demos/demo_math_ops/test_math_ops.py::test_basic_arithmetic"

# Parse file from nodeid
if '::' in nodeid:
    file_part, test_part = nodeid.split('::', 1)
    test_name = test_part.replace('::', '.')
else:
    file_part = nodeid
    test_name = Path(nodeid).stem

print(f"Original file_part: {file_part}")
print(f"repo_path: {repo_path}")
print(f"repo_path.name: {repo_path.name}")

# Try the normalization logic from TestRunner
file_path = Path(file_part)
try:
    # Try to make file_part relative to the repo root if possible
    if file_path.is_absolute():
        file_part = str(file_path.relative_to(repo_path))
        print(f"Absolute path case: {file_part}")
    else:
        # For relative paths, check if they contain the full repo path
        # Convert to absolute for comparison
        abs_file = (repo_path / file_path).resolve()
        print(f"Trying to resolve: {repo_path} / {file_path}")
        print(f"abs_file: {abs_file}")
        print(f"abs_file.exists(): {abs_file.exists()}")
        if abs_file.exists():
            file_part = str(abs_file.relative_to(repo_path))
            print(f"Relative path case (exists): {file_part}")
except (ValueError, Exception) as e:
    print(f"Exception in first try block: {e}")
    # If relative_to fails, try manual stripping
    repo_name = repo_path.name
    print(f"Falling back to manual stripping with repo_name: {repo_name}")
    
    # Find the repo name in the path and strip everything before it
    pos = str(file_path).find(f"{repo_name}/")
    print(f"Position of '{repo_name}/' in '{file_path}': {pos}")
    if pos != -1:
        # Found repo name in path, extract everything after it
        file_part = str(file_path)[pos + len(repo_name) + 1:]
        print(f"Manual strip result: {file_part}")
    elif file_part.startswith(f"{repo_name}/"):
        # Simple case: path starts with repo name
        file_part = file_part[len(repo_name)+1:]
        print(f"Simple strip result: {file_part}")

print(f"\nFinal file_part: {file_part}")
print(f"Expected: test_math_ops.py")
