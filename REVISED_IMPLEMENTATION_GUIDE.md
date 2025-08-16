# Revised Implementation Guide: Direct CLI Consolidation

## OS-1035: Consolidate to One CLI Path (Deep Agent Default)

Based on comparison with the provided plan, this is the **streamlined approach** for immediate implementation.

---

## Executive Summary

**Goal**: Replace the legacy multi-step loop in `nova/cli.py` with a single Deep Agent invocation. No gradual migration, no backward compatibility options - just a clean, direct replacement.

**Timeline**: 1 week (not 4 weeks)

**Approach**: Rip off the band-aid - Deep Agent only, no legacy options

---

## Current Problem (Specific)

In `nova/cli.py`, the `fix` command currently:

```python
# CURRENT PROBLEMATIC CODE:
while state.current_iteration < state.max_iterations:
    # 1. Planner generates fixes
    planner_result = planner_node(state, telemetry, repo_path)

    # 2. Actor applies patches
    actor_result = actor_node(state, telemetry, repo_path)

    # 3. Critic reviews
    critic_result = critic_node(state, telemetry, repo_path)

    # 4. Loop continues...
```

This needs to be **completely removed** and replaced with:

```python
# NEW CLEAN CODE:
deep_agent = NovaDeepAgent(state, telemetry, git_manager, verbose)
success = deep_agent.run(failures_summary, error_details, code_snippets)
```

---

## Implementation Steps (Direct Approach)

### Day 1: Core Replacement

#### File: `src/nova/cli.py`

**1. Remove these imports:**

```python
# DELETE THESE:
from nova.nodes.planner import planner_node
from nova.nodes.actor import actor_node
from nova.nodes.critic import critic_node
from nova.agent.llm_agent import LLMAgent
```

**2. Add this import:**

```python
# ADD THIS:
from nova.agent.deep_agent import NovaDeepAgent
```

**3. Replace the entire fix loop:**

**DELETE** (lines approximately 200-400):

```python
# DELETE ALL OF THIS:
agent = None
if use_enhanced:
    agent = LLMAgent(repo_path)
else:
    # basic agent logic

while state.current_iteration < state.max_iterations:
    console.print(f"\n[bold]Iteration {state.current_iteration + 1}/{state.max_iterations}[/bold]")

    # Planning phase
    planner_result = planner_node(state, telemetry, repo_path)

    # Acting phase
    actor_result = actor_node(state, telemetry, repo_path)

    # Critic phase
    critic_result = critic_node(state, telemetry, repo_path)

    # Test running
    # ... more legacy code ...
```

**REPLACE WITH** (exactly as provided):

```python
# NEW CLEAN IMPLEMENTATION:

# 1. Run initial tests to identify failures
console.print("[cyan]Running pytest to identify failing tests...[/cyan]")
runner = TestRunner(repo_path, verbose=verbose)
failing_tests, initial_junit_xml = runner.run_tests(max_failures=5)

if initial_junit_xml:
    telemetry.save_test_report(0, initial_junit_xml, report_type="junit")
state.add_failing_tests(failing_tests)

# Exit if no failures
if not failing_tests:
    console.print("[green]✅ No failing tests found! Repository is already green.[/green]")
    state.final_status = "success"
    telemetry.log_event("completion", {"status": "no_failures"})
    telemetry.end_run(success=True)
    return

# 2. Display failing tests
console.print(f"\n[bold red]Found {len(failing_tests)} failing test(s):[/bold red]")
table = Table(title="Failing Tests", show_header=True, header_style="bold magenta")
table.add_column("Test", style="cyan")
table.add_column("Error", style="red")
for test in failing_tests[:10]:
    test_name = getattr(test, "name", str(test))
    error_msg = getattr(test, "short_traceback", "Unknown error").splitlines()[0]
    table.add_row(test_name, error_msg)
if len(failing_tests) > 10:
    table.add_row("...", f"... and {len(failing_tests)-10} more")
console.print(table)

# Prepare context
failures_summary = runner.format_failures_table(failing_tests)
error_details = "\n\n".join(test.short_traceback for test in failing_tests[:3])
code_snippets = ""  # Optional

# 3. Initialize and run Deep Agent (THIS IS THE KEY CHANGE)
console.print("\n[bold]Initializing Nova Deep Agent...[/bold]")
deep_agent = NovaDeepAgent(
    state=state,
    telemetry=telemetry,
    git_manager=git_manager,
    verbose=verbose,
    safety_config=safety_conf  # if configured
)

console.print("[cyan]🤖 Running Deep Agent to fix failing tests...[/cyan]")
success = deep_agent.run(
    failures_summary=failures_summary,
    error_details=error_details,
    code_snippets=code_snippets
)

# 4. Handle completion
if success:
    console.print("\n[green bold]✅ SUCCESS - All tests fixed![/green bold]")
    state.final_status = "success"
else:
    console.print("\n[red bold]❌ FAILED - Some tests could not be fixed.[/red bold]")
    if state.final_status == "max_iters":
        console.print(f"[yellow]Reached maximum iterations ({state.max_iterations}).[/yellow]")
    elif state.final_status == "error":
        console.print("[yellow]Agent encountered an error during execution.[/yellow]")

telemetry.log_event("completion", {
    "status": state.final_status,
    "iterations": state.current_iteration,
    "total_patches": len(state.patches_applied),
    "final_failures": state.total_failures
})
```

### Day 2: Remove Legacy Code

**Files to DELETE entirely:**

- `src/nova/cli_enhanced.py`
- `src/nova/cli_backup.py`
- `src/nova/cli_integration.py`
- `src/nova/cli_migration_helper.py`

**Files to ARCHIVE (move to `archive/legacy/`):**

- `src/nova/agent/llm_agent.py`
- `src/nova/nodes/planner.py`
- `src/nova/nodes/actor.py`
- `src/nova/nodes/critic.py` (unless used by Deep Agent)

### Day 3: Update Deep Agent

Ensure `NovaDeepAgent` has the correct `run()` signature:

```python
class NovaDeepAgent:
    def run(
        self,
        failures_summary: str,
        error_details: str,
        code_snippets: str = ""
    ) -> bool:
        """
        Main entry point for Deep Agent.
        Returns True if all tests pass, False otherwise.
        """
        # Implementation using LangChain tools
        # ...
```

### Day 4: Remove Configuration Complexity

In config files, REMOVE:

- `use_enhanced` flag
- `agent_type` selection
- `basic_mode` options
- Any legacy agent configuration

KEEP only Deep Agent settings:

```yaml
# nova.config.yaml - SIMPLIFIED
model: gpt-4
temperature: 0.0
max_iterations: 5
safety:
  max_patch_lines: 500
  max_affected_files: 5
```

### Day 5: Testing

**Critical Tests:**

```python
def test_deep_agent_is_only_option():
    """Ensure no legacy code paths exist."""
    # Check that LLMAgent is not imported
    # Check that planner/actor/critic nodes are not called
    # Verify only NovaDeepAgent is instantiated

def test_cli_calls_deep_agent():
    """Ensure CLI directly calls Deep Agent."""
    # Mock NovaDeepAgent
    # Run nova fix
    # Assert deep_agent.run() was called exactly once
```

### Day 6: Documentation

Update README.md:

````markdown
## Usage

```bash
nova fix  # Automatically fixes failing tests using AI
```
````

Nova uses an advanced Deep Agent powered by LangChain to analyze
and fix your failing tests. There are no agent options - it always
uses the best available approach.

````

Remove ALL references to:
- Agent selection
- Legacy mode
- Basic vs enhanced
- Multi-step loops

### Day 7: Deploy

1. **Final checklist:**
   - [ ] All legacy code removed
   - [ ] No agent selection options remain
   - [ ] Deep Agent is hardcoded as only path
   - [ ] Tests pass
   - [ ] Documentation updated

2. **Deploy directly to main**
   - No gradual rollout needed
   - No feature flags
   - No compatibility mode

---

## What NOT to Do (Avoiding Over-Engineering)

❌ **DON'T** create an Agent Factory
❌ **DON'T** add --agent flags
❌ **DON'T** maintain backward compatibility
❌ **DON'T** keep legacy code "just in case"
❌ **DON'T** add configuration options for agent selection

---

## Success Criteria

✅ Running `nova fix` ALWAYS uses Deep Agent
✅ No legacy code paths remain in CLI
✅ No user-facing options for agent selection
✅ Clean, simple, maintainable code
✅ All tests passing with new implementation

---

## Emergency Rollback (If Needed)

If critical issues arise, the rollback is simple:
```bash
git revert <commit-hash>  # Revert the change
# Fix the issue in Deep Agent
# Re-apply the consolidation
````

No complex compatibility layers needed - just revert and fix.

---

## Summary

This revised approach is **simpler**, **faster**, and **cleaner** than my original proposal. By removing all options and forcing Deep Agent usage, we:

- Eliminate confusion
- Reduce code complexity
- Improve maintainability
- Accelerate adoption

The key insight from your plan: **Don't give users a choice between good and bad options - just give them the good option.**

---

_Implementation Guide for OS-1035_
_Timeline: 1 week_
_Approach: Direct replacement, no migration period_
