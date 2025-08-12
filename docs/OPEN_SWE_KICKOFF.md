# OPEN_SWE_KICKOFF.md — v4.21 Action-First Agent

## One-line spec
Ship a CLI + API that fixes failing tests end-to-end: plan → edit code → run tests → iterate until green, using GP5-Pro + LangGraph, with OpenSWE as the external “muscle” tool. Target: works on 3 public Python repos + 1 internal repo with ≥70% fix-rate on seeded failures in ≤20 min.

## Release gates (must all pass)
- ✅ nova fix runs locally with zero manual edits.
- ✅ Passes 4-repo eval suite (≥70%).
- ✅ README Quickstart (+ 90-sec Loom) ≤5 min setup.
- ✅ Telemetry: JSONL trace + artifacts per run.

## Architecture (simple & composable)
### Control plane (LLM + state)
- Planner (GP5-Pro): reads failing tests, emits ≤5-step plan.
- LangGraph state machine: plan → act → observe → reflect → done.
- Critic (GP5-Pro, small context): safety/fit gate before commit.

### Action plane (tools)
- Code I/O: read files, apply unified diff patch, revert on fail.
- Tests: run pytest, capture stdout/exit, parse JUnit.
- Git: branch, commit, restore; optional PR create.
- Search: local ripgrep; optional web (Tavily/Exa) if allowed.
- OpenSWE Tool: remote call “write/modify function X to satisfy Y”.
- Sandbox: subprocess/Docker runner with time/mem limits.

## Observability
Run log (trace.jsonl), artifacts (diffs, junit.xml, scorecard.json).

## Packaging
- CLI: `nova fix`, `nova eval`.
- SDK: `Agent.run(repo_path, task)`.
- Daytona first-boot (idempotent): install git tree rg curl ca-certificates unzip tar. Language env comes from repo lockfiles.

## 5-day sprint (calendar week)
- Day 1 — Repo & skeleton: Scaffold apps/cli, agent/, tools/, evals/, telemetry/. Wire LangGraph with mock tools; CLI “hello world” runs dry pipeline.
- Day 2 — Core tools: Filesystem read/write + safe patcher; pytest runner; Git ops; tag runs.
- Day 3 — Reason-act loop: Planner → Actor → Tests → Reflect (≤6 iters). Critic gate pre-commit. Persist structured trace.
- Day 4 — OpenSWE + Evals: Add Tool(OpenSWE.call). Seed 10 failures each across 3 OSS + 1 internal repo. `nova eval` computes success/time/cost.
- Day 5 — Hardening + Docs: Kill-switch, budgets, CLI polish, README, Loom. Final eval; prompt tuning; cut 4.21 tag.

## Backlog (P0→P2)
- P0 (ship): A-001..A-013 (state, patch, pytest, git, planner, actor, reflector, critic, OpenSWE adapter, telemetry, CLI, evals, docs)
- P1: streaming console UI; cost/time budgeter; simple PR creator.
- P2: multi-file planning; ripgrep/mypy/ruff+black; Docker runner.

## Wiring (reference shape)
```python
from langgraph.graph import StateGraph, END
class State(TypedDict):
    plan: str; step: int; diffs: list[str]
    test_result: dict; reflections: list[str]; done: bool

def planner(s): ...
def actor(s): ...        # GP5 or OpenSWE → unified diff
def critic(s): ...
def apply_patch(s): ...
def run_tests(s): ...
def reflect(s): ...      # next step or done

g = StateGraph(State)
for n in ["planner","actor","critic","apply_patch","run_tests","reflect"]:
    g.add_node(n, globals()[n])
g.add_edge("planner","actor"); g.add_edge("actor","critic")
g.add_edge("critic","apply_patch"); g.add_edge("apply_patch","run_tests")
g.add_edge("run_tests","reflect")
g.add_conditional_edges("reflect",
    lambda s: END if s["done"] or s["step"]>6 else "actor")
graph = g.compile()
```

## Prompts (concise & durable)
- Planner: “Given failing pytest output + repo tree, output a ≤5-step plan with target files/functions and rationale.”
- Actor: “Propose a unified diff implementing Step N. Respect style; don’t touch unrelated code.”
- Critic: “Validate scope/imports/side-effects. If unsafe, suggest edits or reject.”
- Reflector: “From test deltas, decide: iterate (what next) or stop (why).”

## Guardrails
Max diff lines/files; forbidden paths; never commit creds.

## Ops (keys, allow-list, Daytona)
- Domains: api.openai.com, api.tavily.com, api.exa.ai, github.com, raw.githubusercontent.com, pypi.org, files.pythonhosted.org, huggingface.co, cdn-lfs.huggingface.co, OpenSWE endpoint.
- `.env` via pydantic-settings; no secrets in traces.
- Default-deny network: add only what’s needed.
- Daytona bootstrap one-liner installs base tools (idempotent).

## Evals (make it undeniable)
- Repos: 3 OSS (Python) + 1 internal.
- Seeds: 10 failures each (logic, API drift, flake).
- Metrics: success rate, time-to-green, iterations, tokens, $ cost.
- Command: `nova eval --repos repos.yaml --max-iters 6 --budget 3`.
- Keep best/worst traces for launch thread.

## Deliverables for 4.21 tag
- ✅ `nova fix` + `nova eval` binaries.
- ✅ `docs/README.md` Quickstart (3 cmds) + 90-sec Loom.
- ✅ `telemetry/trace.jsonl` + artifacts/ per run.
- ✅ `docs/CHANGELOG.md` and seeded evals/.
