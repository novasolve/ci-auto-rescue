# Nova CI-Rescue Comprehensive Bug Report

## 🔴 Critical Issues

### 1. **No Source Files Identified (MOST CRITICAL)**

- **Issue**: Nova cannot find source files to fix, resulting in blind patch generation
- **Symptoms**:
  - `[Nova Debug] Plan created with source files: []`
  - `⚠ No source files identified`
  - Empty plan generation with no approach or steps
- **Root Cause**: Nova only looks in project root, not in subdirectories like `src/`
- **Impact**: Nova generates random code without seeing actual bugs
- **Example**: In `demo_broken_project`, the actual file is at `src/calculator.py` but Nova looks for `calculator.py` in root
- **Status**: Fixed with AST-based source file discovery ✅ (Applied from fix pack A)

### 2. **Path Doubling Bug**

- **Issue**: Test file paths are incorrectly constructed with duplicated segments
- **Example**: `/Users/.../demo_broken_project/examples/demos/demo_broken_project/tests/test_calculator.py`
- **Impact**: Files cannot be found due to malformed paths
- **Location**: Path construction in `llm_agent_enhanced.py`
- **Status**: Fixed with path deduplication logic ✅

### 3. **GPT-5 Temperature Hardcoding**

- **Location**: Multiple files (`llm_agent_enhanced.py`, `pr_generator.py`, `llm_client.py`)
- **Issue**: Temperature is hardcoded to 1.0 for GPT-5 models
- **Impact**: Removes flexibility for different use cases (deterministic vs creative output)
- **Files**:
  - `src/nova/agent/llm_agent_enhanced.py:123`
  - `src/nova/tools/pr_generator.py:87`
  - `src/nova/agent/llm_client.py:128`
- **Status**: Fixed - temperature is now configurable ✅ (Applied from fix pack B)

### 4. **Bare Exception Handlers**

- **Issue**: Multiple places use bare `except:` which can hide critical errors
- **Impact**: Can mask SystemExit, KeyboardInterrupt, and other critical exceptions
- **Files**:
  - `src/nova/cli.py:538, 561`
  - `src/nova/nodes/apply_patch.py:91`
  - `src/nova/tools/pr_generator.py:264, 300`
  - `src/nova/agent/llm_client.py:177`

### 5. **Submodule Git Repository Warnings**

- **Issue**: Embedded git repositories causing warnings during commits
- **Paths**:
  - `examples/demos/demo_llm_repo`
  - `examples/demos/demo_nova_test`
  - `examples/demos/demo_test_repo`
  - `examples/sample_repos/nova_demo_workspace`
- **Status**: Cleanup script created ✅

### 6. **Import Error: 'settings' from nova.config**

- **Issue**: ImportError: cannot import name 'settings' from 'nova.config'
- **Root Cause**: `nova.config` exports `get_settings()` function, not `settings` variable
- **Files Involved**:
  - `src/nova/config.py` - Only exports `NovaSettings` class and `get_settings()` function
  - `src/nova/cli.py:90` - ❌ Incorrectly tries `from nova.config import settings`
  - `src/nova/cli.py:204` - Creates local `settings = NovaSettings()` instead of using `get_settings()`
- **Other files correctly use**: `llm_agent_enhanced.py`, `llm_client.py`, `llm_agent.py`
- **Status**: Fixed by using `get_settings()` consistently ✅

### 7. **Datetime - Float Arithmetic Error (CRITICAL - STILL BROKEN)**

- **Issue**: Despite multiple fix attempts, datetime arithmetic errors still occur
- **Error**: `unsupported operand type(s) for -: 'datetime.datetime' and 'float'`
- **Status**: CRITICAL - Fixes applied but error persists, blocking all nova runs
- **Fixed Files** (in PR fix/p0-bugs-cleanup):
  - `src/nova/cli.py:82-85, 542-545` - Added isinstance checks ✅
  - `src/nova/nodes/reflect.py:55-57` - Added isinstance checks ✅
- **Error Still Occurs**: After "⚠ No progress: 5 test(s) still failing"
- **Root Cause**: Mixed datetime-float arithmetic in multiple locations
- **Status**: Fixed with datetime_utils.py and safe datetime handling ✅ (Applied from fix pack D)
- **Fixed Files**:
  - `src/nova/cli.py` - Uses now_utc() and seconds_between()
  - `src/nova/agent/state.py` - Uses seconds_between()
  - `src/nova/nodes/reflect.py` - Uses seconds_between()
  - `src/nova/tools/lock.py` - Uses to_datetime() and seconds_between()

### 8. **JUnit Report Path Not Interpolated**

- **Issue**: Missing f-string prefix causes literal `{junit_report_path}` files
- **File**: `src/nova/runner/test_runner.py:68`
- **Impact**: Creates files named `{junit_report_path}` in demo directories
- **Fix**: Change `"--junit-xml={junit_report_path}"` to `f"--junit-xml={junit_report_path}"`
- **Status**: Fixed ✅

## 🟡 High Priority Issues

### 9. **Patch Truncation Handling**

- **Issue**: Fragile mechanism for handling truncated patches from LLM
- **File**: `src/nova/tools/patch_fixer.py`
- **Symptoms**: Warnings about truncation (line 141 in patch_fixer.py)
- **Risks**: Truncated patches could lead to syntax errors or logical errors
- **Impact**: Undermines Nova's core function of applying fixes reliably

### 10. **Resource Management**

- **Issue**: Temporary files and artifacts not consistently cleaned up
- **Details**:
  - `src/nova/nodes/apply_patch.py:73` - Temp file without guaranteed cleanup
  - `src/nova/tools/fs.py:414` - Patch files accumulate in .nova directory
  - `src/nova/runner/test_runner.py:54` - Temporary JSON report files
- **Impact**: File clutter and potential interference between runs

### 11. **JSON Parsing Without Proper Error Handling**

- **Issue**: Silent failures in JSON parsing with broad exception handling
- **Files**:
  - `src/nova/runner/test_runner.py:119`
  - `src/nova/cli.py:560`
- **Impact**: Wrong configurations or missing results without user notification

### 12. **Race Conditions in CI Environment**

- **Issue**: No locking or coordination for concurrent runs
- **Impact**: Parallel Nova processes can conflict and corrupt each other's work
- **Example**: Two GitHub Actions running nova fix simultaneously

### 13. **Nova Cannot Find Tests in Subfolders**

- **Issue**: Test discovery doesn't search recursively in subdirectories
- **Example**: Running `nova fix .` at project root misses tests in nested folders
- **Impact**: Major usability issue for real projects with organized test structures
- **Status**: Fixed by removing path restrictions in pytest invocation ✅

### 14. **Test Detection Limited by pytest.ini Configuration**

- **Issue**: `pytest.ini` contains `--maxfail=1` which stops pytest after first failure
- **Root Cause**: Line 9 in `pytest.ini`: `--maxfail=1`
- **Impact**: Nova only detects 1 failing test even when there are many
- **Example**: `demo_broken_project` has 13 tests with bugs but Nova only sees 1
- **Files Involved**:
  - `pytest.ini` - Contains the limiting configuration
  - `src/nova/runner/test_runner.py` - Runs pytest with this config
- **Status**: Fixed by adding `--maxfail=0` to override in test runner ✅

### 15. **Nova Creates Incomplete/Broken Fixes**

- **Issue**: Nova reports "All tests passing" while leaving code in broken state
- **Examples**:
  - `demo_file_io`: Deleted utility functions needed by other tests
  - `demo_oop`: Deleted entire Employee class causing import failures
- **Impact**: Most dangerous issue - users trust false "success" messages
- **Causes**:
  - Running only subset of tests
  - Stopping after initial tests pass without full verification
  - Related to subfolder discovery issue

## 🟠 Medium Priority Issues

### 16. **Hardcoded Limits**

- **Issue**: Magic numbers and limits hardcoded throughout
- **Examples**:
  - Content truncation: 2000-3000 character limits
  - Max tokens: 8000 tokens in llm_agent_enhanced.py
  - Test failure limit: Previously 5 (now removed ✅)
- **Impact**: Reduces effectiveness on larger projects
- **Recommendation**: Expose via environment variables or config

### 17. **Platform-Specific Code**

- **Issue**: Assumes POSIX environment in some parts
- **File**: `src/nova/tools/sandbox.py` (lines 79, 89, 99)
- **Risk**: May fail on Windows
- **Examples**: os.fork(), signals, shell behaviors

### 18. **GitHub Token Permissions**

- **Issue**: PR creation fails without proper token permissions
- **Context**: Requires `pull-requests: write` permission
- **Impact**: Configuration/documentation issue
- **Resolution**: Better error messages and documentation

### 19. **Shell Injection Risk**

- **File**: `examples/demos/demo_full_llm.py:21`
- **Issue**: `subprocess.run(..., shell=True)` with string concatenation
- **Impact**: Potential security vulnerability
- **Recommendation**: Use `shell=False` with list arguments

## 🟢 Minor Issues & TODOs

### 20. **Unimplemented Features**

- **Observation**: Placeholders like `nova eval` command
- **Impact**: Confusing for users discovering non-functional commands
- **Recommendation**: Remove from help text or implement

### 21. **Encoding Issues**

- **Issue**: Lossy text encoding handling with `errors='replace'`
- **Files**:
  - `src/nova/tools/sandbox.py:109-110`
  - `src/nova/tools/fs.py:185`
- **Impact**: Could mask real content in non-UTF-8 scenarios

### 22. **Test Coverage Gaps**

- **Observation**: No skipped or xfailed tests
- **Impact**: May indicate missing edge case coverage
- **Recommendation**: Add tests for known limitations

### 23. **Error Message Truncation**

- **Issue**: Error messages truncated to 50-200 characters
- **Impact**: Important debugging info may be lost
- **Resolution**: Increase limits or provide full logs

## ✅ Fixes Applied in PR fix/p0-bugs-cleanup

### P0 (Critical) Fixes - Completed

1. **Branch Preservation on Success** ✅
2. **Critic Auto-Approval Logic** - Defaults to rejection on JSON parse errors ✅
3. **Test Discovery** - Removed path restrictions for subfolder discovery ✅
4. **False Success Limit** - Removed 5-test cap ✅
5. **Patch Step Numbering** - Uses iteration number ✅
6. **Git Diff Base Case** - Handles zero patches gracefully ✅
7. **JUnit Path Interpolation** - Fixed f-string issue ✅

### P1 (High Priority) Fixes - Completed

1. **Uncommitted Changes Check** - Warns before creating fix branch ✅
2. **Patch Failure Recovery** - Retries on next iteration instead of aborting ✅
3. **Stagnation Detection** - Provides feedback when no progress is made ✅

### P2 (Medium Priority) Fixes - Partial

1. **Default Branch Detection** - Auto-detects main/master from origin ✅
2. **--auto-pr Flag** - Added for automatic PR creation ✅

### Still Broken Despite Fixes

- **Datetime Error** - Applied fixes but error persists in unknown location 🔴

## 🔧 Proposed Solution: Nova Configuration File

### Add `nova.yml` Configuration Support

To solve the source file discovery issue, implement support for a `nova.yml` configuration file that projects can use to specify their structure:

```yaml
# nova.yml - Project structure hints for Nova CI-Rescue
version: 1
paths:
  sources:
    - src/ # Primary source directory
    - lib/ # Alternative source directory
  tests:
    - tests/ # Test directory
    - test/ # Alternative test directory
  exclude:
    - node_modules/
    - .venv/
    - build/
```

**Implementation**:

1. Check for `nova.yml` in project root before starting
2. Use specified paths for source file discovery
3. Fall back to current logic if no config file exists
4. Would fix the "No source files identified" issue immediately

**Benefits**:

- Projects with non-standard structures can work with Nova
- Faster file discovery (no need to search everywhere)
- Better support for monorepos and complex projects
- Explicit is better than implicit

## 📋 Recommendations

### Immediate Actions (Before Launch)

1. **Fix source file discovery** - Implement nova.yml support or fix path logic ✅
2. **Fix path doubling bug** - Correct the file path construction ✅
3. **Fix bare exception handlers** - Add specific exception types
4. **Add file locking** for CI environments to prevent race conditions
5. **Clean up embedded git repositories** or convert to proper submodules
6. **Add proper JSON error handling** with fallbacks
7. **Ensure temp file cleanup** in all error paths
8. **Resolve datetime arithmetic bug** - Find and fix the remaining instance

### Short-term Improvements

1. **Make hardcoded limits configurable** via environment variables
2. **Add comprehensive error logging** before exceptions
3. **Implement dry-run mode** to preview changes without applying
4. **Better telemetry and debugging** output for issue diagnosis

### Long-term Enhancements

1. **Refactor patch handling** for reliability and clarity
2. **Multiple LLM provider support** with per-model configurations
3. **Better test suite coverage** including edge cases
4. **Platform compatibility** improvements

## 🚀 Launch Readiness Assessment

**Verdict**: 🚫 **NOT READY FOR LAUNCH**

### Critical Blockers:

1. **Datetime subtraction bug** - Must be found and resolved
2. **Bare exception handlers** - Need to be fixed to avoid masking issues
3. **False success reporting** - Nova must verify ALL tests pass, not just initial ones

### Major Issues to Address:

1. Resource leaks and cleanup
2. Embedded git directories
3. Clear documentation of limitations and requirements

### Recommendation:

Hold off on broad release until critical bugs are resolved. The concept is excellent and fixes are on the right track - a bit more polish and debugging will get Nova CI-Rescue to a safe launch state.
