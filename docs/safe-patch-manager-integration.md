# SafePatchManager Integration Guide

## Overview

The `SafePatchManager` provides programmatic enforcement of the critic review workflow, ensuring that no patch can be applied without passing through review first. This adds a hard safety guarantee beyond relying on LLM prompt compliance.

## Integration Options

### Option 1: Direct Integration in NovaDeepAgent (Recommended)

Modify the agent to use SafePatchManager for all patch operations:

```python
# In src/nova/agent/deep_agent.py

from nova.agent.safe_patch_manager import create_safe_patch_manager

class NovaDeepAgent:
    def __init__(self, ...):
        # ... existing init code ...

        # Create SafePatchManager instance
        self.patch_manager = create_safe_patch_manager(
            state=self.state,
            telemetry=self.telemetry,
            llm=self.llm,
            safety_config=self.safety_config,
            verbose=self.verbose,
            allow_override=False  # Never allow override in production
        )

    def apply_patch_with_review(self, patch_diff: str, failing_tests: str = "") -> Dict[str, Any]:
        """
        Apply a patch using the SafePatchManager to ensure review.
        This method can be exposed as a tool or called internally.
        """
        return self.patch_manager.review_and_apply(
            patch_diff=patch_diff,
            failing_tests_context=failing_tests
        )
```

### Option 2: Custom Tool Wrapper

Create a combined tool that replaces separate critic_review and apply_patch tools:

```python
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

class ReviewAndApplyInput(BaseModel):
    patch_diff: str = Field(..., description="Unified diff patch to review and apply")
    failing_tests: str = Field(default="", description="Context about failing tests")

class ReviewAndApplyTool(BaseTool):
    """Combined tool that enforces review before application."""
    name: str = "review_and_apply_patch"
    description: str = (
        "Review a patch and apply it if approved. "
        "Combines critic review and patch application in one atomic operation."
    )
    args_schema: Type[BaseModel] = ReviewAndApplyInput

    def __init__(self, patch_manager: SafePatchManager, **kwargs):
        super().__init__(**kwargs)
        self.patch_manager = patch_manager

    def _run(self, patch_diff: str, failing_tests: str = "") -> str:
        result = self.patch_manager.review_and_apply(
            patch_diff=patch_diff,
            failing_tests_context=failing_tests
        )

        if result["applied"]:
            return f"SUCCESS: Patch reviewed and applied. Review: {result['review_reason']}"
        else:
            return f"FAILED: {result['review_decision']} - {result['review_reason']}"
```

### Option 3: Orchestrator-Level Enforcement

Implement enforcement at the orchestration layer outside the agent:

```python
# In the main run loop
def run_nova_with_safe_patches(repo_path: Path, ...):
    agent = NovaDeepAgent(...)
    patch_manager = create_safe_patch_manager(...)

    for iteration in range(max_iterations):
        # Let agent work
        action = agent.get_next_action()

        # Intercept patch applications
        if action.tool == "apply_patch":
            # Force it through SafePatchManager instead
            result = patch_manager.review_and_apply(
                patch_diff=action.patch_diff,
                failing_tests_context=agent.state.current_failures
            )
            # Feed result back to agent
            agent.process_tool_result(result)
        else:
            # Let other tools run normally
            agent.execute_action(action)
```

## Configuration

### Basic Usage

```python
# Create with defaults (production settings)
patch_manager = SafePatchManager(
    repo_path=Path("."),
    llm=llm_instance,
    telemetry=logger,
    safety_config=SafetyConfig(),  # Uses default limits
    verbose=False,
    allow_override=False  # Never allow override in production
)

# Review and apply a patch
result = patch_manager.review_and_apply(
    patch_diff=unified_diff,
    failing_tests_context="test_add fails with AssertionError"
)

if result["applied"]:
    print(f"✅ Patch applied: {result['apply_result']}")
else:
    print(f"❌ Patch not applied: {result['review_reason']}")
```

### Development Mode

For development/testing, you might allow overrides:

```python
# Development settings with override capability
dev_patch_manager = SafePatchManager(
    repo_path=Path("."),
    llm=llm_instance,
    telemetry=logger,
    allow_override=True,  # Allows force=True flag
    verbose=True  # Show detailed output
)

# Force application despite rejection (dev only!)
result = dev_patch_manager.review_and_apply(
    patch_diff=risky_patch,
    force=True  # Will apply even if rejected
)
```

## Audit Trail

The SafePatchManager provides comprehensive logging:

```python
# Get review history
history = patch_manager.get_review_history()
for review in history:
    print(f"Decision: {review['decision']}, Reason: {review['reason']}")

# Get statistics
stats = patch_manager.get_stats()
print(f"Total reviews: {stats['total_reviews']}")
print(f"Approved: {stats['approved']}")
print(f"Rejected: {stats['rejected']}")
print(f"Applied: {stats['applied']}")
```

## Benefits

1. **Hard Enforcement**: Patches cannot bypass review, even if the LLM tries
2. **Audit Trail**: Every review decision and application is logged
3. **Override Control**: Clear mechanism for development/emergency overrides
4. **Statistics**: Track review patterns and success rates
5. **Integration Flexibility**: Multiple ways to integrate with existing code

## Migration Path

To migrate existing code:

1. Add SafePatchManager to your agent initialization
2. Replace direct `apply_patch` calls with `patch_manager.review_and_apply()`
3. Update tool descriptions to mention the combined workflow
4. Monitor logs to ensure the workflow is being followed

## Example Log Output

```
🔍 Running critic review on patch...
✅ Patch approved: Correctly fixes the addition bug
📝 Applying patch...
✅ SUCCESS: Patch applied successfully.

# Telemetry events:
{"event": "patch_review", "decision": "APPROVED", "reason": "Correctly fixes the addition bug", "patch_size": 6}
{"event": "patch_applied", "message": "SUCCESS: Patch applied successfully.", "override_used": false}
```
