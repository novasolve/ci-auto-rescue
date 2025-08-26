# Nova CI-Rescue Bug Report & Issues

## 🔴 Critical Issues

### 1. **GPT-5 Temperature Hardcoding**
- **Location**: Multiple files (`llm_agent_enhanced.py`, `pr_generator.py`, `llm_client.py`)
- **Issue**: Temperature is hardcoded to 1.0 for GPT-5, but comment says "GPT-5 requires temperature=1"
- **Impact**: May not be using optimal temperature settings for different tasks
- **Files**: 
  - `src/nova/agent/llm_agent_enhanced.py:123`
  - `src/nova/tools/pr_generator.py:87`
  - `src/nova/agent/llm_client.py:128`

### 2. **Bare Exception Handlers**
- **Issue**: Multiple places use bare `except:` which can hide critical errors
- **Files**:
  - `src/nova/cli.py:538, 561`
  - `src/nova/nodes/apply_patch.py:91`
  - `src/nova/tools/pr_generator.py:264, 300`
  - `src/nova/agent/llm_client.py:177`

### 3. **Submodule Git Repository Warnings**
- **Issue**: Embedded git repositories causing warnings during commits
- **Paths**:
  - `examples/demos/demo_llm_repo`
  - `examples/demos/demo_nova_test`
  - `examples/demos/demo_test_repo`
  - `examples/sample_repos/nova_demo_workspace`

## 🟡 High Priority Issues

### 4. **Patch Truncation Handling**
- **Issue**: Patches can be truncated but detection is fragile
- **Files**: `src/nova/tools/patch_fixer.py`
- **Symptoms**: 
  - Warning about truncation artifacts (line 141)
  - Attempts to reconstruct truncated patches
  - May fail silently on corrupted patches

### 5. **Resource Management**
- **Issue**: Temporary files not always cleaned up properly
- **Files**:
  - `src/nova/nodes/apply_patch.py:73` - temp file creation
  - `src/nova/tools/fs.py:414` - temp patch files in .nova directory
  - `src/nova/runner/test_runner.py:54` - temp JSON report files

### 6. **JSON Parsing Without Proper Error Handling**
- **Issue**: JSON parsing that could fail on malformed data
- **Files**:
  - `src/nova/runner/test_runner.py:119` - FileNotFoundError/JSONDecodeError
  - `src/nova/cli.py:560` - bare except on JSON parsing

### 7. **Race Conditions in CI Environment**
- **Issue**: No locking mechanism for parallel runs
- **Impact**: Multiple Nova instances could conflict
- **Mitigation needed**: File locks or run coordination

## 🟠 Medium Priority Issues

### 8. **Hardcoded Limits**
- **Issue**: Various hardcoded limits that should be configurable
- **Examples**:
  - Content truncation at 2000-3000 chars in multiple files
  - Max tokens hardcoded to 8000 in `llm_agent_enhanced.py`
  - Test failure limit of 5 in various places

### 9. **Platform-Specific Code**
- **Issue**: OS-specific code without full testing
- **Files**: `src/nova/tools/sandbox.py:79, 89, 99`
- **Risk**: May fail on non-POSIX systems

### 10. **GitHub Token Permissions**
- **Issue**: PR creation can fail without proper permissions
- **Documented in**: `docs/07-risks-and-guardrails.md:51`
- **Required**: `pull-requests: write` permission

### 11. **Shell Injection Risk**
- **File**: `demo_full_llm.py:21`
- **Issue**: `subprocess.run` with `shell=True`
- **Risk**: Command injection if user input is passed

## 🟢 Minor Issues & TODOs

### 12. **Unimplemented Features**
- **Eval command**: `src/nova/cli.py:661` - "Eval command not yet implemented"
- **TODO comments**: Various TODO/FIXME markers throughout codebase

### 13. **Encoding Issues**
- **Issue**: UTF-8 decode with 'replace' errors could hide data corruption
- **Files**: 
  - `src/nova/tools/sandbox.py:109-110`
  - `src/nova/tools/fs.py:185`

### 14. **Test Coverage Gaps**
- **Issue**: No skipped or xfailed tests found (too good to be true?)
- **Risk**: May be missing edge case tests

### 15. **Error Message Truncation**
- **Issue**: Error messages truncated to 50-200 chars in various places
- **Impact**: May lose critical debugging information

## 📋 Recommendations

### Immediate Actions (Before Launch)
1. **Fix bare exception handlers** - Add specific exception types
2. **Add file locking** for CI environments to prevent race conditions
3. **Clean up embedded git repositories** or convert to proper submodules
4. **Add proper JSON error handling** with fallbacks
5. **Ensure temp file cleanup** in all error paths

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

**Nice to have**:
- Configuration improvements
- Better error messages
- Platform compatibility

**Verdict**: The codebase is functional but has several robustness issues that could cause problems under load or edge cases. The critical bare exception handlers should be fixed before launch to ensure errors are properly reported rather than silently suppressed.