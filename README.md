# 🧑‍🔧 Nova CI-Rescue

**Self-healing CI for Python — open source**

[![PyPI](https://img.shields.io/pypi/v/nova-ci-rescue)](https://pypi.org/project/nova-ci-rescue/)
[![CI](https://github.com/novasolve/ci-auto-rescue/actions/workflows/tests.yml/badge.svg)](https://github.com/novasolve/ci-auto-rescue/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/pypi/pyversions/nova-ci-rescue)
[![Coverage Status](https://codecov.io/gh/novasolve/ci-auto-rescue/branch/main/graph/badge.svg)](https://codecov.io/gh/novasolve/ci-auto-rescue)
![PyPI - Downloads](https://img.shields.io/pypi/dm/nova-ci-rescue)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://pre-commit.com/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Nova CI-Rescue automatically fixes failing Python tests with an AI-powered agent loop.
Instead of red CI builds, Nova analyzes failures, proposes patches, and opens a PR with passing tests — all audit-ready.

👉 [Demo video](#) · [Docs](docs/) · [Contributing](CONTRIBUTING.md)

## ✨ Why Nova?

🔄 **Self-healing CI** — automatically repair failing pull requests

🧠 **LLM agent loop** — Planner → Generate → Patch → Critic

⚡ **Runs anywhere** — local CLI or GitHub Actions

📜 **Audit-friendly** — artifacts, reports, and patch history

🔧 **Flexible** — OpenAI GPT-4, Anthropic Claude, or bring your own model

## 🚀 Quickstart (60 seconds)

```bash
pip install -e .
export OPENAI_API_KEY=sk-...
nova fix examples/demos/demo_broken_project
```

✅ **Nova will:**

- Create a new branch
- Attempt targeted fixes
- Push a reviewable PR with test results

Requires Python 3.10+.
Supports OpenAI and Anthropic models (`NOVA_DEFAULT_LLM_MODEL=claude-3-5-sonnet`).

## ⚡ Usage

```bash
# Fix a repository
nova fix /path/to/repo \
  --max-iters 5 \
  --timeout 300 \
  --whole-file    # optional: replace entire files
```

**Other commands:**

- `nova version` — print installed version
- `nova eval` — benchmarking (stub)

## 🔧 Configuration

Environment variables control runtime behavior.

**Minimal .env:**

```bash
OPENAI_API_KEY=sk-...
# or:
# ANTHROPIC_API_KEY=...
# NOVA_DEFAULT_LLM_MODEL=claude-3-5-sonnet

# Optional telemetry
NOVA_ENABLE_TELEMETRY=true
```

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for full reference.

## 🛡 Safety Limits

- **Global timeout:** 300s per run
- **Max iterations:** 5
- **Test execution timeout:** 120s
- **Run frequency cap:** 600s per repo
- **LLM call timeout:** 60s

## 🤝 Contributing

- [Contribution guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)

We welcome issues, PRs, and feedback!

## 📜 License

MIT — see [LICENSE](LICENSE).

## 💬 Slack Integration (Beta)

Get CI fix notifications in Slack (private beta).
Open an issue to join the waitlist.

## 📚 Resources

- [Demo video](#)
- [Quickstart guide](docs/QUICKSTART.md)
- [Troubleshooting & FAQ](docs/TROUBLESHOOTING.md)
- [Privacy](docs/PRIVACY.md)

---

✨ **Nova is your AI teammate that keeps CI green — so you can ship faster.**
