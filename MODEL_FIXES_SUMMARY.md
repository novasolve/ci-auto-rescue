# Model Fixes and Improvements Summary

## Issues Fixed

### 1. ✅ Fixed "gpt-4.1alias" Model Error

- **Problem**: Nova was trying to use "gpt-4.1alias" directly with OpenAI API, causing a 404 error
- **Solution**: Added intelligent model mapping that converts "gpt-4.1alias" and similar aliases to "gpt-4"
- **Location**: `src/nova/agent/llm_client.py` - `_get_openai_model_name()` method

### 2. ✅ Changed Default Model to GPT-4

- **Problem**: Default was set to non-existent "gpt-5"
- **Solution**: Changed default to "gpt-4" for better out-of-box compatibility
- **Location**: `src/nova/config.py` - `NovaSettings.default_llm_model`

### 3. ✅ Added Runtime Model Fallback

- **Problem**: If a model wasn't found, Nova would crash
- **Solution**: Added automatic fallback to GPT-4 when model errors occur
- **Location**: `src/nova/agent/llm_client.py` - `_complete_openai()` method

### 4. ✅ Added --model CLI Option

- **Problem**: No easy way to specify model from command line
- **Solution**: Added `--model` / `-m` option to `nova fix` command
- **Location**: `src/nova/cli.py` - `fix()` command

### 5. ✅ Fixed Invalid "gpt-4o" Fallback

- **Problem**: Nova was falling back to "gpt-4o" which isn't a valid OpenAI model
- **Solution**: Changed all fallbacks to use valid "gpt-4" model
- **Location**: `src/nova/agent/llm_client.py`

## Model Configuration Priority

Nova now supports model configuration with clear precedence:

1. **CLI Option** (highest priority)

   ```bash
   nova fix . --model gpt-4
   ```

2. **Config File**

   ```yaml
   # nova.config.yml
   model: gpt-4
   ```

3. **Environment Variables**

   ```bash
   export NOVA_MODEL=gpt-4
   export NOVA_LLM_MODEL=gpt-4  # alternative
   export MODEL=gpt-4           # legacy
   ```

4. **Default**: `gpt-4`

## Supported Model Mappings

| Input Model   | Maps To | Notes                    |
| ------------- | ------- | ------------------------ |
| gpt-4.1alias  | gpt-4   | Fixes the terminal error |
| gpt-4.1\*     | gpt-4   | Any GPT-4.1 variant      |
| gpt-5\*       | gpt-4   | Until GPT-5 is available |
| gpt-4o        | gpt-4   | Internal alias           |
| unknown-model | gpt-4   | Any unrecognized model   |

## Git Branching Documentation

Created comprehensive guide at `docs/git-branching-guide.md` covering:

- Default timestamped branch behavior
- `NOVA_FIX_BRANCH_NAME` environment variable
- Model configuration options
- Best practices

## How to Use

### Fix the "gpt-4.1alias" Error

The error is now automatically fixed. When Nova encounters "gpt-4.1alias":

1. It maps it to "gpt-4"
2. Shows a warning: "Unknown model 'gpt-4.1alias', falling back to gpt-4"
3. Continues execution with GPT-4

### Specify a Different Model

```bash
# Via CLI
nova fix . --model gpt-3.5-turbo

# Via environment
export NOVA_MODEL=gpt-4-turbo
nova fix .

# Via config file
echo "model: gpt-4" > nova.config.yml
nova fix .
```

### Use Consistent Branch Names

```bash
# Instead of timestamped branches
export NOVA_FIX_BRANCH_NAME="nova-fixes"
nova fix .
```

## Testing

All fixes have been tested and verified:

- ✅ Model mapping correctly handles all aliases
- ✅ CLI option is working
- ✅ Default model is set to gpt-4
- ✅ Runtime fallback works for invalid models
- ✅ Environment variables are properly read

The "gpt-4.1alias" error that was shown in the terminal output is now completely resolved!
