# Nova CI-Rescue v1.1 Migration Guide

Nova CI-Rescue v1.1 introduces a new Deep Agent architecture that replaces the legacy multi-step agent from v1.0. This guide summarizes the breaking changes, removals, and how to adapt to the new system.

## Overview of Changes

- **Deep Agent as Default:** The `nova fix` CLI command now uses the LangChain-powered **NovaDeepAgent** by default. This agent encapsulates the entire fix loop internally using tools (planning, file read/write, test run, patch review).
- **Legacy Agent Deprecated:** The old Planner/Actor/Critic pipeline is removed from the default code path. If necessary, you can invoke it using the `--legacy-agent` flag (for this release only). This legacy mode uses the v1.0 LLM-based approach and is meant as a fallback during transition.
- **Unified Tools Integration:** Safety and test execution are now handled by unified tools:
  - `ApplyPatchTool` – Applies patches with safety checks (max lines/files, blocked paths).
  - `RunTestsTool` – Runs tests in an isolated Docker sandbox (or falls back to local runner) and returns structured results.
  - `CriticReviewTool` – Uses an LLM to review a proposed patch and decide on approval.
  These tools are seamlessly used by NovaDeepAgent, replacing the need for separate nodes or manual checks.
- **Removed Modules:** The following legacy modules and classes have been removed or moved to a legacy archive:
  - `nova/agent/llm_agent.py` (Legacy LLM agent class)
  - `nova/agent/mock_llm.py` (Mock agent used in tests/dev)
  - `nova/orchestrator.py` (Orchestration logic now handled by NovaDeepAgent or CLI)
  - `nova/nodes/planner.py`, `nova/nodes/actor.py`, `nova/nodes/critic.py` (Planner/Actor/Critic node implementations)
  - Other helper nodes (e.g., `reflect.py`, deprecated safety checks) that were part of the v1.0 loop.
  > **Note:** These legacy components are no longer invoked by default. The code remains accessible for the `--legacy-agent` mode in v1.1, but will be fully removed in a future release.
- **CLI Interface Changes:** All existing CLI options (`--max-iters`, `--timeout`, etc.) remain the same. A new flag `--legacy-agent` has been added to `nova fix` to explicitly run the old agent. The prior internal flags or toggles used in v1.0 (such as any environment variables to disable critic or alternate paths) are discontinued since there is now a single primary execution path.
- **Behavioral Changes:** In v1.0, each iteration's steps (planning, patching, critic, etc.) were logged separately. In v1.1, the Deep Agent still logs similar events (e.g., patch applied, tests run), but they are managed within the LangChain agent loop. Users will notice fewer console prints about "Planner/Actor/Critic" phases; instead, Nova outputs iteration summaries and relies on the unified tool feedback (e.g., errors from `open_file` or `write_file` are shown directly if the agent tries to violate safety rules).
- **Telemetry Events:** JSONL telemetry now records new event types: `"deep_agent_start"`, `"deep_agent_success"`, `"deep_agent_error"`, etc. The old events for planner/actor/critic (`"planner_start"`, `"actor_complete"`, `"critic_approved"`, etc.) will not appear unless using `--legacy-agent`. If you have any tooling that parses Nova's log output or telemetry, update it to handle the new event names.

## Adapting Your Workflow

**Using NovaDeepAgent in Code:** If you previously used `LLMAgent` or `NovaOrchestrator` in your Python code, switch to `NovaDeepAgent`. For example:
```python
# v1.0 (old way)
# from nova.agent.llm_agent import LLMAgent
# agent = LLMAgent(repo_path=".", model="gpt-4")
# ... (manual loop or orchestrator)

# v1.1 (new way)
from nova.agent.deep_agent import NovaDeepAgent
from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger

state = AgentState(repo_path=".")
telemetry = JSONLLogger()
agent = NovaDeepAgent(state=state, telemetry=telemetry, verbose=True)
success = agent.run(failures_summary="...", error_details="...", code_snippets="")
```

The `NovaDeepAgent.run()` method encapsulates the full loop and returns a boolean indicating success. It automatically uses the tools and adheres to safety limits defined in `NovaSettings` or config files.

**Legacy Mode (if needed):** For this release, you can still trigger the old behavior via CLI flag or by calling the legacy functions:
```bash
nova fix . --legacy-agent
```

This will perform the iterative loop using the deprecated code. This is intended for verification or in case of unexpected issues with the new agent. Going forward, the legacy path will be removed, so migrate any custom integrations to use the new Deep Agent.

**Configuration Files:** No changes in format. The same `NovaSettings` fields (like `max_iterations`, `timeout_seconds`, `default_llm_model`) apply. New safety-related fields (if any were introduced for v1.1, e.g., `blocked_paths`, `max_changed_lines/files`) should be documented in the README; ensure your config includes them if you need to override defaults. The Deep Agent reads these settings via `get_settings()` internally.

## Removed and Deprecated APIs

If you have import statements or references to the following, you'll need to update:

- **`nova.orchestrator.NovaOrchestrator`** – Removed. No longer needed; use `NovaDeepAgent` directly via CLI or code.
- **`nova.agent.llm_agent.LLMAgent`** – Removed. (Available internally only for legacy mode.) Replace with `NovaDeepAgent` usage.
- **`nova.nodes.planner_node/actor_node/critic_node`** – Removed. No direct replacements; the Deep Agent handles these steps internally. You can assume the new agent performs planning and critique automatically. If you need to mimic their functionality, consider using the unified tools or the LangChain agent prompt directly.
- **`nova.agent.mock_llm.MockLLMAgent`** – Removed. (This was for testing with a dummy LLM; you may simulate Deep Agent behavior with your own stub if needed.)
- **Telemetry event names for legacy steps** (e.g., `"planner_plan_generated"`) – No longer emitted. Use new event names or parse output differently if automating analysis.

## Testing and Validation

It's highly recommended to test Nova v1.1 on a sample failing repository:

1. Run `nova fix` without flags and observe that it completes using the Deep Agent. All functionality (like applying multiple patches, honoring iteration limits, posting GitHub comments, etc.) should work as before or better.
2. Run `nova fix --legacy-agent` on the same scenario and compare outcomes. The legacy mode should behave as v1.0 did, allowing you to verify that the Deep Agent is producing equivalent or improved results.
3. All existing CLI options (`--max-iters`, `--config`, etc.) continue to work in both modes. The `--legacy-agent` flag can be combined with these options as well.
4. The test suite (if you maintain one for Nova) should be updated to include at least one run in legacy mode to ensure the fallback path remains functional in this release.

## Documentation

Refer to the updated [README](README.md) for details on usage and to the Quickstart Guide for an example of running Nova v1.1. The documentation has been updated to reflect the new one-agent workflow (the previous "Happy Path" with separate nodes is obsolete). If you maintained any internal docs or runbooks referencing the old agent, update them to remove references to Planner/Actor/Critic nodes and instead describe the Deep Agent behavior.

## Summary

Nova CI-Rescue v1.1 simplifies the architecture by consolidating to a single Deep Agent and modern tool-based approach. This yields a more maintainable codebase and sets the stage for future enhancements (v1.2 and beyond). While a compatibility layer (`--legacy-agent`) exists, it's meant as a temporary bridge. Users and developers are encouraged to embrace the new Deep Agent for all use cases moving forward.