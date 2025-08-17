# Preventing Future Model Configuration Issues

## How to Avoid GPT-5-like Configuration Problems

Based on our recent audit where GPT-5 was incorrectly configured without function calling support, here are key recommendations to prevent similar issues:

### 1. **Single Source of Truth**
- Maintain model capabilities in ONE central location
- Import from that single source everywhere else
- Currently split between `deep_agent.py` and `model_config.py`

### 2. **Automated Testing for New Models**
```python
# Add to test suite
def test_model_capabilities():
    for model in ["gpt-5", "gpt-5-turbo"]:
        caps = get_model_capabilities(model)
        # Verify against OpenAI docs
        assert caps['function_calling'] == True
```

### 3. **Runtime Validation**
- Test model availability at startup
- Detect capabilities programmatically instead of hardcoding
- Log when fallbacks are triggered

### 4. **Clear Documentation**
- Document each model's capabilities when added
- Include verification date and API version
- Add migration guides for breaking changes

### 5. **Better Error Messages**
```python
# Instead of silent fallback
if model_unavailable:
    raise ConfigError(
        f"{model} not available. Check:\n"
        f"1. API key is set\n"
        f"2. Model name is correct\n"
        f"3. Your account has access"
    )
```

### 6. **Configuration Validation**
- Use Pydantic models for type safety
- Validate configs at startup
- Add CI checks for config changes

### 7. **Feature Flags**
```python
# Gradual rollout of new models
if feature_flag("enable_gpt5"):
    available_models.append("gpt-5")
```

### 8. **Monitoring**
- Track model usage and success rates
- Alert on high fallback rates
- Monitor API errors by model

## Quick Checklist for Adding New Models

- [ ] Add to central MODEL_CAPABILITIES registry
- [ ] Verify capabilities with official docs
- [ ] Add automated tests
- [ ] Test with real API calls
- [ ] Document in SUPPORTED_MODELS.md
- [ ] Update user guides
- [ ] Add telemetry tracking
- [ ] Test fallback scenarios

## What Went Wrong with GPT-5

1. **Assumption**: GPT-5 didn't support function calling
2. **Reality**: GPT-5 does support function calling (per OpenAI docs)
3. **Impact**: Forced unnecessary ReAct pattern usage (slower)
4. **Root Cause**: No validation against actual API capabilities

## Immediate Actions

1. Centralize model configuration (this sprint)
2. Add capability tests (next PR)
3. Document all current models (today)
4. Add startup validation (next sprint)
