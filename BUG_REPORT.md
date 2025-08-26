# Nova CI-Rescue Bug Report & Issues

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

### 2. **Path Doubling Bug**

- **Issue**: Test file paths are incorrectly constructed with duplicated segments
- **Example**: `/Users/.../demo_broken_project/examples/demos/demo_broken_project/tests/test_calculator.py`
- **Impact**: Files cannot be found due to malformed paths
- **Location**: Path construction in `llm_agent_enhanced.py`

### 3. **GPT-5 Temperature Hardcoding**

- **Location**: Multiple files (`llm_agent_enhanced.py`, `pr_generator.py`, `llm_client.py`)
- **Issue**: Temperature is hardcoded to 1.0 for GPT-5, but comment says "GPT-5 requires temperature=1"
- **Impact**: May not be using optimal temperature settings for different tasks
- **Files**:
  - `src/nova/agent/llm_agent_enhanced.py:123`
  - `src/nova/tools/pr_generator.py:87`
  - `src/nova/agent/llm_client.py:128`

### 4. **Bare Exception Handlers**

- **Issue**: Multiple places use bare `except:` which can hide critical errors
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

### 6. **Datetime - Float Arithmetic Error (CRITICAL - STILL BROKEN)**

- **Issue**: Despite multiple fix attempts, datetime arithmetic errors still occur
- **Error**: `unsupported operand type(s) for -: 'datetime.datetime' and 'float'`
- **Status**: CRITICAL - Fixes applied but error persists, blocking all nova runs
- **Fixed Files** (in PR fix/p0-bugs-cleanup):
  - `src/nova/cli.py:82-85, 542-545` - Added isinstance checks ✅
  - `src/nova/nodes/reflect.py:55-57` - Added isinstance checks ✅
- **Error Still Occurs**: After "⚠ No progress: 5 test(s) still failing"
- **Root Cause**: There's another location performing datetime arithmetic that we haven't found
- **Next Steps**: Need full stack trace to identify exact location

### 7. **JUnit Report Path Not Interpolated**

- **Issue**: Missing f-string prefix causes literal `{junit_report_path}` files
- **File**: `src/nova/runner/test_runner.py:68`
- **Impact**: Creates files named `{junit_report_path}` in demo directories
- **Fix**: Change `"--junit-xml={junit_report_path}"` to `f"--junit-xml={junit_report_path}"`

## 🟡 High Priority Issues

### 6. **Patch Truncation Handling**

- **Issue**: Patches can be truncated but detection is fragile
- **Files**: `src/nova/tools/patch_fixer.py`
- **Symptoms**:
  - Warning about truncation artifacts (line 141)
  - Attempts to reconstruct truncated patches
  - May fail silently on corrupted patches

### 7. **Resource Management**

- **Issue**: Temporary files not always cleaned up properly
- **Files**:
  - `src/nova/nodes/apply_patch.py:73` - temp file creation
  - `src/nova/tools/fs.py:414` - temp patch files in .nova directory
  - `src/nova/runner/test_runner.py:54` - temp JSON report files

### 8. **JSON Parsing Without Proper Error Handling**

- **Issue**: JSON parsing that could fail on malformed data
- **Files**:
  - `src/nova/runner/test_runner.py:119` - FileNotFoundError/JSONDecodeError
  - `src/nova/cli.py:560` - bare except on JSON parsing

### 9. **Race Conditions in CI Environment**

- **Issue**: No locking mechanism for parallel runs
- **Impact**: Multiple Nova instances could conflict
- **Mitigation needed**: File locks or run coordination

## 🟠 Medium Priority Issues

### 10. **Hardcoded Limits**

- **Issue**: Various hardcoded limits that should be configurable
- **Examples**:
  - Content truncation at 2000-3000 chars in multiple files
  - Max tokens hardcoded to 8000 in `llm_agent_enhanced.py`
  - Test failure limit of 5 in various places

### 11. **Platform-Specific Code**

- **Issue**: OS-specific code without full testing
- **Files**: `src/nova/tools/sandbox.py:79, 89, 99`
- **Risk**: May fail on non-POSIX systems

### 12. **GitHub Token Permissions**

- **Issue**: PR creation can fail without proper permissions
- **Documented in**: `docs/07-risks-and-guardrails.md:51`
- **Required**: `pull-requests: write` permission

### 13. **Shell Injection Risk**

- **File**: `demo_full_llm.py:21`
- **Issue**: `subprocess.run` with `shell=True`
- **Risk**: Command injection if user input is passed

## 🟡 High Priority Issues (continued)

### 18. **Nova Cannot Find Tests in Subfolders**

- **Issue**: When running `nova fix .` in a parent directory, Nova reports "No failing tests found" even when subdirectories contain failing tests
- **Impact**: Users must manually navigate to each subdirectory to fix tests
- **Example**: Running `nova fix .` in `examples/demos/` doesn't find failing tests in `demo_file_io/`, `demo_oop/`, etc.
- **Root Cause**: Test discovery logic may not be recursively searching subdirectories properly

### 19. **Nova Creates Incomplete/Broken Fixes**

- **Issue**: Nova reports "All tests passing" but actually leaves the codebase in a broken state
- **Examples Observed**:
  - `demo_file_io`: Nova fixed 5 tests but deleted functions needed by 6 other tests (copy_file, get_file_size, file_exists, create_directory, list_files, delete_file)
  - `demo_oop`: Nova deleted the Employee class entirely, causing import errors
- **Impact**: False positives where Nova claims success but the codebase is actually more broken than before
- **Root Cause**: Nova may only be running a subset of tests or not properly validating the full test suite after changes

## 🟢 Minor Issues & TODOs

### 14. **Unimplemented Features**

- **Eval command**: `src/nova/cli.py:661` - "Eval command not yet implemented"
- **TODO comments**: Various TODO/FIXME markers throughout codebase

### 15. **Encoding Issues**

- **Issue**: UTF-8 decode with 'replace' errors could hide data corruption
- **Files**:
  - `src/nova/tools/sandbox.py:109-110`
  - `src/nova/tools/fs.py:185`

### 16. **Test Coverage Gaps**

- **Issue**: No skipped or xfailed tests found (too good to be true?)
- **Risk**: May be missing edge case tests

### 17. **Error Message Truncation**

- **Issue**: Error messages truncated to 50-200 chars in various places
- **Impact**: May lose critical debugging information

## ✅ Fixes Applied in PR fix/p0-bugs-cleanup

### P0 (Critical) Fixes - Completed

1. **Branch Preservation** - Fixed cleanup(success=True) when PR created ✅
2. **Critic Auto-Approval** - Now defaults to rejection on JSON parse failure ✅
3. **Test Discovery** - Removed explicit path to allow subfolder discovery ✅
4. **False Success** - Removed max_failures limit to run all tests ✅
5. **Patch Step Numbering** - Uses iteration number instead of current_step ✅
6. **Git Diff Base** - Handles zero patches case properly ✅
7. **JUnit Path** - Fixed f-string interpolation ✅

### P1 (High Priority) Fixes - Completed

1. **Uncommitted Changes Check** - Warns user before creating fix branch ✅
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
    - src/          # Primary source directory
    - lib/          # Alternative source directory
  tests:
    - tests/        # Test directory
    - test/         # Alternative test directory
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

1. **Fix source file discovery** - Implement nova.yml support or fix path logic
2. **Fix path doubling bug** - Correct the file path construction
3. **Fix bare exception handlers** - Add specific exception types
4. **Add file locking** for CI environments to prevent race conditions
5. **Clean up embedded git repositories** or convert to proper submodules
6. **Add proper JSON error handling** with fallbacks
7. **Ensure temp file cleanup** in all error paths

### Short-term Improvements

1. **Make hardcoded limits configurable** via environment variables
2. **Add comprehensive error logging** before exceptions
3. **Implement retry logic** for transient failures
4. **Add telemetry for bug tracking**
5. **Create integration tests** for patch application edge cases

### Long-term Enhancements

1. **Refactor patch handling** to be more robust against LLM output variations
2. **Add support for multiple LLM providers** with proper abstraction
3. **Implement proper resource pooling** for LLM calls
4. **Add health checks** and monitoring endpoints
5. **Create comprehensive test suite** with failure injection

## 🔍 Bug Patterns Observed

1. **LLM Output Handling**: Many issues stem from handling unpredictable LLM output
2. **Resource Cleanup**: Consistent pattern of resource leaks in error paths
3. **Error Suppression**: Too many bare exceptions hiding real issues
4. **Hardcoded Values**: Configuration that should be dynamic
5. **Platform Assumptions**: Code assuming POSIX environment

## 🚀 Launch Readiness Assessment

**Critical fixes needed**:

- ✅ Loop prevention (already implemented)
- ❌ Bare exception handlers
- ❌ Resource cleanup in error paths
- ⚠️ Race condition prevention (documented risk)
- 🔴 **Nova creates broken fixes** - This is a CRITICAL issue that makes the tool dangerous to use
- 🔴 **Nova cannot find tests in subfolders** - Major usability issue

**Nice to have**:

- Configuration improvements
- Better error messages
- Platform compatibility

**Verdict**: **NOT READY FOR LAUNCH**. The codebase has critical issues that make it unsafe for production use:

1. **Nova creates broken "fixes"** that delete necessary code while claiming success. This could destroy user codebases.
2. **Subfolder test discovery is broken**, severely limiting usability for real projects.
3. **Multiple bare exception handlers** hide real errors.
4. **Resource leaks** in error paths could cause system issues.

These issues MUST be fixed before any public launch. The tool currently poses a risk of damaging user code while providing false confidence through incorrect success messages.
