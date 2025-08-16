#!/usr/bin/env python3
"""
Nova CI-Rescue Demo - Manual Fix Demonstration
===============================================
This script demonstrates what Nova CI-Rescue would do to fix the failing tests.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def run_tests():
    """Run the tests and return True if they pass."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_calculator.py", "-v"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def apply_fixes():
    """Apply the fixes that Nova would automatically generate."""
    print("\n🔧 Applying fixes that Nova would generate:\n")
    
    # Read the current buggy file
    with open("src/calculator.py", "r") as f:
        content = f.read()
    
    print("Original calculator.py has these bugs:")
    print("  - add() uses subtraction instead of addition")
    print("  - subtract() has an off-by-one error")
    print("  - multiply() uses addition instead of multiplication")
    print("  - divide() uses integer division and lacks zero-check")
    
    # Apply the fixes
    fixes = [
        ("return a - b  # (Should be a + b)", "return a + b"),
        ("return a - b - 1  # (Should be a - b)", "return a - b"),
        ("return a + b  # (Should be a * b)", "return a * b"),
        ("return a // b  # (Should handle b=0 and use float division a / b)",
         """if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b""")
    ]
    
    for old, new in fixes:
        content = content.replace(old, new)
    
    # Save the fixed file
    with open("src/calculator.py", "w") as f:
        f.write(content)
    
    print("\n✅ Applied all fixes to calculator.py")

def main():
    """Main demo function."""
    print("=" * 60)
    print("Nova CI-Rescue Demo - Automatic Test Fixing")
    print("=" * 60)
    
    # Backup original file
    shutil.copy("src/calculator.py", "src/calculator.py.backup")
    
    try:
        # Step 1: Show tests are failing
        print("\n📊 Step 1: Running tests with buggy code...")
        if run_tests():
            print("✅ Tests are already passing!")
            return
        else:
            print("❌ Tests are failing (as expected)")
        
        # Step 2: Apply fixes (what Nova would do automatically)
        print("\n🤖 Step 2: Nova CI-Rescue analyzing failures...")
        print("Nova would:")
        print("  1. Analyze the test failures")
        print("  2. Understand what the tests expect")
        print("  3. Generate patches to fix the bugs")
        print("  4. Apply and validate the fixes")
        
        apply_fixes()
        
        # Step 3: Verify tests now pass
        print("\n📊 Step 3: Running tests with fixed code...")
        if run_tests():
            print("\n🎉 Success! All tests are now passing!")
            print("\nThis is what Nova CI-Rescue does automatically:")
            print("  - Analyzes failing tests")
            print("  - Understands the expected behavior")
            print("  - Generates appropriate fixes")
            print("  - Validates the fixes work")
        else:
            print("❌ Some tests still failing")
    
    finally:
        # Restore original file
        shutil.move("src/calculator.py.backup", "src/calculator.py")
        print("\n🔄 Restored original buggy file for next demo")

if __name__ == "__main__":
    main()
