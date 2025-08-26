# Configuration

Nova reads configuration from environment variables (optionally via a local `.env`) and exposes CLI flags for common runtime controls.

## Quick start with `.env`

Create a `.env` file next to the repo you want to fix (or export env vars):

```bash
# LLM credentials
OPENAI_API_KEY=sk-...
# Or use Anthropic
# ANTHROPIC_API_KEY=...
# NOVA_DEFAULT_LLM_MODEL=claude-3-5-sonnet

# Telemetry (disabled by default). Set to true to save patches and test reports.
NOVA_ENABLE_TELEMETRY=true
NOVA_TELEMETRY_DIR=telemetry

# Limits and safety
NOVA_MAX_ITERS=5
NOVA_RUN_TIMEOUT_SEC=300
NOVA_TEST_TIMEOUT_SEC=120
NOVA_LLM_TIMEOUT_SEC=60
NOVA_MIN_REPO_RUN_INTERVAL_SEC=600
NOVA_MAX_DAILY_LLM_CALLS=200
NOVA_WARN_DAILY_LLM_CALLS_PCT=0.8

# Network allow-list (CSV or JSON-like list)
# NOVA_ALLOWED_DOMAINS=api.openai.com,api.anthropic.com,pypi.org,files.pythonhosted.org,github.com,raw.githubusercontent.com
```

## Environment variables reference

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | — | OpenAI API key used when the default model is an OpenAI model |
| `ANTHROPIC_API_KEY` | — | Anthropic API key; set `NOVA_DEFAULT_LLM_MODEL=claude-3-5-sonnet` to use |
| `OPENSWE_BASE_URL` | — | Optional alternative inference endpoint base URL |
| `OPENSWE_API_KEY` | — | API key for alternative inference endpoint |
| `NOVA_DEFAULT_LLM_MODEL` | `gpt-5-chat-latest` | Default model for the agent |
| `NOVA_MAX_ITERS` | `5` | Max planner/actor/critic iterations |
| `NOVA_RUN_TIMEOUT_SEC` | `300` | Overall timeout for a run |
| `NOVA_TEST_TIMEOUT_SEC` | `120` | Per test run timeout |
| `NOVA_LLM_TIMEOUT_SEC` | `60` | Timeout per LLM call |
| `NOVA_MIN_REPO_RUN_INTERVAL_SEC` | `600` | Cooldown between runs on the same repo |
| `NOVA_MAX_DAILY_LLM_CALLS` | `200` | Hard limit on daily LLM calls |
| `NOVA_WARN_DAILY_LLM_CALLS_PCT` | `0.8` | Warn when usage exceeds this fraction of the daily limit |
| `NOVA_ENABLE_TELEMETRY` | `false` | Enable saving patches/reports; can also be disabled with `--no-telemetry` |
| `NOVA_TELEMETRY_DIR` | `telemetry` | Where to store run artifacts |
| `NOVA_ALLOWED_DOMAINS` | preset list | CSV or JSON-like list of allowed outbound domains |

Allowed domains default:

```
api.openai.com, api.anthropic.com, pypi.org, files.pythonhosted.org, github.com, raw.githubusercontent.com
```

## CLI flags

The `fix` command supports:

```bash
nova fix REPO_PATH \
  --max-iters 5 \
  --timeout 300 \
  --verbose \
  --auto-pr \
  --no-telemetry \
  --whole-file
```

Notes:

- `--whole-file` switches from patch application to whole-file replacement.
- `--no-telemetry` disables saving artifacts for the current run regardless of env.
- A per-repo cooldown prevents back-to-back runs within the configured interval.

