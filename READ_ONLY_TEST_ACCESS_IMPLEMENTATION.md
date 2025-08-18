# Read-Only Test File Access Implementation

## Summary

Implemented read-only access to test files in Nova CI-Rescue, allowing the Deep Agent to read test files for better context while maintaining the safety restriction that prevents modifying test files.

## Changes Made

### 1. Configuration Setting

- Added `allow_test_file_read` to `NovaSettings` in `src/nova/config.py`
- Default value: `True` (test files can be read)
- Environment variable: `NOVA_ALLOW_TEST_READ`
- Can be set to `false` to restore the previous behavior of blocking all test file access

### 2. OpenFileTool Updates

- Modified `OpenFileTool` class in `src/nova/agent/unified_tools.py`
- Added `settings` field to store Nova settings
- Updated `_run` method to:
  - Check if a file is a test file first
  - If it's a test file and `allow_test_file_read=True`, allow reading
  - If it's a test file and `allow_test_file_read=False`, block access with helpful hints
  - Add a header comment to test files indicating they are read-only
  - For non-test files, apply normal BLOCKED_PATTERNS restrictions

### 3. WriteFileTool Unchanged

- Write restrictions remain unchanged
- Test files are always blocked from modification
- This ensures the agent cannot alter tests to make them pass

### 4. Tool Creation Updates

- Updated `create_default_tools()` to accept optional `settings` parameter
- If no settings provided, falls back to `get_settings()`
- Updated `NovaDeepAgent` to pass settings when creating tools

## Usage

### Enable Test File Reading (Default)

```bash
# Default behavior - test files can be read
nova fix

# Or explicitly enable via environment variable
export NOVA_ALLOW_TEST_READ=true
nova fix
```

### Disable Test File Reading

```bash
# Restore original behavior - block all test file access
export NOVA_ALLOW_TEST_READ=false
nova fix
```

### In Configuration File

```yaml
# nova.config.yml
allow_test_file_read: true # or false
```

## Benefits

1. **Better Context**: The agent can now see what tests expect, making it easier to fix issues correctly on the first try
2. **Deterministic Fixes**: Instead of inferring from error messages, the agent can see exact assertions
3. **Safety Maintained**: Test files can never be modified, only read
4. **Clear Indication**: Test files are clearly marked with a header comment when read
5. **Backward Compatible**: Can be disabled to restore original behavior

## Example Output

When the agent reads a test file:

```python
# TEST FILE (READ-ONLY): test_exceptions.py
# DO NOT MODIFY TEST FILES - Fix the source code to make tests pass

"""
Test file for exception handling.
"""
...
```

## Testing

Verified that:

- ✅ Test files can be read when `allow_test_file_read=True`
- ✅ Test files are blocked when `allow_test_file_read=False`
- ✅ Test files can never be written to (always blocked)
- ✅ Non-test files work normally
- ✅ BLOCKED_PATTERNS still apply to non-test files
