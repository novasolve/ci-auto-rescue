#!/usr/bin/env python3
"""
Demonstration of how the proposed LangChain ReAct-based implementation
would fix the calculator bugs using unified diffs and critic review.
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

class MockNovaDeepAgent:
    """
    Simulated version of the proposed LangChain-based NovaDeepAgent.
    This demonstrates the workflow without requiring full LangChain setup.
    """
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.iteration = 0
        self.max_iterations = 3
        
    def run_tests(self) -> Dict:
        """Run tests and return failure analysis."""
        print("\n🔧 Running tests...")
        result = subprocess.run(
            ["pytest", "tests/test_calculator.py", "-v", "--tb=short"],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        
        failures = self._parse_failures(result.stdout + result.stderr)
        
        if result.returncode == 0:
            print("✅ All tests passing!")
            return {"status": "success", "failures": []}
        else:
            print(f"❌ {len(failures)} test(s) failing")
            for f in failures[:3]:
                print(f"   - {f['test']}: {f['error'][:60]}...")
            return {"status": "failing", "failures": failures}
    
    def _parse_failures(self, output: str) -> List[Dict]:
        """Parse pytest output to extract failure details."""
        failures = []
        
        # Pattern to match test failures
        failure_pattern = r"FAILED tests/test_calculator.py::(\w+)"
        assertion_pattern = r"assert (.+) == (.+)"
        
        for match in re.finditer(failure_pattern, output):
            test_name = match.group(1)
            
            # Extract assertion details
            assertion_match = re.search(assertion_pattern, output)
            if assertion_match:
                actual = assertion_match.group(1)
                expected = assertion_match.group(2)
                error = f"Expected {expected} but got {actual}"
            else:
                error = "Assertion failed"
            
            failures.append({
                "test": test_name,
                "error": error,
                "file": "tests/test_calculator.py"
            })
        
        return failures
    
    def generate_patch(self, failures: List[Dict]) -> str:
        """
        Generate a unified diff patch to fix the failures.
        In the real implementation, this would be done by the LLM.
        """
        print("\n🤔 Analyzing failures and generating patch...")
        
        # Simulate LLM reasoning about the failures
        print("   Thought: The test failures indicate:")
        print("   - add() is using subtraction instead of addition")
        print("   - subtract() has an off-by-one error")
        print("   - multiply() is using addition instead of multiplication")
        print("   - divide() uses integer division and lacks zero check")
        
        # Generate the unified diff patch
        patch = '''--- a/src/calculator.py
+++ b/src/calculator.py
@@ -6,18 +6,22 @@
 def add(a, b):
-    """Add two numbers."""
-    # Bug: incorrect operation used
-    return a - b  # (Should be a + b)
+    """Add two numbers."""
+    # Bug: incorrect operation used
+    return a + b
 
 def subtract(a, b):
-    """Subtract b from a."""
-    # Bug: off-by-one error in subtraction
-    return a - b - 1  # (Should be a - b)
+    """Subtract b from a."""
+    # Bug: off-by-one error in subtraction
+    return a - b
 
 def multiply(a, b):
-    """Multiply two numbers."""
-    # Bug: incorrect operation used
-    return a + b  # (Should be a * b)
+    """Multiply two numbers."""
+    # Bug: incorrect operation used
+    return a * b
 
 def divide(a, b):
-    """Divide a by b."""
-    # Bug: missing zero division check and wrong division behavior
-    return a // b  # (Should handle b=0 and use float division a / b)
+    """Divide a by b."""
+    # Bug: missing zero division check and wrong division behavior
+    if b == 0:
+        raise ValueError("Cannot divide by zero")
+    return a / b'''
        
        print("   Action: ApplyPatch")
        print("   Generated patch with 4 function fixes")
        
        return patch
    
    def critic_review(self, patch: str, failures: List[Dict]) -> Tuple[bool, str]:
        """
        Simulate the CriticReviewTool evaluating the patch.
        In real implementation, this would use an LLM.
        """
        print("\n🔍 Critic reviewing patch...")
        
        # Simulate LLM critic analysis
        print("   Analyzing patch correctness...")
        print("   - ✓ Fixes add() to use addition")
        print("   - ✓ Fixes subtract() to remove off-by-one")
        print("   - ✓ Fixes multiply() to use multiplication")
        print("   - ✓ Fixes divide() with float division and zero check")
        
        # In this demo, approve the patch
        approved = True
        reason = "Patch correctly addresses all identified bugs"
        
        if approved:
            print(f"   ✅ APPROVED: {reason}")
        else:
            print(f"   ❌ REJECTED: {reason}")
        
        return approved, reason
    
    def apply_patch(self, patch: str) -> bool:
        """
        Apply the unified diff patch to the repository.
        This demonstrates the ApplyPatchTool functionality.
        """
        print("\n📝 Applying patch...")
        
        # Save patch to temporary file
        patch_file = self.repo_path / "fix.patch"
        patch_file.write_text(patch)
        
        # Apply using git apply (or patch command)
        try:
            result = subprocess.run(
                ["patch", "-p1"],
                input=patch,
                text=True,
                cwd=self.repo_path,
                capture_output=True
            )
            
            if result.returncode == 0:
                print("   ✅ Patch applied successfully")
                patch_file.unlink()  # Clean up
                return True
            else:
                print(f"   ❌ Patch failed: {result.stderr}")
                patch_file.unlink()  # Clean up
                return False
        except Exception as e:
            print(f"   ❌ Error applying patch: {e}")
            if patch_file.exists():
                patch_file.unlink()
            return False
    
    def run(self) -> Dict:
        """
        Main agent loop demonstrating the ReAct pattern.
        """
        print("=" * 60)
        print("🤖 Nova Deep Agent (Proposed Implementation Demo)")
        print("=" * 60)
        
        while self.iteration < self.max_iterations:
            self.iteration += 1
            print(f"\n=== Iteration {self.iteration}/{self.max_iterations} ===")
            
            # Step 1: Run tests to check current state
            test_result = self.run_tests()
            
            if test_result["status"] == "success":
                return {
                    "status": "success",
                    "iterations": self.iteration,
                    "message": "All tests fixed!"
                }
            
            failures = test_result["failures"]
            
            # Step 2: Generate a patch to fix failures
            patch = self.generate_patch(failures)
            
            # Step 3: Review patch with critic
            approved, reason = self.critic_review(patch, failures)
            
            if not approved:
                print(f"\n⚠️ Patch rejected: {reason}")
                print("   Generating new patch...")
                continue
            
            # Step 4: Apply the approved patch
            if self.apply_patch(patch):
                print("\n🔄 Re-running tests to verify fix...")
            else:
                print("\n⚠️ Patch application failed, trying again...")
                continue
        
        # Max iterations reached
        return {
            "status": "max_iterations",
            "iterations": self.iteration,
            "message": "Maximum iterations reached without fixing all tests"
        }


def show_fixed_code():
    """Display the fixed calculator code."""
    calc_file = Path(__file__).parent / "src" / "calculator.py"
    print("\n📄 Fixed calculator.py:")
    print("-" * 40)
    with open(calc_file, 'r') as f:
        print(f.read())
    print("-" * 40)


def main():
    """Run the demonstration."""
    repo_path = Path(__file__).parent
    
    # Create agent and run
    agent = MockNovaDeepAgent(repo_path)
    result = agent.run()
    
    # Show results
    print("\n" + "=" * 60)
    print("📊 Final Result:")
    print(f"   Status: {result['status']}")
    print(f"   Iterations used: {result['iterations']}")
    print(f"   {result['message']}")
    
    if result['status'] == 'success':
        show_fixed_code()
        
        # Verify by running all tests
        print("\n🧪 Running complete test suite to verify:")
        subprocess.run(
            ["pytest", "tests/test_calculator.py", "-v"],
            cwd=repo_path
        )
    
    print("\n" + "=" * 60)
    print("✨ Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
