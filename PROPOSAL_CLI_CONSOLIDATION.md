# Proposal: Consolidate to One CLI Path (Deep Agent Default)
## Linear Task OS-1035

---

## Executive Summary

This proposal outlines a plan to consolidate Nova CI-Rescue's multiple CLI implementations into a single, unified CLI path that uses the Deep Agent as the default implementation. This consolidation will simplify maintenance, improve user experience, and establish the Deep Agent as the primary execution path while maintaining backward compatibility.

---

## Current State Analysis

### 1. Multiple CLI Files
Currently, Nova has **6 different CLI-related files**:
- `src/nova/cli.py` - Main CLI entry point
- `src/nova/cli_enhanced.py` - Enhanced CLI with additional features
- `src/nova/cli_integration.py` - Integration-specific CLI
- `src/nova/cli_migration_helper.py` - Migration utilities
- `src/nova/cli_backup.py` - Backup of original CLI
- `src/nova_deep_agent/cli.py` - Deep Agent specific CLI

### 2. Multiple Agent Implementations
- `deep_agent.py` - Current Deep Agent implementation
- `nova_deep_agent.py` - Nova-specific Deep Agent variant
- `llm_agent.py` - Legacy LLM Agent
- `mock_llm.py` - Mock agent for testing

### 3. Current Problems
- **Fragmentation**: Multiple entry points confuse users and developers
- **Maintenance burden**: Changes need to be synchronized across multiple files
- **Inconsistent behavior**: Different CLIs may have different features/options
- **Unclear default**: Users don't know which implementation to use

---

## Proposed Solution

### Phase 1: Unified CLI Interface (Week 1)

#### 1.1 Create Single Entry Point
```
src/nova/cli.py (MAIN - keep this only)
```

#### 1.2 Consolidate Commands
```python
# Unified command structure
nova fix [options]      # Default: Deep Agent
nova test [options]     # Run tests only
nova config [options]   # Configuration management
nova version           # Version info
```

#### 1.3 Deep Agent as Default
```python
# Default behavior
nova fix .             # Uses Deep Agent automatically
nova fix --agent=deep  # Explicit Deep Agent (same as default)
nova fix --agent=legacy # Fallback to legacy if needed
```

### Phase 2: Backend Consolidation (Week 2)

#### 2.1 Agent Factory Pattern
```python
# src/nova/agent/factory.py
class AgentFactory:
    @staticmethod
    def create_agent(agent_type="deep", **kwargs):
        if agent_type == "deep":
            return NovaDeepAgent(**kwargs)
        elif agent_type == "legacy":
            return LLMAgent(**kwargs)  # For backward compatibility
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
```

#### 2.2 Unified Configuration
```yaml
# nova.config.yaml
agent:
  type: deep  # Default agent type
  model: gpt-4
  max_iterations: 5
  
# Legacy support
legacy:
  enabled: false  # Can be enabled if needed
```

### Phase 3: Migration & Cleanup (Week 3)

#### 3.1 Migration Path
1. **Deprecation warnings** in old CLI files
2. **Redirect old commands** to new unified CLI
3. **Configuration migration** tool for old configs
4. **Documentation updates** with migration guide

#### 3.2 File Consolidation Plan
```
KEEP:
- src/nova/cli.py (unified CLI)
- src/nova/agent/deep_agent.py (main implementation)
- src/nova/agent/state.py (shared state management)

ARCHIVE:
- cli_*.py files → archive/legacy_cli/
- llm_agent.py → archive/legacy_agents/

REMOVE (after migration period):
- Duplicate implementations
- Backup files
```

---

## Implementation Strategy

### Step 1: Prepare Unified CLI (Day 1-2)
```python
# src/nova/cli.py structure
@app.command()
def fix(
    repo_path: Path = ".",
    agent: str = "deep",  # Default to Deep Agent
    max_iters: int = None,
    config: Path = None,
    verbose: bool = False
):
    """Fix failing tests using AI agent (default: Deep Agent)."""
    
    # Load configuration
    config_data = load_config(config)
    
    # Override agent type if specified
    agent_type = agent or config_data.get("agent", {}).get("type", "deep")
    
    # Create agent using factory
    agent_instance = AgentFactory.create_agent(
        agent_type=agent_type,
        config=config_data,
        verbose=verbose
    )
    
    # Run the fix process
    return agent_instance.fix(repo_path, max_iters)
```

### Step 2: Add Compatibility Layer (Day 3-4)
```python
# Backward compatibility wrapper
@app.command(hidden=True)  # Hide from help but still works
def legacy_fix(**kwargs):
    """Deprecated: Use 'nova fix' instead."""
    print("Warning: This command is deprecated. Use 'nova fix' instead.")
    return fix(**kwargs)
```

### Step 3: Implement Agent Factory (Day 5)
- Create factory for agent instantiation
- Ensure consistent interface across agents
- Add validation and error handling

### Step 4: Update Documentation (Day 6-7)
- Update README with new CLI structure
- Create migration guide
- Update all examples and tutorials

---

## Benefits

### 1. **Simplicity**
- Single entry point for users
- Clear default behavior
- Reduced cognitive load

### 2. **Maintainability**
- One CLI to maintain
- Centralized configuration
- Easier testing

### 3. **Performance**
- Deep Agent as default leverages best implementation
- Reduced import overhead
- Optimized execution path

### 4. **User Experience**
- Consistent command structure
- Better error messages
- Progressive disclosure of options

---

## Backward Compatibility

### Compatibility Matrix
| Old Command | New Command | Status |
|------------|-------------|---------|
| `nova fix` | `nova fix` | ✅ Same |
| `nova-deep fix` | `nova fix` | ✅ Default |
| `nova fix --llm` | `nova fix --agent=legacy` | ⚠️ Deprecated |
| Custom CLIs | `nova fix --config=custom.yaml` | 📝 Migrate |

### Grace Period
- **3 months**: Deprecation warnings
- **6 months**: Hidden but functional
- **1 year**: Complete removal

---

## Risk Mitigation

### Potential Risks & Solutions

1. **Risk**: Breaking existing workflows
   - **Solution**: Comprehensive compatibility layer
   - **Solution**: Gradual migration with warnings

2. **Risk**: Performance regression
   - **Solution**: Benchmark before/after
   - **Solution**: Keep legacy mode available initially

3. **Risk**: User confusion during transition
   - **Solution**: Clear migration documentation
   - **Solution**: Helpful error messages with guidance

4. **Risk**: Integration breakage
   - **Solution**: Extensive integration testing
   - **Solution**: Beta period with early adopters

---

## Success Metrics

### Quantitative
- ✅ Single CLI entry point achieved
- ✅ 100% feature parity maintained
- ✅ < 5% performance overhead
- ✅ Zero breaking changes for basic usage

### Qualitative
- ✅ Simplified onboarding for new users
- ✅ Reduced support questions about "which CLI to use"
- ✅ Cleaner codebase with less duplication
- ✅ Easier to add new features

---

## Timeline

### Week 1: Foundation
- [ ] Unified CLI structure
- [ ] Agent factory implementation
- [ ] Basic Deep Agent integration

### Week 2: Migration
- [ ] Compatibility layer
- [ ] Configuration migration
- [ ] Deprecation warnings

### Week 3: Polish
- [ ] Documentation update
- [ ] Testing & validation
- [ ] Performance optimization

### Week 4: Release
- [ ] Beta release to early adopters
- [ ] Gather feedback
- [ ] Final adjustments

---

## Testing Strategy

### 1. Unit Tests
```python
def test_default_agent_is_deep():
    """Ensure Deep Agent is used by default."""
    agent = AgentFactory.create_agent()
    assert isinstance(agent, NovaDeepAgent)

def test_legacy_compatibility():
    """Ensure legacy agent still works."""
    agent = AgentFactory.create_agent(agent_type="legacy")
    assert isinstance(agent, LLMAgent)
```

### 2. Integration Tests
- Test all existing workflows still work
- Test migration from old to new CLI
- Test configuration compatibility

### 3. Performance Tests
- Benchmark Deep Agent vs Legacy
- Measure CLI startup time
- Profile memory usage

---

## Configuration Examples

### Default Configuration (Deep Agent)
```yaml
# nova.config.yaml
agent:
  type: deep  # Optional, this is default
  model: gpt-4
  temperature: 0.0
  max_iterations: 5
```

### Legacy Mode (if needed)
```yaml
# nova-legacy.config.yaml
agent:
  type: legacy
  model: gpt-4
  # Legacy-specific settings
```

### Advanced Configuration
```yaml
# nova-advanced.config.yaml
agent:
  type: deep
  model: gpt-4
  tools:
    - plan_todo
    - open_file
    - write_file
    - run_tests
  safety:
    max_patch_lines: 500
    max_affected_files: 5
```

---

## Documentation Updates Required

1. **README.md**
   - Update main usage examples
   - Add migration notice
   - Update installation instructions

2. **docs/quickstart.md**
   - Use new CLI in all examples
   - Add "What's New" section
   - Include migration FAQ

3. **docs/migration-guide.md** (NEW)
   - Step-by-step migration instructions
   - Common issues and solutions
   - Configuration conversion tool

4. **API Documentation**
   - Update CLI reference
   - Document agent factory
   - Add deprecation notices

---

## Rollback Plan

If issues arise during rollout:

1. **Immediate**: Feature flag to disable Deep Agent default
2. **Short-term**: Revert to multi-CLI with clear documentation
3. **Long-term**: Re-evaluate approach based on feedback

```python
# Emergency override
NOVA_USE_LEGACY=1 nova fix .  # Force legacy mode
```

---

## Conclusion

Consolidating to a single CLI path with Deep Agent as the default will:
- **Simplify** the user experience
- **Reduce** maintenance burden
- **Improve** performance and reliability
- **Maintain** backward compatibility
- **Position** Nova for future enhancements

The phased approach ensures a smooth transition with minimal disruption to existing users while establishing a clean, maintainable foundation for future development.

---

## Next Steps

1. **Review & Approval**: Get stakeholder sign-off on this proposal
2. **Create Implementation PRs**: Break down into manageable chunks
3. **Set up Feature Branch**: `feature/cli-consolidation`
4. **Begin Phase 1**: Start with unified CLI structure
5. **Community Communication**: Announce plans and timeline

---

*Proposal prepared for Linear Task OS-1035*
*Author: Nova CI-Rescue Team*
*Date: 2025-01-16*
