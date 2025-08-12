# CI Auto‑Rescue — Agents Spec + Bootstrap

> Zero‑downtime CI recovery. These agents detect, diagnose, and automatically rescue failing pipelines while keeping humans in the loop.

---

## Why this exists
When CI breaks, product velocity stalls. CI Auto‑Rescue gives you an always‑on incident crew that:
- Detects failures within seconds
- Reproduces flake vs. real breakage
- Applies safe, reversible fixes (retry, quarantine, pin, revert) via PRs
- Notifies the right owners with crisp context

---

## Agent constellation

- **IncidentSentinel**: Subscribes to GitHub Actions webhooks and Checks API. Collates failing jobs, classifies severity (blocker, flaky, transient), opens/updates incidents.
- **LogWhisperer**: Downloads and parses job logs/artifacts. Redacts secrets, extracts failing test signatures, top error frames, exit codes, and heuristics.
- **FlakeHunter**: Cross-references historical runs to score flakiness, tags tests/files, proposes quarantine with expiry.
- **DependencyDoctor**: Detects dependency breakage (new releases, lockfile drift, resolver conflicts). Proposes pin/rollback.
- **Reproducer**: Generates a minimal repro (container/`act` recipe or `pytest -k` shard). Attaches script as artifact and to PR comment.
- **FixProposer**: Chooses the safest remedy policy:
  - Retry with backoff
  - Auto-retry only impacted matrix cells
  - Quarantine test behind label/skip marker with TTL
  - Pin offending dependency
  - Revert the breaking commit
  - Open tracking issue with owner assignment
- **Backporter**: After main is green, backports fix to protected branches using cherry-pick PRs.
- **Notifier**: Posts updates to Slack/Teams/email with a one‑screen status: incident link, root cause hypothesis, owner, ETA.

---

## Event flow
1. Workflow run fails → webhook → `IncidentSentinel` creates/updates incident.
2. `LogWhisperer` parses artifacts and builds a failure fingerprint.
3. `FlakeHunter` queries history → flake score.
4. Policy engine selects remedy → `FixProposer` acts (PR / retry / quarantine / pin / revert).
5. `Notifier` updates channels; `Backporter` follows up once green.

---

## Labels and taxonomy
- `ci:auto-rescue` — managed by this system
- `ci:flake` — suspected flaky failure
- `ci:quarantined` — test temporarily skipped with TTL
- `ci:dep-pin` — dependency pinned pending upstream fix
- `ci:revert` — automated revert PR

---

## Minimal policy (safe-by-default)
- Only auto‑merge when change is strictly reversible (retry, label, quarantine with TTL).
- Code edits (pin/revert) always go through PR + review unless repository policy allows `auto-approve` for bots.
- Never touch protected branches directly.

---

## Quick Bootstrap
Follow these steps to get a working baseline in minutes. Adjust to your org’s naming.

### 1) Prerequisites
- GitHub App or PAT with `repo`, `checks:read`, `actions:read`, `pull_requests:write` scopes
- GitHub CLI (`gh >= 2.40`)
- Optional: Slack bot token for notifications

### 2) Create repository secrets (recommended names)
```bash
# Replace with your actual values
gh secret set CI_RESCUE_GITHUB_TOKEN --body "$GH_TOKEN"
# Optional Slack
gh secret set CI_RESCUE_SLACK_BOT_TOKEN --body "$SLACK_BOT_TOKEN"
```

### 3) Install the action/workflow trigger
Create `.github/workflows/ci-auto-rescue.yml` in each target repo:
```yaml
name: CI Auto‑Rescue
on:
  workflow_run:
    workflows: ["CI", "Test", "Build"]
    types: ["completed"]
permissions:
  contents: read
  checks: read
  actions: read
  pull-requests: write
  issues: write
jobs:
  rescue:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Auto‑Rescue
        uses: novasolve/ci-auto-rescue@main
        with:
          token: ${{ secrets.CI_RESCUE_GITHUB_TOKEN }}
          slack-token: ${{ secrets.CI_RESCUE_SLACK_BOT_TOKEN }}
          quarantine-ttl-days: 7
          retry-max: 2
```

### 4) Local dev quickstart
```bash
# One‑liner bootstrap for contributors
make bootstrap || bash -lc '
  python3 -m venv .venv && source .venv/bin/activate && \
  pip install -U pip && pip install -r requirements.txt 2>/dev/null || true && \
  echo "Dev ready"'
```

---

## Suggested repo layout (for the action/agent implementation)
```
ci-auto-rescue/
├─ action.yml                 # composite/action entrypoint (if distributed as action)
├─ src/
│  ├─ sentinel/               # webhooks, checks api polling
│  ├─ logs/                   # parsers, redactors, fingerprinting
│  ├─ policies/               # retry/quarantine/pin/revert strategies
│  ├─ fixes/                  # PR builders, patch generators, backporter
│  └─ notify/                 # Slack/Teams/email
├─ rules/
│  ├─ defaults.yaml           # org‑wide sane defaults
│  └─ overrides/              # per‑repo overrides
├─ tests/
└─ README.md
```

---

## Policy examples
- **Flaky pytest**: add `@pytest.mark.flaky` or `-k` retry; open issue; TTL 7 days.
- **Tooling timeouts**: retry matrix cell; escalate after 2 failures.
- **New dependency release breaks build**: pin to last known good version; open upstream issue link.
- **Secrets missing**: fail fast with clear owner; do not auto‑retry.

---

## Slack messages (compact status)
- Title: "CI Auto‑Rescue: <repo>@<sha> failed — <policy> applied"
- Fields: culprit job, failure summary, remedy, link to PR/incident, next steps

---

## Observability
- Emit events to GitHub Checks annotations and an optional `rescue.log` artifact.
- Suggested metrics: mean‑time‑to‑green, retry success rate, flake rate per suite, auto‑fix PR merge rate.

---

## Security & guardrails
- Read‑only until a remedy is chosen; write privileges are narrowly scoped.
- All changes land via PR from a bot user; never push to protected branches.
- Secrets never leave GitHub; logs are redacted before storage.

---

## Roadmap
- Containerized reproducible runners per job image
- Fine‑grained ownership mapping using CODEOWNERS + historical blame
- Multi‑provider support (GitLab, CircleCI) via adapter layer

---

## Credits
Made with care for teams that ship fast and fix faster.
