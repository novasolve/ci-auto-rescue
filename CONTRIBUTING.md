# Contributing to Nova CI‑Rescue

Thanks for your interest in improving Nova CI‑Rescue! We welcome issues and PRs.

## Getting started

- Fork the repo and create a branch: `git checkout -b feat/your-change`
- Create a virtualenv and install in editable mode: `pip install -e .[dev]`
- Run tests locally before submitting: `pytest -q`

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
