# Test Structure Guidelines for Nova CI-Rescue

## 🎯 The Golden Rule

**Bugs belong in IMPLEMENTATION files, NOT in test files!**

Tests should always have correct expectations. Nova's job is to fix the buggy implementation to make the tests pass.

## ✅ Correct Structure

### Implementation File (HAS BUGS)
```python
# src/math_ops.py
def sum_numbers(numbers):
    # Bug: Returns product instead of sum
    result = 1
    for n in numbers:
        result *= n  # ❌ Wrong operation
    return result
```

### Test File (CORRECT EXPECTATIONS)
```python
# tests/test_math_ops.py
def test_sum():
    numbers = [1, 2, 3, 4, 5]
    assert sum_numbers(numbers) == 15  # ✅ Correct expectation
```

## ❌ Wrong Structure (Don't do this!)

### Implementation File (Correct)
```python
# src/math_ops.py
def sum_numbers(numbers):
    return sum(numbers)  # Correct implementation
```

### Test File (Wrong expectations)
```python
# tests/test_math_ops.py
def test_sum():
    numbers = [1, 2, 3, 4, 5]
    assert sum_numbers(numbers) == 10  # ❌ Wrong expectation!
```

## 📊 Test Scenario Summary

| Scenario | Bug Location | Test Expectations | Nova Can Fix? |
|----------|--------------|-------------------|---------------|
| **simple_math** | Implementation ✅ | Correct ✅ | Yes ✅ |
| **string_ops** | Implementation ✅ | Correct ✅ | Yes ✅ |
| **list_ops** | Implementation ✅ | Correct ✅ | Yes ✅ |
| **off_by_one** | Implementation ✅ | Correct ✅ | Yes ✅ |
| **edge_cases** | Implementation ✅ | Correct ✅ | Yes ✅ |
| **import_issues** | Implementation ✅ | Correct ✅ | Yes ✅ |
| **type_hints** | Implementation ✅ | Correct ✅ | Yes ✅ |
| **exception_handling** | Implementation ✅ | Correct ✅ | Yes ✅ |
| **unfixable_bug** | Test (intentional) ⚠️ | Wrong (intentional) ⚠️ | No ❌ |
| **no_op_patch** | Neither ⚠️ | Always fails ⚠️ | No ❌ |

## 🔍 Why This Matters

1. **Nova fixes code, not tests** - Nova assumes tests are the source of truth
2. **Real-world accuracy** - In practice, tests define requirements; code implements them
3. **Clear success criteria** - When tests pass, the implementation is correct

## ⚠️ Special Edge Cases

Only two scenarios intentionally violate this rule to test Nova's limits:

### 1. unfixable_bug
- **Purpose:** Test Nova's behavior when test expectations are wrong
- **Implementation:** Code is correct (returns 42)
- **Test:** Expects wrong value (43)
- **Expected Result:** Nova should fail to fix this

### 2. no_op_patch
- **Purpose:** Test Nova with always-failing tests
- **Implementation:** Any code
- **Test:** `assert False` (always fails)
- **Expected Result:** Nova should recognize it can't fix this

## 🔧 Verification Script

Run this to verify all test scenarios follow the correct pattern:

```bash
python verify_test_scenarios.py
```

Expected output:
```
✅ All scenarios follow the correct pattern!
   Bugs are in implementation files, tests have correct expectations.
   (Except for intentional edge cases: unfixable_bug and no_op_patch)
```

## 📝 Checklist for New Test Scenarios

When creating new test scenarios:

- [ ] Bug is in the implementation file (.py)
- [ ] Test has correct expectations
- [ ] Bug is clearly commented with `# Bug: explanation`
- [ ] Test will pass when bug is fixed
- [ ] Test will fail with current buggy implementation

## 💡 Examples of Good Bug Comments

```python
# Bug: adds extra 1
# Bug: integer division instead of float
# Bug: missing uppercase handling
# Bug: doesn't handle negative indices
# Bug: catches wrong exception type
```

## 🚀 Quick Test

To verify a specific scenario works correctly:

```bash
# Generate and test a scenario
./nova_unified_test_suite.py --generate --timeout 300

# The test should:
# 1. Fail initially (bug in implementation)
# 2. Nova fixes the implementation
# 3. Test passes after fix
```

---

**Remember:** Nova is a code fixer, not a test fixer. Always put bugs in the implementation!
