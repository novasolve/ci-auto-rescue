# Operations Runbook — CI-Rescue

## Before enabling on a repo (checklist)
- [ ] Install GitHub App with least-privilege scopes.
- [ ] Add `.nova/orgspec.yml` (start with template from docs/ORGSPEC.reference.md).
- [ ] Confirm sandbox bootstrap passes (`git/tree/rg/curl/ca-certificates` present).
- [ ] Ensure project has a reproducible env (lockfile or setup script).

## Day-to-day
- Trigger: failing workflow, PR label `nova:fix`, or Action dispatch.
- Nova opens a **Draft PR** with Scorecard; CI re-runs.
- If green and within policy, reviewer merges. If not, see triage below.

## Triage playbook
- **Repro failed**: inspect `sandbox/setup.log`; often missing dependencies. Add/install via repo setup.
- **Flaky test**: Scorecard shows `flake: true`; test is quarantined (label `flaky`). Decide to skip or rewrite.
- **Policy hit**: Scorecard `within_caps=false` → increase `diff_caps` or narrow scope.
- **Budget exceeded**: raise `budgets.cost_usd`/`wall_time_s` or simplify scope; inspect Ledger for long steps.

## Cancel / Retry
- Cancel long runs in UI or via API:
  - `POST /threads/{id}/runs/{run_id}/cancel?action=interrupt`
- Retry after tweaking OrgSpec or adding missing deps.

## Logs & Artifacts
- **Scorecard**: PR check + `artifacts/scorecard.json`
- **Ledger**: `artifacts/ledger.jsonl`
- **Sandbox**: `/var/log/nova/*.log` (ephemeral)

## SLOs & paging (internal)
- O24 < 50% for 2 consecutive days → **incident**; rotate to add new heuristics or tighten policy.
- Revert rate > 5% weekly → freeze auto-apply; require extra reviewer until back under 5%.

## Comms templates
- PR comment (success): “✅ Nova made tests green in {{mins}}m; diff {{lines}} lines. Scorecard attached.”
- PR comment (handoff): “🟨 Repro succeeded but fix exceeded budget. See Ledger; suggested next steps: …”
