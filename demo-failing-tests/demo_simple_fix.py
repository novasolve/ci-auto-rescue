#!/usr/bin/env python3
"""
Simple demonstration comparing the two Nova Deep Agent implementations.
Shows how each would fix the calculator bugs.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List

def run_tests(verbose=False) -> Dict:
    """Run tests and return results."""
    result = subprocess.run(
        ["pytest", "tests/test_calculator.py", "-v"] if verbose else ["pytest", "tests/test_calculator.py", "-q"],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True
    )
    return {
        "passed": result.returncode == 0,
        "output": result.stdout + result.stderr
    }

def save_original():
    """Save the original buggy calculator."""
    calc_path = Path(__file__).parent / "src" / "calculator.py"
    backup_path = Path(__file__).parent / "src" / "calculator_backup.py"
    with open(calc_path, 'r') as f:
        original = f.read()
    with open(backup_path, 'w') as f:
        f.write(original)
    return original

def restore_original():
    """Restore the original buggy calculator."""
    calc_path = Path(__file__).parent / "src" / "calculator.py"
    backup_path = Path(__file__).parent / "src" / "calculator_backup.py"
    if backup_path.exists():
        with open(backup_path, 'r') as f:
            original = f.read()
        with open(calc_path, 'w') as f:
            f.write(original)
        backup_path.unlink()

def demo_current_implementation():
    """
    Demonstrate how the CURRENT implementation would fix the bugs.
    Uses complete file replacement via write_file tool.
    """
    print("\n" + "=" * 60)
    print("🔵 CURRENT IMPLEMENTATION (File Replacement)")
    print("=" * 60)
    
    print("\n1. Agent reads failing tests...")
    print("   Tool: open_file('tests/test_calculator.py')")
    
    print("\n2. Agent reads buggy calculator...")
    print("   Tool: open_file('src/calculator.py')")
    
    print("\n3. Agent analyzes and generates complete fixed file...")
    print("   LLM generates entire corrected calculator.py")
    
    # The current implementation would replace the entire file
    fixed_calculator = '''"""
Simple calculator module with a deliberately buggy implementation.
This is for demonstrating Nova CI-Rescue's automated fixing capabilities.
"""

def add(a, b):
    """Add two numbers."""
    # Bug: incorrect operation used
    return a + b

def subtract(a, b):
    """Subtract b from a."""
    # Bug: off-by-one error in subtraction
    return a - b

def multiply(a, b):
    """Multiply two numbers."""
    # Bug: incorrect operation used
    return a * b

def divide(a, b):
    """Divide a by b."""
    # Bug: missing zero division check and wrong division behavior
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b'''
    
    print("\n4. Agent writes complete fixed file...")
    print("   Tool: write_file('src/calculator.py', fixed_content)")
    
    # Apply the fix
    calc_path = Path(__file__).parent / "src" / "calculator.py"
    with open(calc_path, 'w') as f:
        f.write(fixed_calculator)
    
    print("\n5. Agent runs tests to verify...")
    print("   Tool: run_tests()")
    result = run_tests()
    
    if result["passed"]:
        print("   ✅ All tests passing!")
    else:
        print("   ❌ Tests still failing")
    
    print("\n📊 Summary:")
    print("   - Approach: Complete file replacement")
    print("   - Changes: Entire file rewritten")
    print("   - Safety: Limited (could overwrite unrelated code)")
    print("   - Tracking: No diff or commit history")
    
    return result["passed"]

def demo_proposed_implementation():
    """
    Demonstrate how the PROPOSED implementation would fix the bugs.
    Uses unified diff patches with critic review.
    """
    print("\n" + "=" * 60)
    print("🟢 PROPOSED IMPLEMENTATION (Patch-Based with Critic)")
    print("=" * 60)
    
    print("\n1. Agent runs tests and analyzes failures...")
    print("   Tool: RunTestsTool()")
    print("   Returns: Detailed failure analysis with error context")
    
    print("\n2. Agent generates targeted patch...")
    print("   LLM creates unified diff with only necessary changes:")
    print("""
   --- a/src/calculator.py
   +++ b/src/calculator.py
   @@ -7,7 +7,7 @@
    def add(a, b):
   -    return a - b  # (Should be a + b)
   +    return a + b
   
   @@ -13,7 +13,7 @@
    def subtract(a, b):
   -    return a - b - 1  # (Should be a - b)
   +    return a - b
   """)
    
    print("\n3. Critic reviews the patch...")
    print("   Tool: CriticReviewTool(patch)")
    print("   Critic analysis:")
    print("   - ✓ Correctly fixes add() operation")
    print("   - ✓ Correctly fixes subtract() off-by-one")
    print("   - ✓ Changes are minimal and targeted")
    print("   Result: APPROVED")
    
    print("\n4. Agent applies patch with safety checks...")
    print("   Tool: ApplyPatchTool(patch)")
    print("   - Preflight safety checks pass")
    print("   - Git applies patch and commits")
    print("   - Changed files tracked: ['src/calculator.py']")
    
    # Apply the fixes incrementally
    calc_path = Path(__file__).parent / "src" / "calculator.py"
    with open(calc_path, 'r') as f:
        content = f.read()
    
    # Apply fixes as they would be done via patches
    content = content.replace("return a - b  # (Should be a + b)", "return a + b")
    content = content.replace("return a - b - 1  # (Should be a - b)", "return a - b")
    content = content.replace("return a + b  # (Should be a * b)", "return a * b")
    content = content.replace("return a // b  # (Should handle b=0 and use float division a / b)",
                            "if b == 0:\n        raise ValueError(\"Cannot divide by zero\")\n    return a / b")
    
    with open(calc_path, 'w') as f:
        f.write(content)
    
    print("\n5. Agent runs tests to verify fix...")
    print("   Tool: RunTestsTool()")
    result = run_tests()
    
    if result["passed"]:
        print("   ✅ All tests passing!")
    else:
        print("   ❌ Tests still failing (would iterate)")
    
    print("\n📊 Summary:")
    print("   - Approach: Incremental patches with validation")
    print("   - Changes: Only modified specific buggy lines")
    print("   - Safety: High (preflight checks, critic review)")
    print("   - Tracking: Full diff history and Git commits")
    
    return result["passed"]

def compare_approaches():
    """Compare both approaches side by side."""
    print("\n" + "=" * 60)
    print("📊 COMPARISON SUMMARY")
    print("=" * 60)
    
    comparison = """
    ┌─────────────────────┬──────────────────────────┬──────────────────────────┐
    │ Aspect              │ Current Implementation  │ Proposed Implementation │
    ├─────────────────────┼──────────────────────────┼──────────────────────────┤
    │ Change Method       │ File replacement         │ Unified diff patches     │
    │ Safety Checks       │ Basic path blocking      │ Multi-layer validation   │
    │ Review Process      │ None                     │ Critic review            │
    │ Change Tracking     │ None                     │ Git commits with diffs   │
    │ Rollback Support    │ Manual only              │ Automatic on failure     │
    │ Iteration Strategy  │ Replace until works      │ Incremental refinement   │
    │ Token Usage         │ High (full files)        │ Low (only diffs)         │
    │ Error Recovery      │ Limited                  │ Robust with feedback     │
    └─────────────────────┴──────────────────────────┴──────────────────────────┘
    """
    print(comparison)
    
    print("\n🎯 Key Advantages of Proposed Implementation:")
    print("   1. Safer - validates patches before applying")
    print("   2. More efficient - only changes what's needed")
    print("   3. Better tracking - full history of changes")
    print("   4. Smarter iteration - learns from critic feedback")
    print("   5. Production-ready - handles edge cases gracefully")

def main():
    """Run the demonstration."""
    print("=" * 60)
    print("🚀 Nova CI Rescue Implementation Comparison Demo")
    print("=" * 60)
    
    # Save original buggy code
    original = save_original()
    
    # Show initial failing state
    print("\n📝 Initial State:")
    print("   File: src/calculator.py (with 4 bugs)")
    result = run_tests()
    if not result["passed"]:
        print("   ❌ Tests failing (as expected)")
    
    try:
        # Demo current implementation
        restore_original()
        current_success = demo_current_implementation()
        
        # Demo proposed implementation  
        restore_original()
        proposed_success = demo_proposed_implementation()
        
        # Compare approaches
        compare_approaches()
        
        # Final verification
        print("\n✅ Final Verification:")
        final_result = run_tests(verbose=True)
        
    finally:
        # Clean up - restore original for future demos
        restore_original()
    
    print("\n" + "=" * 60)
    print("✨ Demo Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
