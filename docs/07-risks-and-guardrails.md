# Nova CI-Rescue — Risks & Guardrails

## Safety Caps

### Code Change Limits
- **Max Lines Changed:** ≤200 LOC per run
- **Max Files Modified:** ≤10 files per run
- **Reason:** Prevent runaway changes that could introduce major regressions

### Denylisted Paths
Never modify these paths:
- `deploy/` - Deployment configurations
- `secrets/` - Sensitive data
- `.github/workflows/` - CI/CD configurations (except nova.yml)
- `.env` files
- `**/credentials/**`
- `**/keys/**`

## Time/Iteration Limits

### Command Line Options
- `--timeout <seconds>`: Maximum runtime (default: 1200s / 20 min)
- `--max-iters <number>`: Maximum fix attempts (default: 6)

### Environment Variables
```bash
NOVA_RUN_TIMEOUT_SEC=1200  # 20 minutes
NOVA_TEST_TIMEOUT_SEC=600  # 10 minutes per test run
NOVA_MAX_ITERS=6           # Maximum iterations
```

## Model Selection

### Default Strategy
- **Primary:** GPT-4o-mini (cost-effective)
- **Fallback:** GPT-4o (for complex fixes)
- **Multi-file:** OpenSWE integration

### Cost Estimates
| Model | Cost per Fix | When to Use |
|-------|-------------|-------------|
| GPT-4o-mini | ~$0.05-0.10 | Default, simple fixes |
| GPT-4o | ~$0.50-1.00 | Complex logic changes |
| Claude-3-sonnet | ~$0.10-0.20 | Alternative for specific patterns |
| Claude-3-opus | ~$0.75-1.50 | Heavy refactoring |

## Known Risks

### GitHub Action Permissions
- **Risk:** PR comment may fail without proper permissions
- **Mitigation:** Ensure GITHUB_TOKEN has `pull-requests: write` permission

### Plugin Availability
- **Risk:** pytest-json-report may not be installed
- **Mitigation:** Fallback to JUnit XML format

### Model Determinism
- **Risk:** Same prompt may produce different fixes
- **Mitigation:** Use temperature=0, seed parameters when available

### Test Flakiness
- **Risk:** Intermittent failures may cause false positives
- **Mitigation:** Run tests multiple times before declaring success

## Security Considerations

### API Key Management
- Never commit API keys to version control
- Use environment variables or secure vaults
- Rotate keys regularly

### Network Access
- Limit HTTP requests to allowed domains
- Default allowed: GitHub, PyPI, OpenAI, Anthropic
- Configure via `NOVA_ALLOWED_DOMAINS`

### Code Execution
- All code changes run in sandboxed environment
- No system calls without explicit approval
- File system access limited to repository

## Monitoring & Alerts

### Telemetry Collection
- All runs logged to `.nova/<run>/trace.jsonl`
- Metrics collected: duration, iterations, success rate
- No PII collected by default

### Alert Thresholds
- Alert if success rate < 80%
- Alert if average iterations > 4
- Alert if runtime > 30 minutes

## Emergency Procedures

### Abort Running Fix
```bash
# Ctrl+C to stop
# Then reset:
git reset --hard HEAD
git clean -fd
```

### Rollback Changes
```bash
# Find the pre-nova commit
git reflog
# Reset to it
git reset --hard <commit-hash>
```

### Disable Nova Temporarily
```bash
# Remove from CI
git rm .github/workflows/nova.yml
git commit -m "Temporarily disable Nova"
```
