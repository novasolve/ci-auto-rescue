# Model Configuration & Bug Analysis

## 🔍 **Environment Variable for Model**

**⚠️ Currently, Nova does NOT read the model from environment variables!**

The model is configured via:

1. **Config file** (nova.config.yml): `model: gpt-4`
2. **Code default**: `default_llm_model: str = "gpt-5"` in `src/nova/config.py`

**There is NO environment variable support currently.** The `MODEL=gpt-4.1alias` in your environment is NOT being used by Nova.

### How to Change the Model:

#### Option 1: Create a config file

```yaml
# nova.config.yml
model: gpt-4
```

#### Option 2: Modify the code default

```python
# src/nova/config.py line 20
default_llm_model: str = "gpt-4"  # Change from "gpt-5"
```

---

## 🐛 **The Bug Explained**

### What's Happening:

1. Nova defaults to using **GPT-5** model
2. GPT-5 is configured to use **ReAct pattern** (line 77 in deep_agent.py)
3. But something is still trying to use **function calling**
4. GPT-5 doesn't support the `"function"` role in messages

### The Error:

```
openai.BadRequestError: Error code: 400 - {'error': {'message':
"Unsupported value: 'messages[3].role' does not support 'function' with this model."
```

### The Problem:

In `deep_agent.py`, even though it sets `use_react = True` for GPT-5, the agent is still being initialized with function calling tools, which causes the error when it tries to send a message with role='function' to GPT-5.

### Why It Fails:

- **GPT-4** supports: `system`, `user`, `assistant`, `function` roles
- **GPT-5** supports: `system`, `user`, `assistant` roles only
- Nova is sending a message with `role='function'` which GPT-5 rejects

---

## 🔧 **Quick Fix**

### Immediate Solution: Switch to GPT-4

Create a config file:

```bash
cat > nova.config.yml << 'EOF'
model: gpt-4
EOF
```

Then run Nova:

```bash
nova fix .
```

### Alternative: Fix the Code

The issue is in `src/nova/agent/deep_agent.py`. When `use_react = True`, it should use a different agent initialization that doesn't use function calling.

Currently line 115-135:

```python
if use_react:
    # For models that don't support function calling well
    agent_executor = initialize_agent(
        tools=[tool_obj for _, tool_obj in self.tools.items()],
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,  # This still uses function calling!
        verbose=self.verbose,
        max_iterations=50,
        handle_parsing_errors=True,
        early_stopping_method="generate",
    )
```

The problem is that even with `ZERO_SHOT_REACT_DESCRIPTION`, LangChain might still try to use function calling with certain tool configurations.

---

## 📝 **To Add Environment Variable Support**

If you want Nova to read from environment variables, you could modify `src/nova/cli.py`:

```python
# Add after line 216
import os
if not config_data or not config_data.model:
    # Check environment variable
    env_model = os.getenv("NOVA_LLM_MODEL") or os.getenv("NOVA_MODEL")
    if env_model:
        settings.default_llm_model = env_model
```

Then you could use:

```bash
export NOVA_LLM_MODEL=gpt-4
nova fix .
```

---

## 🎯 **Recommended Actions**

1. **Immediate:** Create `nova.config.yml` with `model: gpt-4`
2. **Better:** Add environment variable support to Nova
3. **Best:** Fix the ReAct pattern initialization to properly avoid function calling for GPT-5

The root cause is that Nova's GPT-5 support isn't fully implemented - it tries to use ReAct pattern but still ends up sending function-role messages that GPT-5 doesn't support.
