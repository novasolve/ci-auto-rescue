#!/usr/bin/env python3
"""Show the exact diff of changes Nova would make."""

import difflib
from pathlib import Path

# Read the buggy version
buggy_file = Path("src/calculator.py")
fixed_file = Path("src/calculator_fixed.py")

with open(buggy_file) as f:
    buggy_lines = f.readlines()

with open(fixed_file) as f:
    fixed_lines = f.readlines()

# Generate unified diff
diff = difflib.unified_diff(
    buggy_lines,
    fixed_lines,
    fromfile="src/calculator.py (buggy)",
    tofile="src/calculator.py (fixed by Nova)",
    lineterm=""
)

print("=" * 60)
print("DIFF: Changes Nova CI-Rescue would make")
print("=" * 60)
print()

for line in diff:
    if line.startswith("+++"):
        print(f"\033[92m{line}\033[0m")  # Green for new file
    elif line.startswith("---"):
        print(f"\033[91m{line}\033[0m")  # Red for old file
    elif line.startswith("+"):
        print(f"\033[92m{line}\033[0m")  # Green for additions
    elif line.startswith("-"):
        print(f"\033[91m{line}\033[0m")  # Red for deletions
    elif line.startswith("@@"):
        print(f"\033[96m{line}\033[0m")  # Cyan for line numbers
    else:
        print(line)
