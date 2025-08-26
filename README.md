# Nova CI‑Rescue

[![Install Nova CI‑Rescue](https://img.shields.io/badge/Install-GitHub%20App-blue?logo=github)](https://github.com/apps/nova-ci-rescue/installations/new)
[![Add to Slack (beta)](https://img.shields.io/badge/Add%20to%20Slack-beta-4A154B?logo=slack&logoColor=white)](#slack-integration-beta)

Nova keeps your main branch green by automatically fixing failing tests in pull requests. When CI fails, Nova analyzes the failures, proposes focused edits, and opens a reviewable PR with patches and artifacts.

### Why Nova CI‑Rescue

- Patch- or whole-file apply modes with a Planner → Actor → Critic loop
- Runs your test suite, focuses on failures, and iterates up to a limit
- Saves artifacts (patches, test reports) for auditability when enabled
- Guardrails for timeouts, iteration caps, rate limiting, and domain allow-list
- One command to try it locally on a demo repo

Quick links: [Quickstart](docs/QUICKSTART.md) · [Troubleshooting & FAQ](docs/TROUBLESHOOTING.md) · [Privacy](docs/PRIVACY.md)

### Quickstart (one command)

```bash
pip install -e . && export OPENAI_API_KEY=sk-... && nova fix examples/demos/demo_broken_project
```

Notes:

- Requires Python 3.10+ and an OpenAI API key in your environment. Anthropic works too: set `ANTHROPIC_API_KEY` and `NOVA_DEFAULT_LLM_MODEL=claude-3-5-sonnet`.
- The demo repo `examples/demos/demo_broken_project` has failing tests; Nova will create a fix branch and attempt to make them pass.

### Installation

See the dedicated guide: [docs/INSTALLATION.md](docs/INSTALLATION.md)

### Usage

```bash
# Fix a repository (creates a temporary branch and proposes patches)
nova fix /path/to/repo \
  --max-iters 5 \
  --timeout 300 \
  --whole-file    # optional: swap to whole-file replacement mode
```

Other commands:

- `nova version` — print the installed version
- `nova eval` — reserved for multi-repo benchmarking (currently a stub)

### Configuration

Environment variables control runtime behavior (timeouts, LLM model, telemetry, etc). See the full reference and `.env` example: [docs/CONFIGURATION.md](docs/CONFIGURATION.md)

Minimal `.env` example:

```bash
OPENAI_API_KEY=sk-...
# Or use Anthropic
# ANTHROPIC_API_KEY=...
# NOVA_DEFAULT_LLM_MODEL=claude-3-5-sonnet

# Optional telemetry (disabled by default). Set to true to save patches/reports.
NOVA_ENABLE_TELEMETRY=true
```

### Safety limits (defaults)

- Global timeout: 300s per run
- Max iterations: 5
- Test execution timeout: 120s
- Per-repo run frequency cap: 600s between runs
- LLM call timeout: 60s; daily usage warnings enabled

### Contributing and Community

- Contribution guidelines: [CONTRIBUTING.md](CONTRIBUTING.md)
- Code of Conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

### License

MIT — see [LICENSE](LICENSE).

---

### Slack integration (beta)

Slack notifications are currently in private beta. If you’re interested, open an issue or contact us and we’ll add you to the waitlist. The button above is a placeholder until the public app is available.
