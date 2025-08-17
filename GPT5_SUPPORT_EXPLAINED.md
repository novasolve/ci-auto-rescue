# Why GPT-5 Doesn't Work (And How to Fix It)

## 🚫 The Current Problem

**GPT-5 fails with this error:**

```
"Unsupported value: 'messages[3].role' does not support 'function' with this model."
```

## 🔍 Root Cause: A Bug in Nova's Code

The issue is in `src/nova/agent/deep_agent.py`:

1. **Lines 74-77:** Nova correctly detects GPT-5 and sets `use_react = True`

   ```python
   if model_name == "gpt-5":
       llm = ChatOpenAI(model_name="gpt-5", temperature=0)
       use_react = True  # GPT-5 may not support function calling
   ```

2. **Lines 132-138:** But then IGNORES the `use_react` flag!
   ```python
   # Always use OpenAI function-calling agent for reliable multi-input tool support
   agent_executor = initialize_agent(
       agent=AgentType.OPENAI_FUNCTIONS,  # ❌ ALWAYS uses function calling!
   ```

**The bug:** Nova always uses `OPENAI_FUNCTIONS` agent type, even for GPT-5.

## 📊 Model Capabilities

| Model     | Function Calling | ReAct Pattern | Message Roles Supported                   |
| --------- | ---------------- | ------------- | ----------------------------------------- |
| GPT-4     | ✅ Yes           | ✅ Yes        | `system`, `user`, `assistant`, `function` |
| GPT-3.5   | ✅ Yes           | ✅ Yes        | `system`, `user`, `assistant`, `function` |
| **GPT-5** | ❌ No            | ✅ Yes        | `system`, `user`, `assistant` only        |
| Claude    | ❌ No            | ✅ Yes        | `system`, `user`, `assistant` only        |

## 🔧 The Fix

### Option 1: Quick Workaround (Use GPT-4)

```yaml
# nova.config.yml
model: gpt-4
```

### Option 2: Apply the Patch (Fix GPT-5 Support)

```bash
# Apply the fix
git apply fix_gpt5_support.patch

# Then use GPT-5
echo "model: gpt-5" > nova.config.yml
nova fix .
```

### What the Patch Does:

Changes the agent initialization to respect the `use_react` flag:

```python
if use_react:
    # For GPT-5, Claude - use ReAct pattern (no function calling)
    agent = AgentType.ZERO_SHOT_REACT_DESCRIPTION
else:
    # For GPT-4, GPT-3.5 - use function calling
    agent = AgentType.OPENAI_FUNCTIONS
```

## 🤔 Why This Matters

### Function Calling (GPT-4 style):

- Tools are registered as functions
- Model gets structured function schemas
- Responses include function calls with arguments
- More reliable and structured

### ReAct Pattern (GPT-5 compatible):

- Tools are described in text
- Model generates "Thought, Action, Observation" chains
- Less structured but more flexible
- Works with any model

## 📝 Technical Details

### What's a "function" role message?

When using function calling, the conversation includes:

```json
{
  "role": "function",
  "name": "run_tests",
  "content": "Test results: 2 passed, 1 failed"
}
```

GPT-5 doesn't understand this `"role": "function"` - it only knows `system`, `user`, and `assistant`.

### What's ReAct Pattern?

Instead of function messages, it uses plain text:

```
Thought: I need to run the tests to see what's failing
Action: run_tests
Action Input: {"test_file": "test_math.py"}
Observation: Test results: 2 passed, 1 failed
Thought: Now I need to fix the failing test...
```

## 🚀 Future Improvements

Nova could be improved to:

1. **Auto-detect model capabilities** - Query the model's capabilities API
2. **Fallback gracefully** - If function calling fails, switch to ReAct
3. **Support environment variables** - `NOVA_LLM_MODEL=gpt-5`
4. **Better error messages** - "GPT-5 detected, switching to ReAct pattern"

## 📌 Summary

**Current Status:** GPT-5 doesn't work due to a bug where Nova ignores the `use_react` flag.

**Quick Fix:** Use GPT-4 instead (change in `nova.config.yml`)

**Proper Fix:** Apply the patch to make Nova respect the `use_react` flag for GPT-5.

The issue isn't that GPT-5 is inherently incompatible - Nova just has a bug where it always tries to use function calling even when it shouldn't.
