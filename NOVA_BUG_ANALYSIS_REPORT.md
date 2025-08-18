# Nova Deep Agent Bug Analysis Report

## Executive Summary

During our investigation of Nova runs, we identified multiple bugs that prevent the Deep Agent from successfully fixing tests. Some issues from the Linear board are still active, while new bugs have been discovered.

## Status of Known Issues from Linear

### ✅ RESOLVED Issues:

1. **OS-1200: Docker Not Working** ✅

   - **Status**: RESOLVED
   - **Fix**: We added `use_docker` configuration support in RunTestsTool
   - **Note**: Docker can now be disabled via settings

2. **OS-1208: LLM review failed - unexpected keyword argument** ✅
   - **Status**: RESOLVED
   - **Fix**: Fixed the logger.log_event() signature issue (was passing single dict instead of event_type, data)

### ❌ STILL ACTIVE Issues:

3. **OS-1213: Agent Repetition/Looping Bug** ❌

   - **Status**: STILL ACTIVE (partially mitigated)
   - **Current State**: Loop prevention stops duplicate operations but agent gets confused by skip messages
   - **Example**: Agent repeatedly tries `open_file` on already-opened files

4. **OS-1224: Repeated file opening** ❌

   - **Status**: STILL ACTIVE (same as OS-1213)
   - **Current State**: Agent opened exceptions.py 10+ times despite loop prevention
   - **Root Cause**: Agent doesn't understand "ERROR: File already opened" means to proceed

5. **OS-1212: Patch preflight failed - No valid patches** ❌

   - **Status**: STILL ACTIVE
   - **Current State**: Patches sometimes rejected as "incomplete" or "no valid patches"
   - **Mitigation**: Added fallback mechanism, but critic still rejects valid patches

6. **OS-1223: Context mismatch** ❌
   - **Status**: PARTIALLY RESOLVED
   - **Fix**: Added patch fallback mechanism that writes files directly
   - **Issue**: Fallback works but agent may not always trigger it properly

## New Bugs Discovered

### 🆕 Bug #1: Loop Prevention Confuses Agent

**Description**: While loop prevention successfully stops duplicate operations, the agent interprets skip messages as errors and gets stuck.

**Example**:

```
Action: open_file
Input: exceptions.py
Observation: ERROR: File already opened (duplicate invocation skipped)
Thought: [Agent thinks it failed and tries again]
```

**Root Cause**: The "ERROR:" prefix makes agent think operation failed when it was actually prevented for efficiency.

### 🆕 Bug #2: Critic Patch Parsing Issues

**Description**: Critic rejects properly formatted patches claiming they are "incomplete" or have "no changes"

**Example**:

```
*** Begin Patch
*** Update File: examples/demos/demo_exceptions/exceptions.py
@@
 def divide_numbers(a, b):
-    return a / b
+    if b == 0:
+        raise ZeroDivisionError("Cannot divide by zero")
+    return a / b
*** End Patch
```

Result: "The patch provided is incomplete and does not provide any changes to review"

**Root Cause**: Critic may have issues parsing certain patch formats or context markers.

### 🆕 Bug #3: Agent Doesn't Adapt Strategy

**Description**: When one approach fails (e.g., apply_patch), agent doesn't switch to alternative approaches (e.g., write_file)

**Example**: After patch rejection, agent keeps trying patches instead of using write_file directly.

### 🆕 Bug #4: Insufficient Test Result Parsing

**Description**: Agent doesn't always extract detailed error information from test results to guide fixes.

**Example**: Gets "5 tests failed" but doesn't analyze specific assertion errors to craft targeted fixes.

## Bug Priority Matrix

| Bug                       | Impact | Frequency | Priority | Status  |
| ------------------------- | ------ | --------- | -------- | ------- |
| Agent Repetition/Looping  | HIGH   | VERY HIGH | P0       | Active  |
| Loop Prevention Confusion | HIGH   | HIGH      | P0       | New     |
| Critic Patch Parsing      | MEDIUM | HIGH      | P1       | Active  |
| Context Mismatch          | MEDIUM | MEDIUM    | P1       | Partial |
| Agent Strategy Adaptation | MEDIUM | MEDIUM    | P2       | New     |
| Test Result Parsing       | LOW    | MEDIUM    | P2       | New     |
| Patch Format Issues       | LOW    | MEDIUM    | P3       | Active  |

## Root Cause Analysis

### 1. **Communication Gap**

The agent doesn't understand tool responses properly:

- Interprets "skipped" as "failed"
- Doesn't recognize when to change strategy
- Confusion between preventive measures and actual errors

### 2. **Prompt/Tool Mismatch**

The agent's prompts don't align with actual tool behavior:

- Tools return "ERROR:" for non-error skip conditions
- Agent expects different response formats
- No guidance on handling loop prevention

### 3. **Critic Over-Rejection**

The critic is too strict or has parsing bugs:

- Rejects valid, minimal patches
- Claims patches are incomplete when they're not
- May have issues with patch format variations

### 4. **State Management**

Agent doesn't properly track what it has already tried:

- Doesn't remember file contents already seen
- Repeats same failed approaches
- Doesn't leverage state to avoid loops

## Recommendations

### Immediate Fixes:

1. **Change skip messages** from "ERROR:" to "INFO:" or "SKIP:"
2. **Update agent prompts** to handle skip messages explicitly
3. **Fix critic patch parsing** to accept standard unified diff format
4. **Add response caching** so agent can retrieve previously seen content

### Long-term Improvements:

1. **Implement smarter agent strategy** that adapts based on failures
2. **Add explicit state tracking** in agent memory for seen content
3. **Improve test result parsing** to extract actionable error details
4. **Create feedback loop** where agent learns from skip messages

## Conclusion

While we've made progress on infrastructure issues (Docker, logging), the core agent behavior issues remain. The agent gets stuck in loops not because loop prevention fails, but because it doesn't understand the prevention messages. This creates a paradox where our safety mechanisms actually hinder progress.

The highest priority should be fixing the communication gap between tools and agent understanding, followed by improving the critic's patch parsing capabilities.
