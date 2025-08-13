# Nova CI-Rescue — Milestone Board

## Live Linear View

[Open in Linear – Happy Path by Milestone](https://linear.app/nova-solve/project/ci-rescue-v10-happy-path-536aaf0d73d7)

## Milestone Summary

| Milestone                       | Key Deliverables                                       | Status      |
| ------------------------------- | ------------------------------------------------------ | ----------- |
| **A. Local E2E**                | CLI seeded failing tests → green on sample repo        | In Progress |
| **B. Quiet CI & Telemetry**     | Quiet pytest logs, telemetry wiring, packaging cleanup | Not Started |
| **C. GitHub Action & PR Proof** | Action simulate job, Scorecard PR comment, safety caps | Not Started |
| **D. Demo & Release**           | Eval polish, starter demo repo, proof checklist        | Not Started |

## Issue Breakdown - Happy Path (Must-Have)

### Milestone A: Local E2E (Happy Path)

- **OS-832** - A1 — Seed failing tests into Planner _(agent, backend, must-have)_ - 2h
  - AC: If zero failures → exit 0 with "No failing tests"; planner prompt contains failing tests table
- **OS-833** - A2 — Branch & revert safety _(cli, must-have)_ - 1h
  - AC: Aborted run leaves clean working tree; success prints branch name
- **OS-834** - A3 — Apply/commit loop _(backend, must-have)_ - 2h
  - AC: Post-run branch shows ≥1 commits; files match patch contents
- **OS-835** - A4 — Global timeout & max-iters _(backend, must-have)_ - 1h
  - AC: Exiting early prints reason clearly; process exits >0
- **OS-836** - A5 — Smoke run on sample repo _(must-have, testing)_ - 0.5d
  - AC: Tests pass (green) in the end; `.nova/<run>/` contains trace, diffs, and JUnit report

### Milestone B: Quiet CI & Telemetry

- **OS-837** - B1 — Quiet pytest defaults _(ci, must-have, testing)_ - 30m
  - AC: Local test output <5KB on pass / <50KB on fail; CI uses the same settings
- **OS-838** - B2 — Node-level telemetry + artifacts _(must-have, observability)_ - 0.5d
  - AC: `.nova/<run>/trace.jsonl` reconstructs full loop; per-step artifacts present
- **OS-839** - B3 — Packaging cleanup _(must-have, packaging)_ - 1h
  - AC: Fresh venv `pip install -e .` yields working `nova` CLI without errors
- **OS-840** - B4 — README Quickstart _(docs, must-have)_ - 2h
  - AC: New user gets green run locally in ≤15 minutes

### Milestone C: GitHub Action & PR Proof

- **OS-841** - C1 — GitHub Action: simulate job _(ci, must-have)_ - 0.5d
  - AC: Action succeeds on demo repo with downloadable artifacts
- **OS-842** - C2 — Scorecard check-run + PR comment _(ci, must-have, ux)_ - 0.5d
  - AC: PR shows "CI-Auto-Rescue" check with pass status and metrics
- **OS-843** - C3 — Safety caps _(must-have, safety)_ - 2h
  - AC: Violations abort with friendly message explaining why

### Milestone D: Demo & Release (Nice-to-Have)

- **OS-844** - D1 — nova eval polish _(eval, nice-to-have)_ - 0.5d
- **OS-845** - D2 — Starter demo repo _(demo, growth, nice-to-have)_ - 0.5d
- **OS-846** - D3 — Proof thread checklist _(growth, nice-to-have)_ - 1h
- **OS-847** - Update Slite with Complete Happy Path Documentation _(docs)_ - High priority
