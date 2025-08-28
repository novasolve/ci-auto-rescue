# Contributing to Nova CI‑Rescue

Thanks for your interest in improving Nova CI‑Rescue! We welcome issues and PRs.

## Getting started

- Fork the repo and create a branch following our [branch naming convention](#branch-naming-convention)
- Create a virtualenv and install in editable mode: `pip install -e .[dev]`
- Run tests locally before submitting: `pytest -q`

## Branch naming convention

We follow a **trunk-based development** model with the following branch structure:

### Main branches
- **`main`** - Releasable trunk (PR-only, no direct pushes)
- **`release/*`** - Optional frozen patch lines for hotfixes (e.g., `release/v1.2`)

### Short-lived feature branches
Use these prefixes for all development work:
- **`feat/<slug>`** - New features (e.g., `feat/add-retry-logic`)
- **`fix/<slug>`** - Bug fixes (e.g., `fix/handle-timeout-errors`)
- **`docs/<slug>`** - Documentation updates (e.g., `docs/update-api-guide`)
- **`chore/<slug>`** - Maintenance tasks (e.g., `chore/update-dependencies`)
- **`ci/<slug>`** - CI/CD improvements (e.g., `ci/add-security-scan`)
- **`perf/<slug>`** - Performance improvements (e.g., `perf/optimize-test-runner`)

### Bot/experiment branches
- **`bot/<tool>/<date>-<slug>`** - Ephemeral automation branches (auto-deleted)
  - Example: `bot/nova-auto-fix/2025-08-28-memory-leak`

### Examples
```bash
# Good branch names
git checkout -b feat/llm-integration
git checkout -b fix/pytest-collection-error
git checkout -b docs/installation-guide
git checkout -b chore/cleanup-legacy-code

# Avoid these patterns
git checkout -b development        # Use main as trunk instead
git checkout -b demo-branch        # Use tags for demos: demo-v1.0
git checkout -b my-feature         # Missing type prefix
```

## Pull requests

- Keep PRs focused and small when possible
- Include a clear description of the problem and solution
- Add tests when fixing bugs or adding features
- Update docs when behavior changes

## Code style

- Python 3.10+, type hints where practical
- Follow readability-first principles; avoid clever one-liners
- Match existing formatting; run `ruff`/`black` if configured

## Commit messages

- Conventional style preferred: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`

## Security

- Do not include secrets in code or tests
- Report security concerns privately via GitHub Security Advisories

## License

By contributing, you agree that your contributions are licensed under the MIT License.
