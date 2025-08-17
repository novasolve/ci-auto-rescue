#!/usr/bin/env python3
"""Test script to verify Nova fixes for demo_broken_project"""

import subprocess
import sys
import os

def test_nova_fix():
    """Run nova fix on demo_broken_project and check results"""
    
    print("Testing Nova fixes on demo_broken_project...")
    print("=" * 60)
    
    # Run nova fix command
    cmd = ["nova", "fix", "examples/demos/demo_broken_project/", "--verbose"]
    
    print(f"Running: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        print("STDOUT:")
        print(result.stdout)
        print("-" * 60)
        
        print("STDERR:")
        print(result.stderr)
        print("-" * 60)
        
        # Check for success indicators
        success_indicators = [
            "All tests fixed",
            "SUCCESS",
            "0 failures",
            "5 passed",
            "all tests are now passing"
        ]
        
        output = result.stdout + result.stderr
        success = any(indicator in output for indicator in success_indicators)
        
        # Check for known issues
        issues = []
        if "broken_module" in output:
            issues.append("❌ Agent still looking for 'broken_module' instead of 'broken'")
        
        if "hallucinated" in output or ("from broken_module import" in output and "ERROR: Access blocked" in output):
            issues.append("❌ Agent appears to be hallucinating file contents")
        
        if "'str' object has no attribute 'get'" in output:
            issues.append("❌ JSON parsing bug still present")
            
        # Report results
        print("\nRESULTS:")
        print("=" * 60)
        
        if issues:
            print("Issues found:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print("✅ No known issues detected")
            
        if success:
            print("✅ Tests appear to have been fixed successfully")
        else:
            print("❌ Tests do not appear to be fixed")
            
        # Check if src/broken.py was modified
        broken_file = "examples/demos/demo_broken_project/src/broken.py"
        if os.path.exists(broken_file):
            print(f"\n✅ Source file exists: {broken_file}")
            # Check if it was modified recently
            import time
            mtime = os.path.getmtime(broken_file)
            if time.time() - mtime < 300:  # Modified in last 5 minutes
                print("✅ Source file was recently modified")
        else:
            print(f"\n❌ Source file not found: {broken_file}")
            
        return success and not issues
        
    except subprocess.TimeoutExpired:
        print("❌ Command timed out after 120 seconds")
        return False
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

if __name__ == "__main__":
    success = test_nova_fix()
    sys.exit(0 if success else 1)
