# Installation

## Requirements

- Python 3.10+
- macOS, Linux, or WSL2 on Windows
- An LLM API key (OpenAI or Anthropic)

## From source (recommended)

```bash
git clone https://github.com/novasolve/ci-auto-rescue
cd ci-auto-rescue
python -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .

# Verify installation
nova version
```

## Configure credentials

Set one of the following:

```bash
export OPENAI_API_KEY=sk-...
# or
export ANTHROPIC_API_KEY=...
export NOVA_DEFAULT_LLM_MODEL=claude-3-5-sonnet
```

Optionally, create a `.env` file in your project root (see the configuration guide).

## Try the demo

```bash
nova fix examples/demos/demo_broken_project
```

Nova will create a temporary branch, propose changes, and run tests until they pass or limits are reached.

