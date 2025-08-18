# Deterministic Multi-Failure Fix Implementation

## Overview

Implemented a deterministic strategy for Nova CI-Rescue to fix all failing tests in a single cycle, rather than iteratively fixing them one-by-one. This approach reduces the number of test runs, minimizes the risk of partial fixes, and ensures all failures are addressed comprehensively.

## Key Changes

### 1. Enhanced Planning Prompt (`src/nova/agent/llm_client.py`)

Updated `build_planner_prompt()` to be more explicit about fixing all failures at once:

- **Clear Instructions**: Added "DETERMINISTIC MULTI-FAILURE FIX STRATEGY" header
- **Complete Context**: Shows all failing tests (up to 20) with detailed error messages
- **Explicit Requirements**: Instructions to fix ALL tests in ONE cycle
- **Better Error Extraction**: Looks for actual assertion errors, not just first line
- **Comprehensive Planning**: Requires enumerating a fix for EACH failing function

Key improvements:

```python
prompt += "🎯 DETERMINISTIC MULTI-FAILURE FIX STRATEGY\n\n"
prompt += "You have multiple failing tests. Your goal is to fix ALL of them in ONE CYCLE.\n"
prompt += "Do NOT fix them one-by-one. Plan and execute ALL fixes before running tests again.\n\n"
```

### 2. Updated Agent Workflow (`src/nova/agent/deep_agent.py`)

Modified the Deep Agent's system prompt to emphasize the new workflow:

- **Sequential Implementation**: Fix all issues before running tests
- **No Intermediate Testing**: Explicitly forbids testing after each fix
- **Clear Implementation Order**: Step-by-step process for multi-fix cycle
- **One-Shot Verification**: Run tests only after all fixes are applied

New workflow:

1. Run tests once to see all failures
2. Plan fixes for EACH failing function
3. Apply ALL fixes sequentially
4. Run tests ONCE to verify all fixes
5. Iterate only if needed

### 3. Configuration Enhancements (`src/nova/config.py`)

Added new configuration options:

- `agent_max_iterations`: Increased to 20 (from 15) to support more tool calls
- `deterministic_fix`: Boolean flag to enable/disable the strategy (default: True)
- Environment variables:
  - `NOVA_AGENT_MAX_ITERATIONS`: Control max tool calls
  - `NOVA_DETERMINISTIC_FIX`: Enable/disable deterministic fixing

### 4. Dynamic Iteration Limits

Updated all `AgentExecutor` initialization calls to use the configurable limit:

```python
max_iterations=self.settings.agent_max_iterations
```

This ensures the agent has enough iterations to fix all issues without hitting limits.

## Benefits

1. **Efficiency**: Reduces test runs from N+1 to 2 (initial + verification)
2. **Reliability**: Avoids partial fixes and state inconsistencies
3. **Speed**: Faster overall execution by batching fixes
4. **Coherence**: Single patch covers all changes
5. **Determinism**: Predictable behavior across runs

## Usage

### Default Behavior (Deterministic Fix Enabled)

```bash
nova fix
```

### With Environment Variables

```bash
export NOVA_DETERMINISTIC_FIX=true
export NOVA_AGENT_MAX_ITERATIONS=25
nova fix
```

### In Configuration File

```yaml
# nova.config.yml
deterministic_fix: true
agent_max_iterations: 20
allow_test_file_read: true # Helps agent understand test expectations
```

## Example Scenario: demo_exceptions

The `demo_exceptions` project has 5 failing functions:

1. `divide_numbers` - Missing error handling
2. `validate_age` - Missing validation logic
3. `process_data` - Missing data checks
4. `FileProcessor` - Missing file operations
5. `safe_conversion` - Missing type conversion

### Old Behavior (One-by-One)

1. Run tests → See 5 failures
2. Fix `divide_numbers` → Run tests → 4 failures remain
3. Fix `validate_age` → Run tests → 3 failures remain
4. Fix `process_data` → Run tests → 2 failures remain
5. Fix `FileProcessor` → Run tests → 1 failure remains
6. Fix `safe_conversion` → Run tests → All pass

**Total: 6 test runs, 5 fix cycles**

### New Behavior (Deterministic)

1. Run tests → See 5 failures
2. Plan fixes for all 5 functions
3. Apply all 5 fixes sequentially
4. Run tests → All pass

**Total: 2 test runs, 1 fix cycle**

## Testing

Created `test_deterministic_fix.py` to verify the implementation:

- Runs Nova on demo projects
- Counts test executions
- Analyzes telemetry
- Verifies all fixes applied in one cycle

## Future Enhancements

1. **Parallel File Editing**: Open multiple files simultaneously
2. **Batch Patch Generation**: Create one unified diff for all changes
3. **Smart Grouping**: Group related failures for more efficient fixing
4. **Progress Tracking**: Show which fixes have been applied
5. **Rollback Strategy**: Revert all changes if any fix fails

## Conclusion

The deterministic multi-failure fix strategy significantly improves Nova's efficiency and reliability when dealing with multiple test failures. By planning and executing all fixes before re-running tests, we reduce iteration overhead and ensure comprehensive solutions.
