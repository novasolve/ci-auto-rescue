# Tool Implementation Comparison: Current vs Proposed

## Overview

This document compares our current unified tools implementation with the newly proposed implementation.

## High-Level Comparison

| Aspect             | Current Implementation            | Proposed Implementation            |
| ------------------ | --------------------------------- | ---------------------------------- |
| **Location**       | `src/nova/agent/unified_tools.py` | Proposed for `nova/agent/tools.py` |
| **Size**           | 671 lines                         | ~120 lines                         |
| **Tools Count**    | 6 tools                           | 3 tools                            |
| **Approach**       | Mixed (function + class-based)    | All function-based with `@tool`    |
| **Dependencies**   | Multiple Nova modules             | Minimal Nova imports               |
| **Safety Checks**  | Comprehensive built-in            | Delegates to `patch_guard`         |
| **Docker Support** | Built-in with fallback            | Via `TestRunner` abstraction       |

## Tool-by-Tool Comparison

### 1. Test Running Tool

#### Current: `RunTestsTool` (Class-based)

```python
class RunTestsTool(BaseTool):
    # 100+ lines
    # - Docker execution built-in
    # - Local TestRunner fallback
    # - JSON result parsing
    # - Formatted failure output
```

**Features:**

- ✅ Docker sandbox execution with resource limits
- ✅ Automatic fallback to local TestRunner
- ✅ Detailed failure formatting
- ✅ Configurable max_failures parameter
- ✅ Handles both JSON and non-JSON output

#### Proposed: `run_tests_tool` (Function-based)

```python
@tool("run_tests", return_direct=True)
def run_tests_tool(test_pattern: str = "") -> str:
    # ~25 lines
    # - Delegates to TestRunner
    # - Simple failure formatting
```

**Features:**

- ✅ Clean abstraction via TestRunner
- ✅ Pattern-based test filtering
- ✅ Concise failure summary
- ❌ No direct Docker configuration
- ❌ No JSON output parsing

### 2. Patch Application Tool

#### Current: `ApplyPatchTool` (Class-based)

```python
class ApplyPatchTool(BaseTool):
    # 80+ lines
    # - Built-in safety checks
    # - Git operations inline
    # - Markdown unwrapping
```

**Features:**

- ✅ Comprehensive safety checks via `check_patch_safety()`
- ✅ Git preflight checks (`git apply --check`)
- ✅ Automatic markdown formatting removal
- ✅ Detailed error messages
- ✅ Git commit with message

#### Proposed: `apply_patch_tool` (Function-based)

```python
@tool("apply_patch", return_direct=True)
def apply_patch_tool(diff: str) -> str:
    # ~20 lines
    # - Delegates to patch_guard and fs
```

**Features:**

- ✅ Clean abstraction via `fs.apply_and_commit_patch()`
- ✅ Safety via `patch_guard.preflight_patch_checks()`
- ✅ Returns changed files list
- ❌ No markdown unwrapping
- ❓ Depends on external modules availability

### 3. Patch Review/Critic Tool

#### Current: `CriticReviewTool` (Class-based)

```python
class CriticReviewTool(BaseTool):
    # 100+ lines
    # - LLM-based review
    # - Pattern-based safety checks
    # - Forbidden path detection
```

**Features:**

- ✅ LLM integration for semantic review
- ✅ Comprehensive forbidden patterns list
- ✅ Size-based rejection
- ✅ Suspicious code pattern detection
- ✅ JSON response parsing from LLM

#### Proposed: `critic_review_tool` (Function-based)

```python
@tool("critic_review", return_direct=True)
def critic_review_tool(patch_diff: str) -> str:
    # ~25 lines
    # - Basic size checks
    # - Delegates to patch_guard
```

**Features:**

- ✅ Simple size-based validation
- ✅ Delegates safety to patch_guard
- ❌ No LLM review (commented as optional)
- ❌ No forbidden pattern checks
- ❌ No suspicious code detection

### 4. Additional Tools (Current Only)

Our current implementation includes additional tools not in the proposed version:

#### `plan_todo` (Function-based)

- Simple planning tool for agent strategy
- No-op that records plans

#### `open_file` (Function-based)

- Safe file reading with blocked patterns
- Size truncation for large files

#### `write_file` (Function-based)

- Safe file writing with blocked patterns
- Directory creation support

## Key Differences

### 1. **Architecture Philosophy**

**Current**: Self-contained, comprehensive

- All logic implemented within the tools
- Minimal external dependencies
- Can work standalone

**Proposed**: Delegation-based, modular

- Relies on external modules (`TestRunner`, `fs`, `patch_guard`)
- Cleaner separation of concerns
- Assumes infrastructure exists

### 2. **Safety Implementation**

**Current**: Built-in safety

- Direct implementation of safety checks
- Comprehensive blocked patterns
- Multiple validation layers

**Proposed**: Delegated safety

- Relies on `patch_guard` module
- Assumes safety implemented elsewhere
- Simpler but dependent

### 3. **Error Handling**

**Current**: Detailed error messages

- Specific error types (safety, context, etc.)
- User-friendly messages
- Multiple fallback paths

**Proposed**: Basic error handling

- Simple success/failure messages
- Less detailed error information
- Relies on underlying modules

### 4. **Tool Count & Scope**

**Current**: 6 tools

- Covers file I/O operations
- Includes planning tool
- More comprehensive toolkit

**Proposed**: 3 tools

- Core operations only
- Focused on test/patch cycle
- Minimal feature set

## Pros and Cons

### Current Implementation

**Pros:**

- ✅ Complete, self-contained solution
- ✅ Comprehensive safety checks
- ✅ Detailed error handling
- ✅ Docker integration with fallback
- ✅ File I/O tools included
- ✅ Battle-tested in production

**Cons:**

- ❌ Larger codebase (671 lines)
- ❌ Some code duplication
- ❌ More complex to maintain

### Proposed Implementation

**Pros:**

- ✅ Very concise (~120 lines)
- ✅ Clean separation of concerns
- ✅ Easy to understand
- ✅ Leverages existing Nova utilities
- ✅ Consistent function-based approach

**Cons:**

- ❌ Missing file I/O tools
- ❌ No LLM integration in critic
- ❌ Depends on external modules
- ❌ Less comprehensive safety
- ❌ No Docker configuration

## Recommendation

Both implementations have merit, but serve different purposes:

1. **Current Implementation** is production-ready and comprehensive, suitable for immediate use with all features needed for the Deep Agent.

2. **Proposed Implementation** is cleaner and more modular, but would need additional work:
   - Add file I/O tools
   - Implement LLM review in critic
   - Ensure all required modules exist
   - Add more comprehensive error handling

### Suggested Hybrid Approach

We could evolve the current implementation toward the proposed style:

1. **Keep**: Current comprehensive safety and Docker support
2. **Adopt**: Cleaner delegation pattern where appropriate
3. **Refactor**: Move some inline logic to utility modules
4. **Maintain**: File I/O tools and planning tool
5. **Optimize**: Reduce code duplication while keeping functionality

This would give us the best of both worlds: comprehensive functionality with cleaner architecture.

## Migration Path

If we wanted to adopt the proposed implementation:

1. **Phase 1**: Ensure required modules exist

   - Verify `TestRunner` has all needed features
   - Implement `fs.apply_and_commit_patch()` if missing
   - Create/verify `patch_guard` module

2. **Phase 2**: Add missing tools

   - Port `open_file` and `write_file` tools
   - Keep `plan_todo` for agent planning

3. **Phase 3**: Enhance safety and features

   - Add LLM integration to critic
   - Improve error messages
   - Add Docker configuration options

4. **Phase 4**: Testing and validation
   - Ensure all tests pass
   - Verify Deep Agent compatibility
   - Performance testing

## Conclusion

The current implementation is more complete and production-ready, while the proposed implementation offers a cleaner, more modular approach. The best path forward would be to gradually refactor the current implementation to adopt the cleaner patterns from the proposed version while maintaining the comprehensive feature set.
