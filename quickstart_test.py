#!/usr/bin/env python3
"""
Nova CI-Rescue Quickstart Test Script
This script creates a simple test with an intentional bug and runs Nova to fix it.
Perfect for verifying your installation is working correctly.
"""

import sys
import os
import subprocess
import tempfile
import shutil
from pathlib import Path

def main():
    """Run the quickstart test."""
    print("🚀 Nova CI-Rescue Quickstart Test")
    print("=" * 50)
    
    # Create a temporary directory for the test
    temp_dir = Path(tempfile.mkdtemp(prefix="nova_quickstart_"))
    print(f"📁 Created test directory: {temp_dir}")
    
    try:
        # Create a buggy calculator module
        calculator_file = temp_dir / "calculator.py"
        calculator_file.write_text('''
def add(a, b):
    """Add two numbers - has a bug!"""
    return a + b + 1  # Bug: adds extra 1

def multiply(a, b):
    """Multiply two numbers - has a bug!"""
    return a * b + 1  # Bug: adds 1 to result

def divide(a, b):
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
''')
        print("✅ Created buggy calculator.py")
        
        # Create test file
        test_file = temp_dir / "test_calculator.py"
        test_file.write_text('''
import pytest
from calculator import add, multiply, divide

def test_add():
    """Test addition function."""
    assert add(2, 3) == 5, "2 + 3 should equal 5"
    assert add(0, 0) == 0, "0 + 0 should equal 0"
    assert add(-1, 1) == 0, "-1 + 1 should equal 0"

def test_multiply():
    """Test multiplication function."""
    assert multiply(2, 3) == 6, "2 * 3 should equal 6"
    assert multiply(0, 5) == 0, "0 * 5 should equal 0"
    assert multiply(4, 1) == 4, "4 * 1 should equal 4"

def test_divide():
    """Test division function."""
    assert divide(10, 2) == 5.0, "10 / 2 should equal 5"
    assert divide(7, 1) == 7.0, "7 / 1 should equal 7"
    
    with pytest.raises(ValueError):
        divide(10, 0)
''')
        print("✅ Created test_calculator.py with 3 tests")
        
        # Initialize git repo (required for Nova)
        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@nova.ai"], cwd=temp_dir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Nova Test"], cwd=temp_dir, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=temp_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit with bugs"], cwd=temp_dir, capture_output=True)
        print("✅ Initialized git repository")
        
        # Run pytest to show failures
        print("\n📊 Running tests to show failures...")
        result = subprocess.run(
            ["python", "-m", "pytest", "-v", "--tb=short"],
            cwd=temp_dir,
            capture_output=True,
            text=True
        )
        
        failed_count = result.stdout.count("FAILED")
        if failed_count > 0:
            print(f"❌ Found {failed_count} failing test(s) - as expected!")
        else:
            print("⚠️  No failures found - this is unexpected")
            
        # Run Nova to fix the tests
        print("\n🤖 Running Nova CI-Rescue to fix the tests...")
        print("   (This may take 30-60 seconds)")
        
        nova_result = subprocess.run(
            ["nova", "fix", str(temp_dir), "--max-iters", "2", "--timeout", "120"],
            capture_output=True,
            text=True
        )
        
        if nova_result.returncode == 0:
            print("✅ Nova completed successfully!")
        else:
            print(f"⚠️  Nova exited with code {nova_result.returncode}")
            if "API" in nova_result.stderr or "API" in nova_result.stdout:
                print("   Hint: Check your API key configuration")
            
        # Run tests again to verify fix
        print("\n📊 Running tests again to verify fixes...")
        result = subprocess.run(
            ["python", "-m", "pytest", "-v"],
            cwd=temp_dir,
            capture_output=True,
            text=True
        )
        
        if "passed" in result.stdout and "failed" not in result.stdout.lower():
            print("✅ All tests passing! Nova successfully fixed the bugs!")
            
            # Show the fixes
            print("\n📝 Here's what Nova fixed:")
            fixed_code = (temp_dir / "calculator.py").read_text()
            if "+ 1" not in fixed_code:
                print("   - Removed the '+1' bugs from add() and multiply()")
            else:
                print("   - Applied fixes to calculator.py")
                
            return 0
        else:
            print("⚠️  Some tests still failing")
            print("   This might be due to API limits or timeout")
            print("   Try running: nova fix " + str(temp_dir) + " --max-iters 5")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        return 1
        
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up test directory: {temp_dir}")
        try:
            shutil.rmtree(temp_dir)
        except:
            print(f"   Note: Could not delete {temp_dir}, please remove manually")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Nova CI-Rescue Installation Verification")
    print("=" * 50 + "\n")
    
    # Check for Nova installation
    try:
        subprocess.run(["nova", "--version"], capture_output=True, check=True)
    except:
        print("❌ Nova is not installed or not in PATH")
        print("   Please run: pip install -e .")
        sys.exit(1)
    
    # Check for API key
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
        print("⚠️  Warning: No API key found")
        print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY in your .env file")
        print("   Continuing anyway (will fail when calling API)...")
    
    sys.exit(main())
