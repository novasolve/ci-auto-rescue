#!/usr/bin/env python3
"""
Direct test to apply the fixes to calculator.py
"""

import sys
sys.path.insert(0, '/Users/seb/GPT5/working/ci-auto-rescue/src')

from pathlib import Path

# Create a simple patch to fix the calculator
patch_text = """--- a/src/calculator.py
+++ b/src/calculator.py
@@ -6,3 +6,3 @@
 def add(a, b):
     \"\"\"Add two numbers.\"\"\"
-    # Bug: incorrect operation used
     return a + b  # Fixed
 
@@ -11,3 +11,3 @@
 def subtract(a, b):
     \"\"\"Subtract b from a.\"\"\"
-    # Bug: off-by-one error in subtraction
     return a - b  # Fixed
 
@@ -16,3 +16,3 @@
 def multiply(a, b):
     \"\"\"Multiply two numbers.\"\"\"
-    # Bug: incorrect operation used
     return a * b  # Fixed
 
@@ -21,3 +21,5 @@
 def divide(a, b):
     \"\"\"Divide a by b.\"\"\"
-    # Bug: missing zero division check and wrong division behavior
+    if b == 0:
+        raise ValueError("Cannot divide by zero")
     return a / b  # Fixed
"""

# Write the corrected file directly
calculator_path = Path("/Users/seb/GPT5/working/ci-auto-rescue/demo-failing-tests/src/calculator.py")
fixed_content = '''"""
Simple calculator module with correct implementation.
"""

def add(a, b):
    """Add two numbers."""
    return a + b

def subtract(a, b):
    """Subtract b from a."""
    return a - b

def multiply(a, b):
    """Multiply two numbers."""
    return a * b

def divide(a, b):
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
'''

# Apply the fix
calculator_path.write_text(fixed_content)
print("✓ Fixed calculator.py")

# Test the fixes
import subprocess
result = subprocess.run(
    ["python", "-m", "pytest", "tests/test_calculator.py", "-v"],
    cwd="/Users/seb/GPT5/working/ci-auto-rescue/demo-failing-tests",
    capture_output=True,
    text=True
)

print("\nTest Results:")
print(result.stdout)
if result.returncode == 0:
    print("✓ All tests passing!")
else:
    print("✗ Some tests still failing")
    print(result.stderr)
