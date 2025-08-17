# Model Configuration & Test Suite Issues Summary

## 🤖 Current Model Configuration

### Model Being Used: **GPT-5**

Based on your terminal output (line 811):

```
🚀 Using GPT-5 model with ReAct pattern
```

### Where It's Configured:

1. **Default Model Setting:**

   - File: `src/nova/agent/deep_agent.py`
   - Line 70: `model_name = getattr(self.settings, 'default_llm_model', 'gpt-5')`
   - Default: GPT-5 (if not specified in settings)

2. **Model Selection Logic:**
   ```python
   # From src/nova/agent/deep_agent.py
   if model_name == "gpt-5":
       llm = ChatOpenAI(model_name="gpt-5", temperature=0)
       use_react = True  # GPT-5 may not support function calling
   ```

### The Error You're Seeing:

```
openai.BadRequestError: Error code: 400 - {'error': {'message':
"Unsupported value: 'messages[3].role' does not support 'function' with this model.",
'type': 'invalid_request_error', 'param': 'messages[3].role', 'code': 'unsupported_value'}}
```

**Issue:** GPT-5 doesn't support function calling in the same way as GPT-4, which is why Nova tries to use ReAct pattern instead.

---

## 📊 Test Suite Problem Summary

### The Core Issue: **Bug Placement**

You discovered that one of your test scenarios had the bug in the **wrong place**:

### ❌ **What Was Wrong (demo_math_ops initial version):**

```python
# math_ops.py (CORRECT implementation)
def sum_numbers(numbers):
    return sum(numbers)  # Returns 15 for [1,2,3,4,5]

# test_math_ops.py (WRONG test expectation)
def test_basic_arithmetic():
    assert result == 10  # ❌ Wrong! Should expect 15
```

**Problem:** Nova can't fix this because the code is correct but the test is wrong!

### ✅ **What It Should Be:**

```python
# math_ops.py (BUGGY implementation)
def sum_numbers(numbers):
    result = 1
    for n in numbers:
        result *= n  # Bug: multiplying instead of adding
    return result

# test_math_ops.py (CORRECT test expectation)
def test_basic_arithmetic():
    assert result == 15  # ✅ Correct expectation
```

**Solution:** Nova can now fix the buggy implementation to make the test pass!

---

## 🔍 Why This Matters

### Nova's Design Philosophy:

- **Tests are the source of truth** - They define what the code should do
- **Nova fixes implementation** - Not test expectations
- **Real-world alignment** - In practice, tests define requirements

### Test Suite Status:

| Test Suite                            | Bug Location           | Status           |
| ------------------------------------- | ---------------------- | ---------------- |
| **Your Original nova_test_suite.py**  | Implementation ✅      | Working          |
| **demo_math_ops (after fix)**         | Implementation ✅      | Working          |
| **Unified Test Suite (10 scenarios)** | Implementation ✅      | Working          |
| **Edge Cases (unfixable_bug, no_op)** | Tests (intentional) ⚠️ | Expected to fail |

### What We Verified:

- ✅ All 8 normal test scenarios have bugs in implementation files
- ✅ All tests have correct expectations
- ✅ 2 edge cases intentionally break this rule to test Nova's limits
- ✅ Created `verify_test_scenarios.py` to check this automatically

---

## 🚀 Quick Fixes

### To Change the Model:

You can set a different model by:

1. Setting environment variable: `export NOVA_LLM_MODEL=gpt-4`
2. Or in config file:
   ```yaml
   # nova.config.yaml
   default_llm_model: gpt-4
   ```

### To Test Everything Works:

```bash
# Verify test structure
python verify_test_scenarios.py

# Run unified test suite
./nova_unified_test_suite.py --generate --timeout 300
```

---

## 📝 Key Takeaways

1. **Model:** Currently using GPT-5 with ReAct pattern (doesn't support function calling)
2. **Test Philosophy:** Bugs belong in code, not tests
3. **Verification:** All test scenarios now follow correct pattern
4. **Tools Created:** Unified test suite + verification script to prevent future issues
