# Environment Variable Resolution and Tool Wrapper Fixes

## Summary of Fixes Applied

### 1. ✅ Fixed Environment Variable Resolution

**Problem**: Nova was ignoring `NOVA_MODEL` and `NOVA_DEFAULT_LLM_MODEL` environment variables, always defaulting to "gpt-4.1alias"

**Solution Implemented**:
1. Updated `NovaSettings` to read environment variables in `default_factory`:
   ```python
   default_llm_model: str = field(default_factory=lambda: 
       os.getenv("NOVA_MODEL") or 
       os.getenv("NOVA_DEFAULT_LLM_MODEL") or 
       os.getenv("MODEL") or 
       "gpt-4")
   ```

2. Modified `merge_with_yaml()` to preserve environment variable settings:
   - Environment variables are no longer overridden by config files
   - This ensures env vars take precedence over YAML configuration

3. Updated CLI priority order to ensure correct precedence:
   - CLI `--model` option (highest)
   - Environment variables
   - Config file
   - Default value

### 2. ✅ Fixed "Missing input keys: {'path'}" Error

**Problem**: GPT-5 tool wrapper was causing parameter passing issues

**Solution Implemented**:
- Simplified the tool wrapper for GPT-5
- `write_file` tool now accepts two input formats:
  1. JSON format: `{"path": "file.py", "new_content": "content"}`
  2. Delimiter format: `path:::content`
- Other tools are kept as-is instead of wrapping all multi-input tools
- Fixed agent initialization with proper input handling

### 3. ✅ Updated Documentation

- Updated `docs/git-branching-guide.md` to reflect that environment variables now take precedence over config files
- Added clear notes about the priority order

## Configuration Priority Order

The final priority order for model configuration is:

1. **CLI `--model` option** (highest priority)
   ```bash
   nova fix . --model gpt-4
   ```

2. **Environment Variables** (overrides config file)
   ```bash
   export NOVA_MODEL=gpt-4              # Primary
   export NOVA_DEFAULT_LLM_MODEL=gpt-4  # Backward compatibility
   export MODEL=gpt-4                  # Legacy support
   ```

3. **Configuration File**
   ```yaml
   # nova.config.yml
   model: gpt-4
   # or
   default_llm_model: gpt-4
   ```

4. **Default**: `gpt-4`

## Testing

All fixes have been tested and verified:
- ✅ Environment variables are correctly read
- ✅ Environment variables take precedence over config files
- ✅ All three env var names work (NOVA_MODEL, NOVA_DEFAULT_LLM_MODEL, MODEL)
- ✅ Priority order is: NOVA_MODEL > NOVA_DEFAULT_LLM_MODEL > MODEL
- ✅ Tool wrapper no longer causes missing input keys error

## Result

Nova will now:
1. Correctly use the model specified in environment variables
2. Allow environment-based overrides of config file settings
3. Handle GPT-5 tool inputs without parameter errors
4. Provide clear precedence: CLI > Environment > Config > Default

The "gpt-4.1alias" issue is resolved - Nova will use the model you specify via environment variables!
