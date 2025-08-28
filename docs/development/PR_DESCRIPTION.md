# Fix critical Nova issues: source file discovery, imports, datetime arithmetic, and more

## Summary

This PR applies a comprehensive fix pack addressing multiple critical issues preventing Nova from working correctly.

## Fixes Applied

### 🔴 Critical Fixes

1. **Source File Discovery (Fix Pack A)**

   - Replaced regex-based import scanning with AST parsing
   - Handles relative imports (e.g., `from .calculator import X`)
   - Fixes "No source files identified" issue
   - Files: `src/nova/agent/llm_agent_enhanced.py`

2. **Import Error Fix**

   - Fixed `ImportError: cannot import name 'settings' from 'nova.config'`
   - Added backward-compatible `settings` export to config module
   - Updated `cli.py` to use `get_settings()` consistently
   - Files: `src/nova/config.py`, `src/nova/cli.py`

3. **Datetime-Float Arithmetic (Fix Pack D)**

   - Created `src/nova/tools/datetime_utils.py` with safe datetime handling
   - Fixed all instances of datetime-float arithmetic causing TypeErrors
   - Files: `cli.py`, `state.py`, `reflect.py`, `lock.py`

4. **Console Variable Scope Error**
   - Fixed "cannot access local variable console" error in patch application
   - Files: `src/nova/nodes/apply_patch.py`, `src/nova/tools/fs.py`

### 🟡 Other Important Fixes

5. **GPT-5 Temperature**

   - Reverted to hardcoded temperature=1.0 for GPT-5 (API requirement)
   - Files: `src/nova/agent/llm_client.py`

6. **Path Doubling Bug**

   - Fixed test file paths with duplicated segments
   - Files: `src/nova/agent/llm_agent_enhanced.py`

7. **Submodule Cleanup Utility**

   - Added `scripts/clean_submodules.py` to handle git submodule warnings

8. **Enhanced Source File Discovery**
   - Added support for common directories: `src/`, `lib/`, `app/`, `core/`, `modules/`
   - Derives module names from test file names
   - Better debug logging

## Files Changed

### New Files

- `src/nova/tools/datetime_utils.py` - Safe datetime handling utilities
- `scripts/clean_submodules.py` - Submodule cleanup utility

### Modified Files

- `src/nova/agent/llm_agent_enhanced.py` - AST-based source discovery, path fixes
- `src/nova/config.py` - Added `settings` export for backward compatibility
- `src/nova/cli.py` - Fixed imports, datetime handling
- `src/nova/agent/llm_client.py` - GPT-5 temperature handling
- `src/nova/nodes/apply_patch.py` - Console scope fix
- `src/nova/tools/fs.py` - Console import fix
- `src/nova/agent/state.py` - Datetime handling
- `src/nova/nodes/reflect.py` - Datetime handling
- `src/nova/tools/lock.py` - Datetime handling
- `BUG_REPORT.md` - Updated with critical issues
- `BUG_REPORT_COMPREHENSIVE.md` - Comprehensive issue tracking

## Testing

All fixes have been tested and verified to resolve their respective issues. The datetime fix in particular resolves the critical TypeError that was blocking Nova runs.

## Commit History

Key commits in this PR:

1. Fix console variable scope error in patch application
2. Apply AST-based source file discovery and critic fallback fixes
3. Enhance source file discovery and add submodule cleanup utility
4. Fix settings import error and update comprehensive bug report
5. Apply comprehensive fix pack: A, B, D, E from detailed analysis
6. Fix remaining datetime-float arithmetic issues
7. Revert temperature fix for GPT-5 - API requires temperature=1.0

## Related Issues

- Fixes "No source files identified" issue
- Fixes import error: cannot import name 'settings'
- Fixes datetime-float arithmetic crash
- Fixes console variable scope error
- Partially addresses test detection and bare exception handler issues

---

_This PR consolidates multiple critical fixes identified through extensive debugging and analysis._
