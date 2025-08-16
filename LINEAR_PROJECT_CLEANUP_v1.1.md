# Linear Project Cleanup Plan (CI-Rescue v1.0 to v1.1)

## Overview

This document outlines the re-evaluation of all outstanding v1.0 tasks in light of the Deep Agent overhaul in v1.1. Each task is categorized as: **Cancel**, **Merge into v1.1**, **Keep**, or **Defer to v1.2**.

## Task Decisions

### ✅ COMPLETED - OS-1031: LangChain Tool Wrappers (run_tests & apply_patch)

**Decision: Merge into v1.1** ✅ **DONE**

- Successfully implemented unified tools module (`src/nova/agent/unified_tools.py`)
- Consolidated all LangChain tool definitions into single authoritative source
- Eliminated duplicate implementations
- All agents now use unified tools

### 🔄 OS-1028: CLI Uses NovaDeepAgent

**Decision: Merge into v1.1**

- **Action**: Replace legacy fix-loop in CLI with NovaDeepAgent.run()
- **Rationale**: v1.1 includes swapping CLI's fix-loop to call NovaDeepAgent once per iteration
- **Status**: To be implemented as part of CLI agent swap in v1.1
- **Notes**: Remove all old code paths and toggles for legacy LLMAgent

### ❌ OS-1015: Retire Legacy LLMAgent & Flags

**Decision: Cancel as obsolete**

- **Rationale**: Deep Agent architecture completely eliminates legacy agent
- **Action**: Will be handled automatically during v1.1 migration
- **Notes**: No separate v1.0 patch needed - v1.1 makes this redundant

### 🔄 OS-1009: Consolidate Patch Safety Checks

**Decision: Merge into v1.1**

- **Action**: Unify duplicate patch validation logic
- **Implementation**: Use patch_guard.preflight_patch_checks() as single safety layer
- **Remove**: Legacy SafetyLimits.validate_patch() code
- **Status**: Part of v1.1 safety & guardrails work

### ✏️ OS-987: Documentation/UX Improvements

**Decision: Keep (with scope update)**

- **Action**: Update documentation to reflect new Deep Agent architecture
- **Changes**: Document one-agent workflow instead of multi-node "Happy Path" flow
- **Priority**: User-facing docs remain important
- **Notes**: Ensure new agent capabilities/limitations are correctly described

### ⏭️ OS-950: Multi-Language & Complex Failure Support

**Decision: Defer to v1.2**

- **Rationale**: Focus v1.1 on stability and parity with v1.0
- **Includes**: Non-Python tests, multiple concurrent failures, advanced enhancements
- **Timeline**: After Deep Agent migration is solid

### ⏭️ OS-912: Daytona Sandbox Integration

**Decision: Defer to v1.2**

- **Rationale**: Optional improvement, not critical for v1.1
- **Action**: Replace Docker with Daytona or other modern sandbox tech
- **Timeline**: Safe to swap after v1.1 agent integration complete

### ⏭️ OS-881/OS-1046: Marketing & Validation Tasks (5 OSS PR Fixes)

**Decision: Defer to v1.2**

- **Rationale**: Hold off proof-of-value push until new agent is live
- **Includes**: 5 OSS PR fixes milestone, performance benchmarking
- **Timeline**: Execute after v1.1 complete for more impactful results
- **Notes**: Already tracked as OS-1046 in Linear

## Summary

### v1.1 Focus (Active Work)

1. ✅ **OS-1031**: Unified tool definitions (COMPLETED)
2. 🔄 **OS-1028**: CLI uses NovaDeepAgent
3. 🔄 **OS-1009**: Consolidate patch safety checks
4. ✏️ **OS-987**: Update documentation for new architecture

### Cancelled (Obsolete)

- ❌ **OS-1015**: Retire legacy agent (redundant with v1.1)

### Deferred to v1.2

- ⏭️ **OS-950**: Multi-language support
- ⏭️ **OS-912**: Daytona sandbox
- ⏭️ **OS-881/OS-1046**: Marketing/validation (5 OSS fixes)

## Implementation Notes

Most tool- and agent-related v1.0 tasks are absorbed into the v1.1 initiative or rendered moot by it. We cancel truly obsolete items and merge the valuable ones into active epics like "Unified Tools" and "Deep Agent CLI Integration." Ancillary enhancements and marketing goals are pushed to v1.2 to give v1.1 a tight focus on the core architecture transition.

## Next Steps

1. Continue with Deep Agent integration tasks
2. Update CLI to use NovaDeepAgent
3. Consolidate safety checks into single implementation
4. Update all documentation to reflect new architecture
5. Complete v1.1 before starting v1.2 deferred items

---

_Last Updated: August 16, 2025_
_Status: Unified Tools COMPLETED ✅_
