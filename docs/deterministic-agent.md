# Deterministic Deep Agent

## Overview

The Deterministic Deep Agent is an alternative execution mode for Nova that implements a structured Plan-Edit-Apply-Test (PEAT) cycle. Unlike the default ReAct-based agent that can take various paths through the tool space, the deterministic agent follows a strict, predictable workflow designed to fix all failing tests in one coordinated effort.

## Key Differences from ReAct Agent

| Feature | ReAct Agent (Default) | Deterministic Agent |
|---------|----------------------|-------------------|
| Execution Flow | Dynamic tool selection | Fixed PEAT cycle |
| Iterations | Up to 6 by default | Maximum 2 cycles |
| Planning | Incremental per fix | Upfront comprehensive plan |
| Patching | Multiple small patches | One unified patch per cycle |
| LLM Calls | Many tool invocations | Direct LLM completions |
| Predictability | Variable paths | Deterministic sequence |

## Architecture

### Phase 1: Plan
- Analyzes all failing tests at once
- Generates a comprehensive fix strategy
- Identifies all files that need modification
- Stores plan in agent state for transparency

### Phase 2: Edit
- Reads all relevant source files (excluding tests)
- Generates complete updated file contents for each
- Creates in-memory edits before any disk writes
- Computes unified diff for all changes

### Phase 3: Apply
- Applies the complete patch atomically
- Runs safety checks and critic review
- Commits all changes in one git commit
- Handles failures gracefully without partial application

### Phase 4: Test
- Runs the full test suite once
- Checks for regressions (new failures)
- Rolls back if regressions detected
- Decides whether to iterate or complete

## Usage

To use the deterministic agent, add the `--deterministic` flag:

```bash
# Standard ReAct agent (default)
nova fix /path/to/repo

# Deterministic PEAT agent
nova fix /path/to/repo --deterministic
```

## When to Use

The deterministic agent is ideal for:

1. **Simple, well-understood failures** - When the fix is straightforward
2. **Multiple related failures** - When several tests fail due to the same root cause
3. **Speed requirements** - Fewer LLM calls mean faster execution
4. **Predictable behavior** - When you need consistent, reproducible runs
5. **Debugging** - Easier to trace through the fixed sequence

The ReAct agent remains better for:

1. **Complex, exploratory fixes** - When the solution requires investigation
2. **Large codebases** - When finding the right files is challenging
3. **Iterative refinement** - When fixes need multiple adjustments
4. **Unknown failure patterns** - When the root cause is unclear

## Implementation Details

### Loop Control
- Maximum 2 iterations (configurable via `state.max_iterations`)
- First iteration attempts to fix all failures
- Second iteration only runs if some original tests still fail
- No iteration if regression detected (immediate rollback)

### Safety Features
- **Regression Detection**: Automatically rolls back if new tests fail
- **Critic Review**: All patches reviewed before application
- **Safety Checks**: Standard Nova safety policies enforced
- **Atomic Application**: All-or-nothing patch application

### State Management
```python
# Key state fields used
state.plan              # The generated fix plan
state.patches_applied   # List of applied patches
state.critic_feedback   # Feedback from rejected patches
state.final_status      # Outcome: success/patch_error/max_iters
```

### Direct LLM Usage
Instead of LangChain's agent loop, uses direct LLM calls:
```python
client = LLMClient(settings=self.settings)
plan = client.complete(system="...", user=plan_prompt, max_tokens=1000)
```

## Example Workflow

```
1. Start with 3 failing tests
   ↓
2. PLAN: "Fix divide() for zero, fix add() logic, update validate()"
   ↓
3. EDIT: Read math.py, generate fixed version with all 3 fixes
   ↓
4. APPLY: Create unified diff, critic approves, git commit
   ↓
5. TEST: Run suite → 1 test still fails
   ↓
6. ITERATE: New plan for remaining failure
   ↓
7. PLAN: "Fix edge case in validate() for negative numbers"
   ↓
8. EDIT: Read math.py again, generate updated version
   ↓
9. APPLY: Create diff, apply patch, commit
   ↓
10. TEST: All tests pass → SUCCESS
```

## Configuration

The deterministic mode respects all standard Nova settings:
- `--max-iters` - Capped at 2 for deterministic mode
- `--timeout` - Overall execution timeout
- `--model` - LLM model selection
- `--verbose` - Detailed logging of each phase

## Limitations

1. **No Test Reading**: Like all Nova agents, cannot read test files
2. **Context Windows**: Large files may exceed LLM context limits
3. **Fixed Sequence**: Less flexible than ReAct for exploration
4. **Two Iterations Max**: Complex fixes may need more cycles

## Future Enhancements

- Parallel file processing in Edit phase
- Incremental re-planning based on critic feedback
- Integration with LangGraph for better state management
- Configurable iteration limit beyond 2