# Contributing to Nova CI‑Rescue

Thanks for your interest in improving Nova CI‑Rescue! This document outlines how to set up your dev environment, propose changes, and get them merged smoothly.

## Ways to contribute

- Report bugs and propose enhancements
- Improve docs and examples
- Add tests and increase coverage
- Implement features aligned with the roadmap

## Development setup

```bash
git clone https://github.com/novasolve/ci-auto-rescue
cd ci-auto-rescue
python -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .

# Sanity check
nova version
```

## Running the demo locally

```bash
export OPENAI_API_KEY=sk-...
nova fix examples/demos/demo_broken_project
```

## Testing

```bash
pytest -q
```

Please include tests for bug fixes and new features where practical.

## Code style

- Python 3.10+
- Prefer clear naming, early returns, and small focused functions
- Avoid catching exceptions without meaningful handling
- Match existing formatting; keep unrelated reformatting out of PRs

## Pull Request checklist

- Clear title and description of the change and motivation
- Tests pass locally (`pytest`)
- Docs updated when behavior or public APIs change
- No unrelated changes bundled together

## Release and versioning

- The CLI reports the current version via `nova version`
- Keep changes backward-compatible when possible

## Governance and conduct

- Please follow our [Code of Conduct](CODE_OF_CONDUCT.md)
- For sensitive issues, email dev@novasolve.ai

