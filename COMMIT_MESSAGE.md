feat: Complete CLI consolidation with Deep Agent as default

## Summary

Implements all CLI consolidation requirements from audit report to provide a single, unified CLI entry point with Deep Agent as the default and legacy mode for backward compatibility.

## Changes

### Core Implementation

- Add `--legacy-agent` flag to `nova fix` command for backward compatibility
- Create `AgentFactory` for dynamic agent selection (deep vs legacy)
- Implement minimal `LegacyAgent` class since original LLMAgent was removed
- Update CLI to use AgentFactory instead of direct Deep Agent instantiation

### Documentation & UX

- Update CLI help text to clearly state Deep Agent is default
- Add deprecation warnings for legacy agent (will be removed in v2.0)
- Update main app description to mention "Deep Agent (AI-powered)"
- Add deprecation warning to `nova_deep_agent/cli.py` module

### Testing

- Add comprehensive test suite in `tests/test_cli_consolidation.py`
- Test help text updates and flag availability
- Verify default behavior uses Deep Agent
- Test legacy flag properly selects legacy agent
- Validate AgentFactory functionality

## User Impact

### No Breaking Changes

- Existing `nova fix` commands work without modification
- Configuration files remain compatible
- API keys and environment variables unchanged

### New Capability

- Users can use `--legacy-agent` flag if they need the old behavior
- Clear deprecation path with removal timeline (v2.0)

## Usage Examples

```bash
# Default - uses Deep Agent
nova fix

# Legacy mode (shows deprecation warning)
nova fix --legacy-agent

# Help shows new options
nova fix --help
```

## Verification

All tests pass:

- CLI help text properly updated ✅
- Legacy flag shown with deprecation notice ✅
- Default behavior uses Deep Agent ✅
- Legacy flag uses legacy agent ✅

Fixes all issues identified in audit report for PR #36.
