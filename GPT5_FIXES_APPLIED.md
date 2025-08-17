# GPT-5 Loop Issue - Fixes Applied

## Summary

I've identified and fixed the issue causing GPT-5 to get stuck in planning loops. The agent was repeatedly creating TODOs without progressing to actual implementation.

## Root Cause

The issue was caused by three main factors:

1. **Confusing Tool Responses**: The `plan_todo` tool returned "Plan noted" which GPT-5 interpreted as task completion
2. **Parser Confusion**: The "Invalid or incomplete response" tool was confusing the agent
3. **Missing Guidance**: The system prompt didn't explicitly state that planning is just the first step

## Fixes Applied

### 1. Updated Tool Responses

**File**: `src/nova/agent/unified_tools.py`

Changed `plan_todo` to return more directive guidance:

```python
# Before:
return f"Plan noted: {todo}"

# After:
return "Plan recorded. Now proceed to implement the fixes: use 'open_file' to read the source files containing the broken functions."
```

### 2. Removed Confusing Tool

**File**: `src/nova/agent/unified_tools.py`

Removed the "Invalid or incomplete response" tool that was causing confusion.

### 3. Enhanced System Prompt

**File**: `src/nova/agent/deep_agent.py`

Added explicit instructions about continuing after planning:

```
IMPORTANT: After using plan_todo, you MUST continue with the next action!
Creating a plan is just the first step. After planning, immediately:
- Use 'open_file' to read the source files
- Use 'critic_review' to review your proposed changes
- Use 'apply_patch' or 'write_file' to make changes
- Use 'run_tests' to verify fixes
NEVER stop after just creating a plan!
```

### 4. Improved Parser Logic

**File**: `src/nova/agent/deep_agent.py`

Enhanced `GPT5ReActOutputParser` to:

- Detect when the agent tries to stop after planning
- Force continuation with the next logical action
- Handle premature "Final Answer" responses that are actually requests for permission

## Expected Behavior After Fixes

1. Agent creates a plan with `plan_todo`
2. Receives directive response to continue
3. Immediately proceeds to `open_file` to inspect code
4. Continues through the workflow to completion

## Testing Recommendation

Run the same test again:

```bash
cd /Users/seb/GPT5/working/ci-auto-rescue
python -m nova fix examples/demos/demo_broken_project --model gpt-5 --verbose
```

The agent should now:

- Create the plan
- Open the source files
- Make the necessary fixes
- Run tests to verify
- Complete successfully

## Future Improvements

If issues persist, consider:

1. Creating a GPT-5-specific agent type
2. Using more structured prompts
3. Adding state tracking to prevent loops
4. Implementing a maximum retry count for planning
