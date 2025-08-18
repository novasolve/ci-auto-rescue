# Loop Prevention Fix Proposal

Based on the Deep Agent analysis, here are the recommended fixes:

## 1. Change Skip Message Prefixes

The analysis confirms tools return "error strings" for violations, but our skip messages aren't actual errors. The agent is misinterpreting them.

**Current**:

```python
return f"ERROR: File already opened (duplicate invocation skipped)"
```

**Proposed**:

```python
return f"SKIP: File already opened - proceeding with cached content"
```

## 2. Update Agent Prompts

Add explicit guidance about skip messages to the system prompt:

```python
SYSTEM_PROMPT = """
...
## IMPORTANT: Understanding Tool Responses

- If a tool returns "SKIP:" it means the action was already completed and you should proceed with the cached result
- These are NOT errors - they prevent redundant operations
- When you see "SKIP: File already opened", use the content from your previous observation
- Continue with your plan using the information you already have
...
"""
```

## 3. Enhanced State Context

The analysis shows state is used for coordination. We should make skip responses more informative:

```python
def _run(self, path: str) -> str:
    if self.state and (self.name, path, self.state.modifications_count) in self.state.used_actions:
        # Instead of just skipping, provide context
        return (
            f"SKIP: File '{path}' already opened in current iteration.\n"
            f"Proceed with the file content from your previous observation."
        )
```

## 4. Align with ReAct Pattern

The analysis confirms the ReAct pattern expects:

- **Thought**: Decide what to do
- **Action**: Use a tool
- **Observation**: Get result
- **Thought**: Interpret and continue

Our skip messages should clearly indicate the agent can continue thinking rather than retry:

```python
# In each tool's skip response
return "SKIP: [Action already performed]. Continue with next step in your plan."
```

## 5. Fix Critic's Patch Parsing

The analysis mentions the critic performs "semantic and safety analysis on diffs". The current issues with "incomplete patch" rejections suggest the critic needs better diff parsing:

```python
# In CriticReviewTool
def _parse_patch(self, patch_str: str) -> bool:
    # Add more robust parsing for different patch formats
    # Handle edge cases like empty context lines
    # Better detection of actual changes vs. format issues
```

## Implementation Priority

1. **Immediate**: Change all "ERROR:" prefixes to "SKIP:" in loop prevention returns
2. **High**: Update system prompts to explain skip behavior
3. **Medium**: Enhance critic's patch parsing logic
4. **Low**: Add more context to skip messages

This aligns with the analysis showing the Deep Agent should work in "one continuous session" without getting stuck on prevented duplicates.
