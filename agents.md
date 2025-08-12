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

---

## Open SWE Playbook (Daytona sandbox < 60s)

Goal: make a brand-new Daytona Ubuntu sandbox usable in <60s and keep runs stable.
Assumptions: running as root in a fresh container (no sudo). Network may be locked down; CA store may need updating.
Heuristics: prefer safety, idempotency, and short feedback loops. If a step fails, explain and fallback, don’t stall.

### Quick rules
- **Detect → Decide → Do**: detect package manager, languages, repo type before running tools.
- **Idempotent always**: stamp completion and skip next time.
- **Fail soft**: on primary path failure (e.g., GitHub TLS), provide a working fallback (local patch file).
- **Least moving parts**: don’t install runtimes unless the repo needs them.
- **Explain**: print a ≤1‑line reason per action.

### 0) Environment bootstrap (required once)
When to run: if any of `git`, `tree`, `rg`, or `curl` is missing, or `/opt/.open-swe/bootstrap.done` doesn’t exist.

<!-- AGENT:BOOTSTRAP:BEGIN -->
```bash
set -e

STAMP=/opt/.open-swe/bootstrap.done
[ -f "$STAMP" ] && { echo "[bootstrap] already complete"; exit 0; }

export DEBIAN_FRONTEND=noninteractive

pm=""
command -v apt-get >/dev/null 2>&1 && pm="apt"
command -v dnf     >/dev/null 2>&1 && pm="dnf"
command -v apk     >/dev/null 2>&1 && pm="apk"

echo "[bootstrap] pkgmgr=${pm:-none}"

case "$pm" in
  apt)
    apt-get update -y -o Acquire::Retries=3
    apt-get install -y git tree ripgrep ca-certificates curl unzip tar nano less openssh-client xauth publicsuffix
    update-ca-certificates || true
    ;;
  dnf)
    dnf install -y git tree ripgrep ca-certificates curl unzip tar nano less openssh-clients xorg-x11-xauth libpsl
    update-ca-trust || true
    ;;
  apk)
    apk add --no-cache git tree ripgrep ca-certificates curl unzip tar nano less openssh-client xauth libpsl
    update-ca-certificates || true
    ;;
  *)
    echo "[bootstrap] no supported package manager found"; exit 0
    ;;
 esac

# Git TLS sanity
git config --global http.sslCAInfo /etc/ssl/certs/ca-certificates.crt || true
git config --global init.defaultBranch main || true

mkdir -p "$(dirname "$STAMP")" && touch "$STAMP"

echo "[bootstrap] versions:"
( git --version || true ) && ( tree --version || true ) && ( rg --version || true ) && ( curl --version | head -n1 || true )
```
<!-- AGENT:BOOTSTRAP:END -->

### 1) Repo discovery & safe tree printing
When to run: at start of every session.

<!-- AGENT:DISCOVER:BEGIN -->
```bash
set -e

# Workspace root
ROOT="${WORKSPACE:-/home/daytona/os}"
[ -d "$ROOT" ] || ROOT="$(pwd)"

cd "$ROOT"

# Tree printing that works with/without git
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git ls-files | (command -v tree >/dev/null 2>&1 && tree --fromfile -L 3 || xargs -I{} sh -lc 'printf "%s
" "{}"') || true
else
  (command -v tree >/dev/null 2>&1 && tree -L 3) || find . -maxdepth 3 -type f | sed 's|^\./||' | head -n 500
fi

# Language probes (fast, no network)
LANGS=""
[ -f "package.json" ] && LANGS="${LANGS} node"
( ls -1 **/*requirements*.txt **/pyproject.toml 2>/dev/null | head -n1 >/dev/null ) && LANGS="${LANGS} python"
( ls -1 **/go.mod 2>/dev/null | head -n1 >/dev/null ) && LANGS="${LANGS} go"

echo "[discover] langs:${LANGS:- none}"
```
<!-- AGENT:DISCOVER:END -->

### 2) Language toolchain on‑demand (only if needed)

Node (npm/yarn/pnpm)

<!-- AGENT:LANG-NODE:BEGIN -->
```bash
set -e
[ -f package.json ] || exit 0

# Choose package manager
PM="npm"
[ -f pnpm-lock.yaml ] && PM="pnpm"
[ -f yarn.lock ] && PM="yarn"

# Install runtime only if node missing
if ! command -v node >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs
  elif command -v dnf >/dev/null 2>&1; then
    curl -fsSL https://rpm.nodesource.com/setup_20.x | bash - && dnf install -y nodejs
  elif command -v apk >/dev/null 2>&1; then
    apk add --no-cache nodejs-current npm
  fi
fi

# Ensure chosen PM exists
[ "$PM" = "pnpm" ] && command -v pnpm >/dev/null 2>&1 || npm i -g pnpm@9 >/dev/null 2>&1 || true
[ "$PM" = "yarn" ] && command -v yarn >/dev/null 2>&1 || npm i -g yarn@1 >/dev/null 2>&1 || true

echo "[node] installing deps via $PM"
case "$PM" in
  pnpm) pnpm i --frozen-lockfile || pnpm i ;;
  yarn) yarn install --frozen-lockfile || yarn install ;;
  npm)  npm ci || npm i ;;
 esac
```
<!-- AGENT:LANG-NODE:END -->

Python

<!-- AGENT:LANG-PY:BEGIN -->
```bash
set -e
REQ=""
REQ=$(ls -1 **/*requirements*.txt 2>/dev/null | head -n1 || true)
PYPROJ=$(ls -1 **/pyproject.toml 2>/dev/null | head -n1 || true)
[ -z "$REQ$PYPROJ" ] && exit 0

# Install python if missing
command -v python3 >/dev/null 2>&1 || {
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update -y && apt-get install -y python3 python3-pip
  elif command -v dnf >/dev/null 2>&1; then
    dnf install -y python3 python3-pip
  elif command -v apk >/dev/null 2>&1; then
    apk add --no-cache python3 py3-pip
  fi
}

python3 -m pip install --upgrade pip setuptools wheel || true
[ -n "$REQ" ] && python3 -m pip install -r "$REQ" || true
[ -n "$PYPROJ" ] && ( python3 -m pip install . || python3 -m pip install -e . ) || true
```
<!-- AGENT:LANG-PY:END -->

### 3) App-specific quick fixes (Hono static files, if present)
Condition: TypeScript project with Hono and `src/routes/app.ts` exists; no static middleware is set up.

<!-- AGENT:FIX-HONO-STATIC:BEGIN -->
```bash
set -e
APP=src/routes/app.ts
[ -f "$APP" ] || exit 0
grep -q "from 'hono/serve-static'" "$APP" && exit 0

# Add static middleware for /public
tmp="$(mktemp)"
cat > "$tmp" <<'TS'
import { serveStatic } from 'hono/serve-static'

/* __OPEN_SWE_STATIC_START__ */
app.use('/public/*', serveStatic({ root: './' }))
/* __OPEN_SWE_STATIC_END__ */
TS

# Insert after app creation line
perl -0777 -pe '
  BEGIN{undef $/;}
  s/(const\s+app\s*=\s*new\s+Hono\(\s*\)\s*;)/$1
import { serveStatic } from '''hono\/serve-static''';
app.use('''\/public\/*''' , serveStatic({ root: '''\.\/''' }));/s;
' -i "$APP" || {
  # fallback: append at end
  echo -e "
$(cat "$tmp")" >> "$APP"
}
rm -f "$tmp"
echo "[hono] static middleware enabled at /public/*"
```
<!-- AGENT:FIX-HONO-STATIC:END -->

### 4) Dev server runner (detect cmd)
<!-- AGENT:RUN-DEV:BEGIN -->
```bash
set -e
CMD=""
# Detect common scripts
if [ -f package.json ]; then
  if jq -e '.scripts.dev' package.json >/dev/null 2>&1; then
    if command -v pnpm >/dev/null 2>&1; then CMD="pnpm dev"
    elif command -v yarn >/dev/null 2>&1; then CMD="yarn dev"
    else CMD="npm run dev"; fi
  fi
fi
[ -z "$CMD" ] && exit 0
echo "[dev] running: $CMD"
$CMD
```
<!-- AGENT:RUN-DEV:END -->

### 5) Tests / lint (quick feedback)
<!-- AGENT:TEST-LINT:BEGIN -->
```bash
set -e
RUN=""
if [ -f package.json ] && jq -e '.scripts.test' package.json >/dev/null 2>&1; then
  if command -v pnpm >/dev/null 2>&1; then RUN="pnpm test --silent || true"
  elif command -v yarn >/dev/null 2>&1; then RUN="yarn test || true"
  else RUN="npm test || true"; fi
elif [ -n "$(ls -1 **/pytest.ini **/pyproject.toml 2>/dev/null | head -n1)" ]; then
  RUN="pytest -q || true"
fi
[ -z "$RUN" ] && exit 0
echo "[ci] $RUN"
sh -lc "$RUN"
```
<!-- AGENT:TEST-LINT:END -->

### 6) Git hygiene, commits, and safe push fallback
When to run: before the first commit in a fresh sandbox.

<!-- AGENT:GIT-HYGIENE:BEGIN -->
```bash
set -e
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

# Identity (use placeholders if not set)
git config user.name  >/dev/null 2>&1 || git config user.name  "open-swe-bot"
git config user.email >/dev/null 2>&1 || git config user.email "open-swe-bot@example.com"

# Branch naming (use thread id if present)
BR="${OPEN_SWE_BRANCH:-open-swe/$(date +%s)}"
git rev-parse --verify "$BR" >/dev/null 2>&1 || git checkout -b "$BR"

# Commit if diff exists
git add -A
git diff --cached --quiet || git commit -m "Open SWE automated changes"

# Try push; if TLS fails, write a patch for manual upload
set +e
git push -u origin "$BR"
st=$?
set -e
if [ $st -ne 0 ]; then
  echo "[git] push failed; exporting patch to ./open-swe-changes.patch"
  git format-patch --stdout origin/main..HEAD > open-swe-changes.patch || git diff origin/main..HEAD > open-swe-changes.patch || true
fi
```
<!-- AGENT:GIT-HYGIENE:END -->

### 7) Diagnostics (run when things look weird)
<!-- AGENT:DIAGNOSE:BEGIN -->
```bash
set -e
echo "[diag] uname: $(uname -a)"
echo "[diag] whoami: $(whoami)"
echo "[diag] pm: $(command -v apt-get >/dev/null 2>&1 && echo apt || (command -v dnf >/dev/null 2>&1 && echo dnf) || (command -v apk >/dev/null 2>&1 && echo apk) || echo none)"
echo "[diag] tools:"
for t in git tree rg curl node npm pnpm yarn python3 pip; do
  printf " - %-8s : " "$t"; (command -v "$t" >/dev/null 2>&1 && "$t" --version 2>/dev/null | head -n1) || echo "missing"
 done
echo "[diag] certs:"
ls -l /etc/ssl/certs/ca-certificates.crt 2>/dev/null || true
```
<!-- AGENT:DIAGNOSE:END -->

### Minimal run order the agent should follow
1. AGENT:BOOTSTRAP
2. AGENT:DISCOVER
3. AGENT:LANG-NODE and/or AGENT:LANG-PY (depending on discovery)
4. (Optional) AGENT:FIX-HONO-STATIC if the app matches
5. AGENT:RUN-DEV (or skip for non‑web repos)
6. AGENT:TEST-LINT
7. AGENT:GIT-HYGIENE
8. If errors: AGENT:DIAGNOSE

### Notes for the human
- Volumes vs Snapshots: persistent Volume keeps tools between restarts; Snapshots define the base image. To avoid baking, attach a Volume.
- GitHub TLS x509: if pushes fail from the Open SWE server (not the sandbox), use the patch written (`open-swe-changes.patch`) or configure CA on the host.
- Full automation: you can add a tiny hook to parse and execute the `<!-- AGENT:…:BEGIN/END -->` blocks on first contact.

---

## Appendix — Additional Docs pack
We also recommend adding the following files under `docs/`:

- `ARCHITECTURE.md`
- `ORGSPEC.reference.md`
- `SANDBOX-BOOTSTRAP.md`
- `EVIDENCE.md`
- `OPERATIONS-RUNBOOK.md`
- `OPEN_SWE_KICKOFF.md`

Placeholders have been created below. Replace with your org’s specifics.

---

## Agent System Architecture and Guidelines

### Overview of the Planner–Programmer Architecture

Our LLM agent system follows a Planner–Programmer (Executor) architecture. This separates task planning from task execution to improve efficiency, cost, and reliability.

- **Planner Agent**: analyzes the user request and produces a structured multi‑step plan.
- **Programmer (Executor) Agent**: executes plan steps using tools or procedural code.
- **Tool Layer**: functional tools/APIs invoked by the Programmer.

This enables coherent long‑term reasoning with fewer LLM calls and faster, cheaper runs than naive step‑by‑step agents.

### Agent Roles and Responsibilities

#### Planner Agent
- Inputs: user goal, context, available tools, constraints.
- Output: structured, atomic steps with tool suggestions and inputs.
- Supports re‑planning when execution encounters blockers.

Example plan output:

```text
Plan:
1. Search for "teams in Super Bowl 2025" using the Search tool.
2. For each team found, use the Wiki tool to find the name of the quarterback.
3. Use the Stats API tool to get the season statistics for each quarterback.
4. Compile a summary of the quarterbacks' stats and return to the user.
```

#### Programmer (Executor) Agent
Executes each plan step deterministically:
1) parse step, 2) prepare inputs, 3) invoke tool, 4) capture result, 5) validate, 6) log progress.
- Retries transient failures with backoff; triggers re‑plan on hard failures.
- Produces final answer (optionally via a Responder step) from intermediate results.

Behavior notes:
- Executes in order; safe‑guards for forbidden actions; optional micro‑LLM calls for small transforms.

#### Tool Layer
- Standard interface: name, description, input spec, output spec, execution, error handling.
- Used by Planner in plans; invoked by Programmer with validation/sanitization.

### Guidelines for Adding New Tools
1. Define interface (clear function, typed inputs/outputs, docstring).
2. Register in tool registry with name + description; load config via env.
3. Validate I/O; wrap external calls with try/except and timeouts.
4. Safety: avoid logging secrets; guard risky ops.
5. Document in this file; update prompts if tools list isn’t auto‑generated.
6. Tests: unit tests for normal/edge/error paths; integration test via fake plan.

Example skeleton:
```python
def translate_text(text: str, target_lang: str) -> str:
    """Translate text using provider X."""
    # ...
    return translated_text
```

### Logging and Tracing (LangSmith)
- Trace Planner runs, tool calls, Programmer loop, and finalization.
- Tagging: `planner`, `executor`, `tool:<Name>`, environment, session/user.
- Separate projects per env if desired (e.g., AgentSystem‑Prod/Dev).
- Mask sensitive data; consider sampling in prod.

Example trace URL shape (for reference):
```
https://smith.langchain.com/o/<Org>/projects/<Project>/runs/<RUN_ID>
```

### Error Handling and Retry
- Tool errors: retries with exponential backoff for transient issues; log and propagate on hard errors.
- LLM errors: retry/timeouts; format‑validation with corrective prompts; fallback models if needed.
- Re‑planning: single re‑plan pass on critical failure; cap loops.
- Safe mode: partial results or graceful abort; never unsafe actions.
- Timeouts on all external calls; errors are tagged in traces.

### Modularity, Testing, and Best Practices
- Keep Planner, Programmer, Tools modular with clear interfaces and typed data structures.
- Unit tests: planner (stub LLM), tools (mock I/O), programmer (fake plan/tools).
- Integration tests: end‑to‑end scenarios with cheaper models; tracing enabled.
- Treat trace coverage as part of “done”.

Best‑practice highlights:
- Separate prompts from logic; document assumptions; consistent naming.
- No hard‑coded one‑offs; mind latency/cost; add caching only after correctness.
- Coordinate format changes between Planner and Programmer.

### Appendix: Example Scenario
User: “Average high temperature in Paris last week, answer in French.”
- Plan: WeatherAPI → Calculator → Translate → Respond.
- Execution: call each tool, store results, compose final answer.
- Trace: top run + planner run + tool runs (`tool:WeatherAPI`, `tool:Calculator`, `tool:Translate`).

