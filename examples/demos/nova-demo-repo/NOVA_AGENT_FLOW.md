# Nova Agent Logic Flow

This document details the Nova CI-Rescue agent's autonomous workflow for detecting, analyzing, and fixing test failures.

## Agent Architecture: Plan → Generate → Review → Apply → Test → Reflect

Nova follows a structured loop to converge on solutions:

### 1. **Detection Phase**
```
[Nova] ❌ Detected failing test: tests/test_calculator.py::test_subtract
       → AssertionError: expected 4, got 10
```
- Runs `pytest` to identify failures
- Parses test output for specific error details
- Extracts expected vs actual values

### 2. **Analysis Phase (Plan)**
```
[Nova] 🔍 Analyzing failure...
       The function subtract(x, y) returns x + y, which is incorrect.
       Likely cause: The subtraction logic is implemented incorrectly (addition instead of subtraction).
       Proposed solution: Change the implementation to use subtraction (x - y) to match expected behavior.
```
- Uses LLM to understand the code context
- Identifies root cause of failure
- Formulates a plan to fix the issue

### 3. **Generation Phase**
```
*** Begin Patch (Nova AI-generated) ***
*** Update File: calculator.py ***
 def subtract(x, y):
-    return x + y  # BUG: using addition instead of subtraction
+    return x - y  # FIX: use subtraction to get the correct result
*** End Patch ***
```
- Generates minimal, targeted patches
- Preserves code style and comments
- Focuses on fixing the specific issue

### 4. **Review Phase (Critic)**
- AI critic reviews the proposed patch
- Ensures changes are relevant and safe
- Checks for potential side effects
- Approves or requests revision

### 5. **Apply Phase**
```
[Nova] Applying patch to calculator.py...
[Nova] Creating commit: "nova: step 1 - fix subtract logic"
```
- Applies the patch to a new branch
- Never modifies main or original PR branch
- Creates atomic commits for each fix

### 6. **Test Phase**
```
[Nova] ▶ Re-running tests after applying fix...
==================== 5 passed in 0.04s ====================
[Nova] ✅ All tests passed after fix!
```
- Runs full test suite again
- Verifies the fix resolves the issue
- Ensures no new failures introduced

### 7. **Reflect Phase**
- If tests still fail, analyzes why
- Learns from the failure
- Iterates with improved approach
- Maximum 6 iterations by default

## Branch Management

Nova follows strict branch isolation:

```
main
  └── bugfix/wrong-subtraction (PR #1 - failing)
  └── nova-fix-20250820-083945 (Nova's fix branch)
        └── Creates PR #2 with passing tests
```

## Commit Messages

Nova uses structured commit messages:
- `nova: step 1 - fix subtract logic`
- `nova: step 2 - handle edge case`
- Each commit represents one iteration

## Integration Points

### GitHub Actions
```yaml
- name: Run Nova Auto-Fix
  if: steps.test-run.outputs.tests_passed == 'false'
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    nova fix . --max-iters 3 --timeout 300
```

### Pull Request Creation
Nova can automatically:
1. Push fix branch to GitHub
2. Open PR with AI-generated description
3. Link to original failing PR
4. Include test results summary

## Best Practices

1. **Isolation**: Nova never touches main directly
2. **Transparency**: All changes are reviewable via PR
3. **Safety**: Human review before merge
4. **Traceability**: Clear commit history
5. **Idempotency**: Can be run multiple times safely

## Example Full Flow

```bash
# 1. CI detects failure in PR #1
❌ tests/test_calculator.py::test_subtract FAILED

# 2. Nova triggered automatically
$ nova fix .

# 3. Nova creates fix branch
[Nova] Creating branch: nova-fix-20250820-083945

# 4. Nova analyzes and fixes
[Nova] 🔍 Analyzing failure...
[Nova] 🔧 Applying fix...
[Nova] ✅ All tests passed!

# 5. Nova opens PR #2
[Nova] 🎯 Created PR #2: "Nova Fix: Correct subtraction logic"

# 6. CI runs on PR #2
✅ All checks passed

# 7. Human reviews and merges
[Human] LGTM! Merging Nova's fix.
```

This autonomous flow turns red builds green with minimal human intervention!
