#!/usr/bin/env python3
"""
Demo: Using SafePatchManager for enforced patch review workflow
===============================================================

This demo shows how SafePatchManager ensures patches are reviewed before application.
"""

from pathlib import Path
from nova.agent.safe_patch_manager import SafePatchManager
from nova.telemetry.logger import JSONLLogger
from nova.config import SafetyConfig

# Mock LLM for demo (in real usage, use actual ChatOpenAI/ChatAnthropic)
class MockLLM:
    def __init__(self, approve_patches=True):
        self.approve_patches = approve_patches


def demo_safe_patch_workflow():
    """Demonstrate the safe patch workflow."""
    
    # Initialize components
    telemetry = JSONLLogger(Path("demo_patch_audit.jsonl"))
    llm = MockLLM(approve_patches=True)
    
    # Create SafePatchManager
    patch_manager = SafePatchManager(
        repo_path=Path("."),
        llm=llm,
        telemetry=telemetry,
        safety_config=SafetyConfig(max_lines_changed=100),
        verbose=True,
        allow_override=False  # Production setting
    )
    
    # Example 1: Good patch that should be approved
    good_patch = """--- a/src/calculator.py
+++ b/src/calculator.py
@@ -10,7 +10,7 @@ class Calculator:
     
     def add(self, a: float, b: float) -> float:
         '''Add two numbers.'''
-        return a - b  # Bug: wrong operation
+        return a + b  # Fixed: correct operation
     
     def subtract(self, a: float, b: float) -> float:
         '''Subtract b from a.'''"""
    
    print("=" * 60)
    print("Example 1: Applying a good patch")
    print("=" * 60)
    
    # Mock the critic approval
    patch_manager.critic_tool._run = lambda patch_diff, failing_tests=None: (
        "APPROVED: Fixes the addition operation bug correctly"
    )
    # Mock the apply success
    patch_manager.apply_tool._run = lambda patch_diff: (
        "SUCCESS: Patch applied and committed"
    )
    
    result = patch_manager.review_and_apply(
        patch_diff=good_patch,
        failing_tests_context="test_calculator.py::test_add - AssertionError: 5 != 1"
    )
    
    print(f"\nResult: {result}")
    
    # Example 2: Dangerous patch that should be rejected
    dangerous_patch = """--- a/tests/test_calculator.py
+++ b/tests/test_calculator.py
@@ -15,7 +15,7 @@ class TestCalculator:
     def test_add(self):
         calc = Calculator()
         result = calc.add(2, 3)
-        assert result == 5
+        assert result == -1  # Changed test instead of fixing code!"""
    
    print("\n" + "=" * 60)
    print("Example 2: Attempting to apply a dangerous patch")
    print("=" * 60)
    
    # Mock the critic rejection
    patch_manager.critic_tool._run = lambda patch_diff, failing_tests=None: (
        "REJECTED: Modifies test file - tests should not be changed"
    )
    
    result = patch_manager.review_and_apply(
        patch_diff=dangerous_patch,
        failing_tests_context="test_calculator.py::test_add - AssertionError"
    )
    
    print(f"\nResult: {result}")
    print("Note: Patch was NOT applied because it was rejected!")
    
    # Example 3: Override attempt (should fail with allow_override=False)
    print("\n" + "=" * 60)
    print("Example 3: Attempting to override rejection")
    print("=" * 60)
    
    result = patch_manager.review_and_apply(
        patch_diff=dangerous_patch,
        failing_tests_context="test_calculator.py::test_add - AssertionError",
        force=True  # Try to force it
    )
    
    print(f"\nResult: {result}")
    print("Note: Override was denied because allow_override=False!")
    
    # Show statistics
    print("\n" + "=" * 60)
    print("Patch Review Statistics")
    print("=" * 60)
    
    stats = patch_manager.get_stats()
    print(f"Total reviews: {stats['total_reviews']}")
    print(f"Approved: {stats['approved']}")
    print(f"Rejected: {stats['rejected']}")
    print(f"Applied: {stats['applied']}")
    
    # Show review history
    print("\n" + "=" * 60)
    print("Review History")
    print("=" * 60)
    
    history = patch_manager.get_review_history()
    for i, review in enumerate(history, 1):
        print(f"\nReview {i}:")
        print(f"  Decision: {review['decision']}")
        print(f"  Reason: {review['reason']}")
        print(f"  Patch size: {review['patch_size']} lines")


if __name__ == "__main__":
    demo_safe_patch_workflow()
