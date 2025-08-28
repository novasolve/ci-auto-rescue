# Configuration

Nova is configured via environment variables (e.g., `.env`).

## Core

- OPENAI_API_KEY: API key for OpenAI (optional if using Anthropic)
- ANTHROPIC_API_KEY: API key for Anthropic (optional if using OpenAI)
- NOVA_DEFAULT_LLM_MODEL: e.g., `gpt-4o`, `gpt-5`, `claude-3-5-sonnet`
- NOVA_REASONING_EFFORT: reasoning effort for GPT models (`low`, `medium`, `high` - default `high`)

## Timeouts and limits (defaults)

- NOVA_MAX_ITERS (default 5)
- NOVA_RUN_TIMEOUT_SEC (default 300)
- NOVA_TEST_TIMEOUT_SEC (default 120)
- NOVA_LLM_TIMEOUT_SEC (default 60)
- NOVA_MIN_REPO_RUN_INTERVAL_SEC (default 600)
- NOVA_MAX_DAILY_LLM_CALLS (default 200)
- NOVA_WARN_DAILY_LLM_CALLS_PCT (default 0.8)

## Telemetry

- NOVA_ENABLE_TELEMETRY: `true` to save patches/reports (default false)
- NOVA_TELEMETRY_DIR: directory for run artifacts (default `telemetry`)

## Network allow-list

- NOVA_ALLOWED_DOMAINS: CSV or `["host"]` format; defaults include OpenAI, Anthropic, GitHub, PyPI.

## Example `.env`

```bash
OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=...
# NOVA_DEFAULT_LLM_MODEL=claude-3-5-sonnet
# NOVA_REASONING_EFFORT=medium  # Use 'low' or 'medium' for faster runs
NOVA_MAX_ITERS=5
NOVA_RUN_TIMEOUT_SEC=300
NOVA_TEST_TIMEOUT_SEC=120
NOVA_ENABLE_TELEMETRY=true
```
