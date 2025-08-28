# 🚨 Nova CI-Rescue Master Bug Ticket

## Executive Summary

Nova CI-Rescue has multiple critical issues preventing it from functioning correctly. The root cause appears to be that Nova cannot properly access source files, leading to a cascade of failures including empty plans, meaningless patches, and false success reports.

---

## 🔴 CRITICAL PATH ISSUES (Must Fix in Order)

### 1. Empty Plan Generation

**Status**: 🔴 CRITICAL  
**Symptom**: Plans are completely empty

```
Plan created:
  Approach:
  Steps:
```

**Root Cause**: Nova cannot see the source files to analyze  
**Impact**: Without a plan, Nova is working blind

---

### 2. Source File Discovery Failure

**Status**: 🔴 CRITICAL  
**Evidence**:

- `calculator.py` has 14+ clearly marked bugs with `# BUG:` comments
- Nova's patches don't reference any actual code from the file
- Test file: `demo_broken_project/tests/test_calculator.py`
- Source file: `demo_broken_project/src/calculator.py`
- Nova is looking in: `demo_broken_project/calculator.py` ❌

**The Problem**:

```python
# Nova's current search paths:
self.repo_path / "calculator.py"          # ❌ Wrong location
self.repo_path / "calculator/__init__.py" # ❌ Wrong location

# Where the file actually is:
self.repo_path / "src/calculator.py"      # ✅ Correct location
```

**Impact**: Nova literally cannot see the bugs it's supposed to fix

---

### 3. Test Detection Failure

**Status**: 🔴 CRITICAL  
**Symptom**: Only detects 1 of 5 failing tests

```
Found 1 failing test(s):
  TestCalculator::test_add
```

**Reality**: 5 tests are actually failing:

- `test_add`
- `test_subtract`
- `test_multiply`
- `test_divide_by_zero`
- `test_power`

**Impact**: Nova only attempts to fix 20% of the problems

---

### 4. Patches Not Displayed (Transparency Issue)

**Status**: 🔴 CRITICAL  
**Symptom**: Even with `--verbose`, patches are hidden

```
Generated patch: 27 lines
```

**Missing**: The actual 27 lines of the patch!  
**Impact**: Users have no idea what Nova is trying to change

---

### 5. Critic Feedback Hidden

**Status**: 🔴 CRITICAL  
**Symptom**: Every patch shows the same generic message

```
Patch review indeterminate (parsing failed, auto-rejected)
```

**Missing**:

- What the critic actually said
- Why the patch was rejected
- What needs to be fixed

**Impact**: No actionable feedback for debugging

---

## 🟡 SECONDARY ISSUES (Fix After Critical Path)

### 6. False Success Reports

**Status**: 🟡 HIGH  
**Symptom**: Nova claims "All tests passing" but code is more broken than before
**Example**: In `demo_file_io`, Nova:

- Fixed 5 tests ✅
- Deleted 6 functions that other tests needed ❌
- Reported success anyway 🤦

---

### 7. datetime.datetime vs float Error

**Status**: 🟡 HIGH (Partially Fixed)
**Error**: `unsupported operand type(s) for -: 'datetime.datetime' and 'float'`
**Fixed in**: `cli.py`, `reflect.py`
**Still Occurs**: Unknown location, needs stack trace

---

### 8. Saved Patches Not Working

**Status**: 🟡 HIGH
**Symptom**:

```
📄 Saved patches (attempted fixes):
[Empty - no patches listed]
```

**Expected**: Patches saved to `.nova/patches/*.patch`

---

### 9. False Uncommitted Changes Warning

**Status**: 🟡 HIGH
**Symptom**: Warning appears even after `git commit -am "..."`
**Cause**: Submodules with untracked content

---

### 10. Whole File Mode Issues

**Status**: 🟡 HIGH
**Note**: `--whole-file` flag was added to work around patch issues
**Problem**: Still not working correctly due to file access issues

---

## 🟢 MINOR ISSUES

### 11. JUnit Report Path

**Status**: 🟢 MINOR (Fixed in PR)
**Issue**: Missing f-string creates files named `{junit_report_path}`

### 12. Verbose Mode Not Verbose

**Status**: 🟢 MINOR
**Missing**: LLM prompts, responses, internal reasoning

### 13. Resource Cleanup

**Status**: 🟢 MINOR
**Issue**: Temp files not always cleaned up
**Locations**: Various `.nova/` directories

---

## 📋 FIX IMPLEMENTATION PLAN

### Phase 1: Enable File Access (URGENT)

1. **Fix `find_source_files_from_test()`** to search common directories:

   ```python
   possible_files = [
       self.repo_path / f"{module}.py",
       self.repo_path / "src" / f"{module}.py",        # Add this
       self.repo_path / "lib" / f"{module}.py",        # Add this
       self.repo_path / module / "__init__.py",
       self.repo_path / "src" / module / "__init__.py", # Add this
   ]
   ```

2. **Add file discovery logging** (temporary):
   ```python
   print(f"[Debug] Looking for: {module}")
   print(f"[Debug] Found at: {found_path}")
   ```

### Phase 2: Enable Transparency

1. **Show patches in verbose mode**:

   ```python
   if verbose:
       console.print("[bold cyan]Generated Patch:[/bold cyan]")
       for line in patch.splitlines()[:50]:  # First 50 lines
           console.print(line)
   ```

2. **Show critic responses**:
   ```python
   if verbose:
       console.print(f"[dim]Critic said: {response}[/dim]")
   ```

### Phase 3: Fix Test Discovery

1. **Run pytest with proper discovery**:

   ```python
   # Current: may be limiting scope
   pytest_args = ["--tb=short", "--no-header", "-q", test_path]

   # Better: discover all tests
   pytest_args = ["--tb=short", "--no-header", "-q", "-v", test_path]
   ```

2. **Remove artificial limits**:
   ```python
   # Remove: max_failures=5
   # This causes early termination
   ```

### Phase 4: Validate Success Claims

1. **Run ALL tests before claiming success**
2. **Check for import errors after changes**
3. **Verify no functions were deleted**

---

## 🎯 SUCCESS CRITERIA

1. **Nova can see source files**: Debug logs show "Found source files: src/calculator.py"
2. **Plans have content**: "Approach: Fix arithmetic bugs in Calculator class"
3. **All tests detected**: "Found 5 failing test(s)"
4. **Patches visible**: Full diff shown in verbose mode
5. **Critic feedback shown**: Actual reasoning displayed
6. **No false positives**: Only claim success when ALL tests pass

---

## ⚡ QUICK TEST

Run this to verify fixes:

```bash
cd examples/demos/demo_broken_project
nova fix . --verbose --whole-file
```

**Should see**:

- ✅ "Found source files: src/calculator.py"
- ✅ "Found 5 failing test(s)"
- ✅ Actual plan content
- ✅ Full patch/replacement content
- ✅ Critic's actual feedback

**Should NOT see**:

- ❌ "No source files found"
- ❌ "Found 1 failing test(s)"
- ❌ Empty plan
- ❌ "parsing failed, auto-rejected"
- ❌ "All tests passing" (when they're not)

---

## 📊 IMPACT ASSESSMENT

**Current State**: Nova is effectively non-functional

- Cannot find source files → Cannot analyze code
- Cannot analyze code → Cannot create plans
- Cannot create plans → Cannot generate fixes
- Cannot see failures → Claims false success

**After Fixes**: Nova should be able to:

1. Find and read source files
2. Create meaningful plans
3. Generate appropriate patches
4. Show its work transparently
5. Accurately report success/failure

---

## 🚀 RECOMMENDATION

**DO NOT SHIP** until Phase 1 & 2 are complete. Nova currently:

- Works blind (can't see source files)
- Hides its actions (no patch visibility)
- Lies about success (claims fixes when breaking code)

This is worse than not working - it actively damages codebases while providing false confidence.
