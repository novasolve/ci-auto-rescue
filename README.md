# Nova CI-Rescue

<!-- Badges: CI | Coverage | PyPI | Python Versions | License | pre-commit | Black | OpenSSF -->
[![CI](https://github.com/novasolve/ci-auto-rescue/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/novasolve/ci-auto-rescue/actions/workflows/ci.yml)
<!-- [![Coverage](https://codecov.io/gh/novasolve/ci-auto-rescue/branch/main/graph/badge.svg)](https://codecov.io/gh/novasolve/nova-ci-rescue) -->
[![PyPI](https://img.shields.io/pypi/v/nova-ci-rescue?label=PyPI)](https://pypi.org/project/nova-ci-rescue/)
![Python Versions](https://img.shields.io/pypi/pyversions/nova-ci-rescue?color=blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://pre-commit.com/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
<!-- [![OpenSSF Best Practices](https://bestpractices.coreinfrastructure.org/projects/8888/badge)](https://bestpractices.coreinfrastructure.org/projects/8888) -->

<!-- Installation -->
[![Install Nova CI‑Rescue](https://img.shields.io/badge/Install-GitHub%20App-blue?logo=github)](https://github.com/apps/nova-ci-rescue/installations/new)
[![Add to Slack (beta)](https://img.shields.io/badge/Add%20to%20Slack-beta-4A154B?logo=slack&logoColor=white)](#slack-integration-beta)

<!-- Demo GIF -->
<!-- ![Nova CI-Rescue Demo](./docs/assets/nova-demo.gif) -->
<!-- TODO: Add 20-sec GIF showing Nova in action: failing test → PR comment → auto-fix PR with artifacts -->

Nova CI-Rescue keeps your main branch green by automatically fixing failing tests in pull requests. When CI fails, Nova uses an LLM (e.g. GPT-4 or Anthropic Claude) to analyze the failures, propose focused code edits, and open a safe, reviewable PR with the patches and logs. It's designed for Python projects (Pytest-based CI) and emphasizes reliability, transparency, and maintainers' control.

## Why Nova CI-Rescue?

**Safe-by-default**: Nova never pushes directly to your branches – it creates a separate fix branch and PR for review. All actions are bounded by guardrails (timeouts, max iterations, rate limits, file allow/deny lists) to prevent runaway changes. By default it focuses on minimal diffs ("patch" mode) rather than wholesale rewrites, unless explicitly allowed.

**Transparent & auditable**: Every auto-fix comes with a detailed diff and explanation. Nova can save all artifacts (patch files, test outputs, LLM reasoning traces) for later audit. Logs are kept in JSONL format for easy search, and output artifacts can be uploaded in CI for maintainers to inspect.

**GitHub-native**: Nova runs as a GitHub Action triggered by your CI workflow or via a GitHub App, requiring only minimal permissions (content and pull request writes). It posts a PR comment or status check to inform you of what it's doing, and integrates into your normal PR review process – no new tools or dashboards to learn.

**Fast to try**: Get started in minutes. You can demo Nova locally with a single command (see below), and enable it in CI by adding one workflow file (copy-paste example provided). No lengthy setup or training phase required.

**Focused CI fixer**: Nova runs your test suite, identifies the failing tests, and iteratively attempts fixes until the tests pass or limits are reached. It doesn't blindly rewrite your code; it pinpoints failures and addresses them one by one. This keeps fixes scoped and relevant to the observed failures.

## How It Works

Nova employs an intelligent loop of Planner → Patch Actor → Critic (inspired by human code review):

**Planner**: The LLM analyzes failing test outputs and devises a plan for what to fix (e.g. which function or logic to change). It focuses only on the tests that failed and their causes.

**Actor**: Following the plan, the LLM suggests a code patch (a unified diff) to implement the fix. Nova applies this patch to a new git branch, without touching your main or PR branch.

**Critic**: Nova then reviews the patch using a second LLM pass. If the patch is judged likely to resolve the issue and not introduce obvious problems, Nova proceeds – otherwise it rejects the patch and feeds the Critic's feedback into the next iteration.

**Test & Iterate**: After an approved patch, Nova runs the test suite again. If tests are still failing, it loops back to the Planner with the Critic's feedback, for up to NOVA_MAX_ITERS attempts (default 5). This loop stops as soon as all tests pass or a safety limit is hit. In the end, Nova opens a pull request with the final patch and attaches logs/artifacts for review. The original failing PR is left unchanged (aside from a non-blocking comment or status) so maintainers retain full control over what gets merged.

## Getting Started

### Quick Demo (Local)

You can try Nova locally on a toy project to see how it works, without any configuration. Just make sure you have Python 3.10+ and an API key:

```bash
pip install nova-ci-rescue && \
export OPENAI_API_KEY=sk-...  && \
git clone https://github.com/novasolve/ci-auto-rescue.git && \
nova fix ci-auto-rescue/examples/demos/demo_broken_project
```

This will install Nova and run it on a small deliberately broken repo (a failing calculator test), creating a fix branch and printing out how Nova analyzes and fixes the tests. You'll see Nova's plan, the patch diff, and the test results as it works – nothing is pushed to any remote.

### Automated CI Fixes (GitHub Action)

To have Nova automatically rescue failing PRs in your project, add a CI step. The easiest integration is via a GitHub Actions workflow that triggers on a failed test run. For example, save the following as `.github/workflows/nova-ci-rescue.yml`:

```yaml
name: Nova CI-Rescue
on:
  workflow_run:
    workflows: ["CI"] # run after your primary CI workflow
    types: [completed]

jobs:
  rescue:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'failure' &&
      github.event.workflow_run.event == 'pull_request' &&
      github.event.workflow_run.head_repository.full_name == github.repository }}
    permissions:
      contents: write # allow creating fix branch
      pull-requests: write # allow opening PRs
    steps:
      - uses: actions/checkout@v4
        with:
          repository: ${{ github.event.workflow_run.head_repository.full_name }}
          ref: ${{ github.event.workflow_run.head_branch }}
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install Nova and deps
        run: |
          python -m pip install -U pip
          pip install nova-ci-rescue pytest
      - name: Run Nova auto-fix
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: nova fix . --max-iters 5 --timeout 300
      - name: Verify tests pass
        run: pytest -q
```

<small>(Make sure to update workflows: ["CI"] above to match the name of your main test workflow.)</small>

In this setup, whenever your primary CI workflow fails on a pull request, Nova will automatically run in a follow-up job. It checks out the PR code, installs Nova and your test dependencies, and invokes `nova fix .`. Nova will create a new branch (e.g. `nova-fix-123`) with proposed fixes and open a PR against the original branch. The workflow then runs tests again to confirm the fixes. Nova also posts a comment on the original PR to summarize the outcome. All of this requires only standard GitHub tokens and runs entirely in your CI – no external services involved except the LLM API calls.

**GitHub App Alternative**: Nova is also available as a GitHub App that can be installed on your repo for a more turnkey setup (the App handles posting PR comments and opening fix PRs on your behalf). This uses the same underlying action and requires you to provide an API key via repo secrets. Refer to the [Quickstart guide](docs/QUICKSTART.md) for details.

## Configuration & Safety

Nova is highly configurable to suit your project's needs, but comes with conservative defaults out of the box. Key runtime settings include timeouts, iteration limits, model selection, and telemetry, which can be set via CLI flags or environment variables (see [CONFIGURATION.md](docs/CONFIGURATION.md) for the full reference). For example, a minimal `.env` configuration might look like:

```bash
OPENAI_API_KEY=sk-your-openai-key       # or ANTHROPIC_API_KEY for Anthropic Claude
#NOVA_DEFAULT_LLM_MODEL=claude-3-5      # (optional) use Anthropic model instead of GPT-4
NOVA_ENABLE_TELEMETRY=true             # enable saving patches & reports for audit (off by default)
#NOVA_MAX_ITERS=5                      # max fix iterations (default 5)
#NOVA_RUN_TIMEOUT_SEC=300              # overall run timeout in seconds (default 300)
```

By default, Nova will give up after ~5 minutes or 5 fix attempts per PR, whichever comes first. It also limits the scope of changes to avoid over-corrections: for instance, no more than ~200 lines across 10 files will be modified in a single run, and certain paths (config, deployment, secrets) are never touched. All code is executed in a sandboxed environment (your CI runner) with no network calls except to the LLM API, and Nova only accesses files within your repository. You can adjust the limits above if your project requires it, but the defaults aim to err on the side of caution.

**Privacy**: Nova does not send your code or test data anywhere except to your chosen LLM (via API calls using your provided key). There is no telemetry sent to the Nova developers unless you opt-in to share data. Enabling `NOVA_ENABLE_TELEMETRY` only saves logs and artifacts locally (or in your CI artifacts) for your own auditing purposes.

## Contributing

Contributions, feedback, and test reports are welcome! If you encounter issues or have ideas, please open an issue or pull request. Before contributing, please see our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines, and note that all participants are expected to uphold our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

This project is licensed under the MIT License – see [LICENSE](LICENSE) for details.

---
