# Nova CI-Rescue Bug Report - New Issues (Aug 25, 2025)

## 🚨 Critical Issues Found During Demo Testing

### P0 - Critical Issues

#### 1. Patches Not Being Displayed (First-Class Citizen Issue)
**Severity**: CRITICAL
**Impact**: Users cannot see what changes Nova is attempting to make
**Details**:
- Generated patches are not shown in verbose mode
- Only see "Generated patch: X lines" but not the actual patch content
- This should be a first-class feature - users need to see what Nova is trying to do
**Expected**: Full patch content should be displayed, especially in verbose mode

#### 2. Missing Test Detection - Only Shows 1 Test When Multiple Fail
**Severity**: CRITICAL  
**Impact**: Nova is not detecting all failing tests
**Observed**:
- demo_broken_project has 5 failing tests (test_add, test_subtract, test_multiply, test_divide_by_zero, test_power)
- Nova only reports "Found 1 failing test(s)" 
- Only TestCalculator.test_add is shown in the table
**Expected**: All 5 failing tests should be detected and displayed

#### 3. Critic Feedback Not Shown - "Patch review indeterminate"
**Severity**: CRITICAL
**Impact**: Users cannot understand why patches are being rejected
**Details**:
- Every patch shows: "Patch review indeterminate (parsing failed, auto-rejected)"
- No actual critic feedback is displayed
- Users need to see what the critic is saying about the patch
**Expected**: Full critic reasoning should be shown

#### 4. Save Patches Feature Broken
**Severity**: HIGH
**Impact**: No patches are being saved despite the message
**Observed**:
```
📄 Saved patches (attempted fixes):
[Empty - no patches listed]
```
**Expected**: Patches should be saved to .nova directory and listed

### P1 - High Priority Issues

#### 5. False Uncommitted Changes Warning
**Severity**: HIGH
**Impact**: Confusing UX - asks about uncommitted changes after git commit
**Details**:
- User runs: `git add -A; git commit -am ">"; git push`
- Nova still warns: "⚠️ Warning: You have uncommitted changes in your working tree."
- This happens because of submodules with untracked content
**Expected**: Should ignore submodule changes or be more specific about what's uncommitted

#### 6. Verbose Mode Not Working
**Severity**: HIGH
**Impact**: Even with --verbose flag, critical information is missing
**Missing in verbose mode**:
- Actual patch content
- Full critic feedback
- Detailed plan steps (only shows "Approach:" with empty value)
- LLM reasoning

### P2 - Medium Priority Issues

#### 7. Plan Details Not Displayed
**Severity**: MEDIUM
**Observed**:
```
Plan created:
  Approach: 
```
**Expected**: Should show the actual approach and steps

#### 8. No Error Details for Test Failures
**Severity**: MEDIUM
**Impact**: Table shows location but not the actual error
**Observed**: Error column just shows "tests/test_calculator.py:22: in test_add"
**Expected**: Should show the actual assertion error or exception

## Summary of Issues

1. **Visibility Problems**: Users can't see what Nova is doing (patches, plans, critic feedback)
2. **Test Detection**: Missing 4 out of 5 failing tests
3. **Saving/Persistence**: Patches aren't being saved
4. **Git Integration**: False warnings about uncommitted changes
5. **Verbose Mode**: Not actually verbose - missing critical information

## Recommended Fixes

### Immediate (P0):
1. Display full patch content in verbose mode
2. Fix test detection to find all failing tests
3. Show actual critic feedback instead of "indeterminate"
4. Fix patch saving functionality

### Short-term (P1):
1. Improve git status checking to handle submodules
2. Make verbose mode actually verbose
3. Show plan details and LLM reasoning

### Medium-term (P2):
1. Show full error details in the failing tests table
2. Add option to control verbosity levels (e.g., -v, -vv, -vvv)
