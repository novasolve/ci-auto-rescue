# Nova Fixes Applied

This document summarizes the fixes applied to address the issues identified in the diagnosis.

## Fix 1: Path Resolution - Automatically Check src/ Directory

**File**: `src/nova/agent/unified_tools.py`
**Lines**: 211-227

**Change**: Enhanced `OpenFileTool._run()` to automatically try common source directories when a file is not found:

```python
except FileNotFoundError:
    # If file not found, try common source directories
    src_alternatives = [
        Path("src") / path,
        Path("lib") / path,
        Path("app") / path,
    ]
    for alt_path in src_alternatives:
        if alt_path.exists():
            try:
                content = alt_path.read_text()
                if len(content) > 50000:  # 50KB limit
                    content = content[:50000] + "\n... (truncated)"
                return f"# Note: Found file at {alt_path}\n{content}"
            except Exception:
                continue
    return f"ERROR: File not found: {path} (also checked: src/{path}, lib/{path}, app/{path})"
```

**Result**: When the agent tries to open `broken.py` and it's not found at the root, it will automatically check `src/broken.py`, `lib/broken.py`, and `app/broken.py`.

## Fix 2: JSON Parsing Bug

**File**: `src/nova/agent/unified_tools.py` 
**Lines**: 359-407

**Change**: Modified the local test runner fallback to set `result` as a dict instead of returning JSON strings directly:

```python
# Before: return json.dumps({...})
# After: result = {...}
```

This ensures that when the code later calls `result.get()`, it's operating on a dict, not a string.

**Result**: The "'str' object has no attribute 'get'" error is eliminated.

## Fix 3: Improved Agent Guidance

**File**: `src/nova/agent/deep_agent.py`
**Lines**: Multiple sections

### System Prompt Enhancement (Lines 379-386):
Added explicit guidance about Python imports:
```
"6. **PYTHON IMPORTS**: When resolving Python imports:\n"
"   - Check test files for sys.path modifications (e.g., sys.path.insert)\n"
"   - If tests import 'from module_name import ...', look for:\n"
"     * module_name.py in the same directory\n"
"     * module_name.py in directories added to sys.path\n"
"     * module_name/__init__.py for packages\n"
"   - Common patterns: src/module_name.py, lib/module_name.py\n"
"   - NEVER guess filenames like 'module_name_module.py' or 'broken_module.py'\n\n"
```

### Workflow Enhancement (Lines 387-397):
Updated the workflow to emphasize analyzing error messages:
```
"1. ANALYZE: Read error messages to identify failing functions/methods\n"
"   - Look for function names like 'divide_numbers', 'calculate_average', etc.\n"
"   - Note the module names from imports (e.g., 'from broken import ...')\n"
"2. INVESTIGATE: Open SOURCE files containing these functions\n"
"   - NEVER try to open test files - they are blocked\n"
"   - Try module.py first, then src/module.py if not found\n"
```

### Task Instructions Enhancement (Lines 627-653):
Made it crystal clear that test files should not be opened:
```
"## IMPORTANT NOTES:\n"
"- Test files (tests/, test_*.py, *_test.py) are READ-ONLY and BLOCKED - don't try to open them\n"
"- Use the error messages and stack traces to understand what needs fixing\n"
"- Look for function/method names in the errors and fix those in the source files\n"
"- Common source locations: src/module.py, lib/module.py, module.py\n"
```

**Result**: The agent will no longer attempt to open test files and will instead focus on the error messages to identify what needs to be fixed.

## Testing the Fixes

To verify these fixes work correctly:

```bash
# 1. Ensure Docker is running (optional but recommended)
./setup_docker_sandbox.sh

# 2. Test with the demo project
nova fix examples/demos/demo_broken_project/

# Expected behavior:
# - Agent identifies failing tests from error messages
# - Agent opens src/broken.py (not broken_module.py)
# - Agent fixes all 6 functions based on test expectations
# - No JSON parsing errors occur
# - All tests pass
```

## Summary

These fixes address all three issues identified in the diagnosis:

1. ✅ **Path Resolution**: Agent now automatically checks src/ directory
2. ✅ **JSON Parsing**: Fixed the bug where JSON strings were treated as dicts
3. ✅ **Agent Guidance**: Clear instructions to not open test files

The Nova agent should now be able to successfully fix the demo_broken_project without encountering the previous errors.
