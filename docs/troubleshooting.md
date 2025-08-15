# Nova CI-Rescue Troubleshooting Guide

This guide helps resolve common issues when using Nova CI-Rescue.

## Common Issues and Solutions

### Installation Issues

**Q: Nova CLI fails with an import error about `NovaConfig` or `CLIConfig`.**  
**A:** This typically means you have an older version installed. Try reinstalling:

```bash
pip uninstall nova-ci-rescue
pip install -e .  # For development installation
# OR
pip install nova-ci-rescue  # For production installation
```

**Q: Running `nova --version` doesn't work.**  
**A:** Make sure you have the latest version installed (v1.0.0 or higher). The `--version` flag was added in v1.0.0. You can also use `nova version` as an alternative.

### API Key Issues

**Q: Nova fails with "Missing API key" error.**  
**A:** Nova CI-Rescue requires an LLM API key to function. Set up your API keys using one of these methods:

1. **Environment Variables (Recommended for CI/CD):**

   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   # Optional: for Claude models
   export ANTHROPIC_API_KEY="your-anthropic-key-here"
   ```

2. **`.env` File (Recommended for local development):**

   ```bash
   # Create a .env file in your project root
   cp env.example .env
   # Edit .env and add your keys:
   # OPENAI_API_KEY=your-api-key-here
   # ANTHROPIC_API_KEY=your-anthropic-key-here  # Optional
   ```

3. **Configuration File:**
   ```yaml
   # In your config.yaml
   openai_api_key: "your-api-key-here" # Not recommended for security
   ```

**Q: How do I get an API key?**  
**A:**

- **OpenAI:** Sign up at [platform.openai.com](https://platform.openai.com) and create an API key in your account settings
- **Anthropic:** Apply for access at [anthropic.com](https://anthropic.com) and get your API key from the console

### Timeout Issues

**Q: Nova times out before fixing all tests.**  
**A:** The default timeout is 1200 seconds (20 minutes). For large test suites or complex fixes, increase the timeout:

```bash
# Increase timeout to 30 minutes (1800 seconds)
nova fix . --timeout 1800

# Or set via environment variable
export NOVA_RUN_TIMEOUT_SEC=1800
nova fix .
```

**Q: Individual test runs are timing out.**  
**A:** Test runs have a separate timeout (default 600 seconds). Increase it via:

```bash
export NOVA_TEST_TIMEOUT_SEC=900  # 15 minutes
```

### Iteration Limit Issues

**Q: Nova stops after a few attempts without fixing all tests.**  
**A:** Nova has a default iteration limit of 6. Increase it if needed:

```bash
# Allow up to 10 iterations
nova fix . --max-iters 10

# Or via environment variable
export NOVA_MAX_ITERS=10
```

### Test Discovery Issues

**Q: Nova says "No failing tests found" but I have failing tests.**  
**A:** Nova uses pytest to discover tests. Ensure:

1. Your tests are discoverable by pytest (follow naming conventions)
2. You're running Nova from the correct directory
3. Your test files match the pattern `test_*.py` or `*_test.py`
4. The tests are not being skipped or marked as xfail

Run pytest manually to verify:

```bash
pytest --tb=short
```

### Patch Application Issues

**Q: Nova generates a patch but it fails to apply.**  
**A:** This can happen if:

1. The working directory has uncommitted changes
2. The file structure has changed since analysis
3. There are merge conflicts

Solutions:

```bash
# Commit or stash your changes first
git stash
nova fix .

# Or create a clean branch
git checkout -b nova-fix
nova fix .
```

### Safety Limit Violations

**Q: Nova refuses to apply a patch due to safety limits.**  
**A:** Nova has built-in safety limits to prevent dangerous changes:

- Max 200 lines changed (default)
- Max 10 files modified (default)
- Restricted paths (CI configs, secrets, etc.)

These are intentional safety features. If the changes are legitimate:

1. Review and apply the patch manually
2. Break large changes into smaller patches
3. Adjust limits in configuration (use with caution)

### Model Selection Issues

**Q: How do I use a different LLM model?**  
**A:** Specify the model via command line or config:

```bash
# Use GPT-4
nova fix . --model gpt-4

# Use Claude
nova fix . --model claude-3-sonnet-20240229

# Use a custom model endpoint
export OPENSWE_BASE_URL="your-endpoint"
export OPENSWE_API_KEY="your-key"
nova fix . --model openswe
```

### Git Integration Issues

**Q: Nova creates too many commits.**  
**A:** Nova creates a commit for each successful patch. To squash them:

```bash
# After Nova completes
git rebase -i HEAD~n  # where n is the number of commits
# Mark all but the first as 'squash'
```

**Q: Nova fails with git-related errors.**  
**A:** Ensure:

1. Git is installed and configured
2. You're in a git repository
3. The repository is not in a detached HEAD state
4. You have write permissions

### Performance Issues

**Q: Nova is very slow.**  
**A:** Performance can be affected by:

1. **Large codebases:** Nova analyzes the entire repository
2. **Slow tests:** Consider parallelizing or optimizing tests
3. **Network latency:** API calls to LLM providers
4. **Model choice:** Larger models (GPT-4) are slower than smaller ones (GPT-3.5)

Tips:

- Use faster models for initial attempts
- Limit the scope with specific test files
- Ensure good network connectivity

### Debug and Telemetry

**Q: How can I see what Nova is doing?**  
**A:** Nova provides detailed telemetry:

```bash
# Enable verbose output
nova fix . --verbose

# Check telemetry files
ls telemetry/
cat telemetry/*/trace.jsonl  # View execution trace

# View generated patches
ls telemetry/*/patches/
```

**Q: How do I report a bug?**  
**A:** When reporting issues:

1. Include the Nova version: `nova --version`
2. Share relevant telemetry files (remove sensitive data)
3. Provide a minimal reproducible example
4. Include error messages and stack traces

## Environment Variables Reference

| Variable                 | Default   | Description                     |
| ------------------------ | --------- | ------------------------------- |
| `OPENAI_API_KEY`         | -         | OpenAI API key (required)       |
| `ANTHROPIC_API_KEY`      | -         | Anthropic API key (optional)    |
| `NOVA_MAX_ITERS`         | 6         | Maximum fix iterations          |
| `NOVA_RUN_TIMEOUT_SEC`   | 1200      | Overall timeout in seconds      |
| `NOVA_TEST_TIMEOUT_SEC`  | 600       | Per-test-run timeout            |
| `NOVA_TELEMETRY_DIR`     | telemetry | Telemetry output directory      |
| `NOVA_DEFAULT_LLM_MODEL` | gpt-4     | Default model to use            |
| `NOVA_ALLOWED_DOMAINS`   | (various) | Comma-separated allowed domains |

## Getting Help

If your issue isn't covered here:

1. Check the [documentation](https://github.com/your-org/nova-ci-rescue/docs)
2. Search [existing issues](https://github.com/your-org/nova-ci-rescue/issues)
3. Join our [Discord community](https://discord.gg/nova-rescue)
4. Open a [new issue](https://github.com/your-org/nova-ci-rescue/issues/new)

## Quick Diagnostic Script

Run this script to check your Nova installation:

```bash
#!/bin/bash
echo "Nova CI-Rescue Diagnostic"
echo "========================="
echo "Version: $(nova --version 2>&1)"
echo "Python: $(python --version)"
echo "Pip: $(pip --version)"
echo "Git: $(git --version)"
echo ""
echo "Environment Variables:"
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:+[SET]}"
echo "ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:+[SET]}"
echo "NOVA_MAX_ITERS: ${NOVA_MAX_ITERS:-[DEFAULT: 6]}"
echo "NOVA_RUN_TIMEOUT_SEC: ${NOVA_RUN_TIMEOUT_SEC:-[DEFAULT: 1200]}"
echo ""
echo "Nova Installation:"
pip show nova-ci-rescue
echo ""
echo "Test Discovery:"
pytest --collect-only 2>&1 | head -20
```

Save this as `diagnose_nova.sh` and run it to quickly identify configuration issues.
