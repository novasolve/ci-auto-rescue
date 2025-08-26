# Quickstart Guide

Get Nova CI-Rescue fixing your failing tests in under 5 minutes.

## Step 1: Install the GitHub App

[![Install Nova CI‑Rescue](https://img.shields.io/badge/Install-GitHub%20App-blue?logo=github)](https://github.com/apps/nova-ci-rescue/installations/new)

1. Click the install button above
2. Choose your organization or personal account
3. Select "All repositories" or specific repos you want Nova to monitor
4. Click **Install**

![GitHub App Installation](https://via.placeholder.com/600x300/f8f9fa/6c757d?text=GitHub+App+Installation+Flow)

## Step 2: Add your API key

Nova needs an OpenAI API key to analyze and fix your code.

1. Go to your repository → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `OPENAI_API_KEY`
4. Value: Your OpenAI API key (starts with `sk-`)
5. Click **Add secret**

> **Don't have an OpenAI API key?** Get one at [platform.openai.com](https://platform.openai.com/api-keys)

## Step 3: Add the Nova workflow

Create `.github/workflows/nova-ci-rescue.yml` in your repository:

```yaml
name: Nova CI-Rescue (on CI failure)

on:
  workflow_run:
    workflows: ["CI"] # ⚠️ Must match your CI workflow name exactly
    types: [completed]

concurrency:
  group: nova-rescue-${{ github.event.workflow_run.head_repository.full_name }}-${{ github.event.workflow_run.head_branch }}
  cancel-in-progress: false

jobs:
  rescue:
    if: >-
      ${{
        github.event.workflow_run.conclusion == 'failure' &&
        github.event.workflow_run.event == 'pull_request' &&
        github.event.workflow_run.head_repository.full_name == github.repository
      }}
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write

    steps:
      - name: Checkout PR head
        uses: actions/checkout@v4
        with:
          repository: ${{ github.event.workflow_run.head_repository.full_name }}
          ref: ${{ github.event.workflow_run.head_branch }}
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install Nova + test deps
        run: |
          python -m pip install -U pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
          pip install nova-ci-rescue pytest

      - name: Configure git author
        run: |
          git config user.name "nova-ci-rescue[bot]"
          git config user.email "nova-ci-rescue[bot]@users.noreply.github.com"

      - name: Run Nova auto-fix
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NOVA_ENABLE_TELEMETRY: "true"
          NOVA_DEFAULT_LLM_MODEL: "gpt-4o"
        run: |
          nova fix . --max-iters 5 --timeout 300

      - name: Re-run tests (confirm green)
        run: pytest -q
```

**Important:** Change `workflows: ["CI"]` to match your actual CI workflow name.

## Step 4: Ensure you have a CI workflow

Nova triggers when your CI fails. Make sure you have a basic CI workflow at `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install deps
        run: |
          python -m pip install -U pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
          pip install pytest
      - name: Run tests
        run: pytest -q
```

## Step 5: Test it out

Create a pull request with a failing test to see Nova in action:

1. **Create a branch:** `git checkout -b test-nova-fix`
2. **Break a test:** Edit a test file to make it fail
3. **Push and open PR:** `git push origin test-nova-fix`
4. **Watch the magic:**
   - Your CI will fail ❌
   - Nova will automatically trigger 🤖
   - Nova will analyze, fix, and open a new PR with the solution ✅

## Step 6: See Nova's results

After Nova runs, you'll see:

### ✅ GitHub Check

Nova posts a status check showing what it did:

![Nova Check Status](https://via.placeholder.com/500x100/28a745/ffffff?text=✓+Nova+CI-Rescue+triggered+auto-fix)

### 💬 PR Comment

Nova leaves a comment explaining the failure and linking to the fix:

> 🤖 **Nova CI-Rescue detected failing tests and triggered an auto-fix.**
>
> View the fix workflow: [Actions → Nova CI-Rescue](link-to-actions)

### 🔧 Fix Pull Request

Nova opens a new PR with:

- **Focused fixes** for the failing tests
- **Detailed explanation** of what was changed and why
- **Test results** showing green status
- **Artifacts** (patches, logs) for review

![Before and After](https://via.placeholder.com/600x200/dc3545/ffffff?text=Before%3A+❌+Tests+Failing)
![Arrow](https://via.placeholder.com/50x50/6c757d/ffffff?text=→)
![After Fix](https://via.placeholder.com/600x200/28a745/ffffff?text=After%3A+✅+Tests+Passing)

## What's Next?

- **Review Nova's fixes** before merging - always verify the changes make sense
- **Customize behavior** with [configuration options](CONFIGURATION.md)
- **Get help** if something doesn't work - see [Troubleshooting](TROUBLESHOOTING.md)

---

## Quick Test (Local)

Want to try Nova locally first? Run this one-liner:

```bash
pip install nova-ci-rescue && \
export OPENAI_API_KEY=sk-your-key && \
git clone https://github.com/novasolve/ci-auto-rescue.git && \
nova fix ci-auto-rescue/examples/demos/demo_broken_project
```

This will show you Nova fixing a deliberately broken calculator project.

---

**Need help?** Check [Troubleshooting & FAQ](TROUBLESHOOTING.md) or [open an issue](https://github.com/novasolve/ci-auto-rescue/issues).
