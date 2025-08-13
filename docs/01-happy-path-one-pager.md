# Nova CI-Rescue — Happy Path One-Pager

## Goal
Ship Nova CI-Rescue v1.0 Happy Path — autonomously detect and fix seeded CI test failures end-to-end, producing proof artifacts and a GitHub Action demo.

**Success means:**
- `nova fix` turns a seeded failing repo green locally in ≤ 3 iterations.
- GitHub Action workflow runs successfully, uploads `.nova` artifacts, and posts a Scorecard PR comment.
- Quickstart README lets a new user reproduce the run in ≤ 15 minutes.

## Scope

**In Scope (v1.0):**
- Local CLI (`nova fix`, `nova eval`) flow to green.
- Core agent loop (Planner → Actor → Critic → Apply → RunTests → Reflect).
- Tools: pytest runner, patcher, git tool.
- Telemetry with node-level events and artifacts.
- Quiet pytest defaults for readable logs.
- GitHub Action workflow + PR Scorecard comment.
- Safety caps (LOC, file count, denylist).
- Demo repo with seeded failure.

**Out of Scope (v1.0):**
- Handling multiple complex failure types.
- Multi-repo orchestration.
- Advanced model routing or fallback logic.
- Notifications beyond GitHub (e.g. Slack, email).

## Current Status

**Complete:**
- ✅ CLI commands + branch creation/reset logic.
- ✅ Core agent loop and tools integrated.
- ✅ Timeout & iteration cap enforcement.
- ✅ Basic telemetry skeleton.
- ✅ Dry-run smoke test.

**In Progress:**
- 🔄 Seed failing tests into planner prompt (A1).
- 🔄 Telemetry wiring for all nodes (B2).
- 🔄 Quiet pytest defaults (B1).
- 🔄 Packaging cleanup (B3).

**Not Started:**
- ⏸️ GitHub Action simulate job (C1).
- ⏸️ Scorecard PR comment (C2).
- ⏸️ README Quickstart (B4).
- ⏸️ Starter demo repo (D2).

## Blockers / Risks
- GitHub Action permissions for PR comment on demo repo.
- Model determinism on seeded failure fix.
- Plugin availability (pytest-json-report vs. JUnit XML).

## This Week's Plan
- **Mon:** A1–A3 (seed failing tests, branch/revert safety, apply/commit loop) → A5 smoke run.
- **Tue:** B1 (quiet logs), B2 (telemetry wiring), B3 (packaging cleanup).
- **Wed:** C1 (Action simulate job).
- **Thu:** C2 (Scorecard PR comment), B4 (Quickstart doc).
- **Fri:** End-to-end dry run → Demo + publish proof.

## Definition of Done (v1.0)
- ✅ Local `nova fix` turns seeded repo green.
- ✅ GitHub Action passes with artifacts + PR summary.
- ✅ `.nova/<run>/trace.jsonl`, `diffs/`, `reports/` complete.
- ✅ README Quickstart works for new user.
