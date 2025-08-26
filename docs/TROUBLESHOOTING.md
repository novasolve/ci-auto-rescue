# Troubleshooting & FAQ

## Common Issues

### Nova didn't post anything after CI failed

**Checklist:**

- ✅ Verify the Nova CI-Rescue GitHub App is installed on your repository
- ✅ Confirm CI actually failed (check the Actions tab)
- ✅ Ensure `OPENAI_API_KEY` is set in repository secrets
- ✅ Check that `.github/workflows/nova-ci-rescue.yml` exists in your repo
- ✅ Verify the workflow name in `nova-ci-rescue.yml` matches your CI workflow exactly (case-sensitive)

**Common fixes:**

- Re-install the GitHub App if permissions changed
- Check repository Settings → Secrets → Actions for missing API keys
- Ensure the failing workflow runs on `pull_request` events (Nova only triggers on PR failures)

### Nova says it can't fix the issue

**What this means:**
Nova encountered a scenario it can't handle automatically. This could be:

- Complex multi-file refactoring beyond current scope
- Infrastructure/environment issues (missing dependencies, Docker problems)
- Non-Python codebases (currently only Python/pytest is fully supported)
- Test failures requiring domain knowledge or architectural changes

**Next steps:**

1. **Check the logs:** Look at the Nova workflow run in Actions for specific error messages
2. **Fix manually:** Use Nova's analysis as a starting point for manual fixes
3. **Contact support:** If you believe this should be fixable, open an issue with:
   - Link to the failing PR
   - Nova's workflow logs
   - Description of what you expected vs. what happened

### Supported languages and frameworks

**Currently supported:**

- ✅ **Python** with pytest
- ✅ **JavaScript/TypeScript** with Jest (experimental)

**Coming soon:**

- 🔄 Go with standard testing
- 🔄 Java with JUnit
- 🔄 Rust with cargo test
- 🔄 Ruby with RSpec

**Not yet supported:**

- ❌ Complex multi-service applications
- ❌ Integration tests requiring external services
- ❌ UI/browser tests (Selenium, Playwright)
- ❌ Performance/load tests

### Data privacy and security

**Code handling:**

- Your code is sent securely to OpenAI/Anthropic APIs for analysis
- Nova does not store your code on our servers
- All communication uses HTTPS encryption
- API providers have their own data retention policies (see [OpenAI](https://openai.com/privacy/) and [Anthropic](https://www.anthropic.com/privacy) privacy policies)

**Repository access:**

- Nova only accesses repositories where the GitHub App is installed
- Requires minimal permissions: read code, write pull requests, read/write checks
- Cannot access private repositories unless explicitly granted permission

**For enterprise:** Contact us about on-premises deployment options that keep your code entirely within your infrastructure.

### Manual triggering

**GitHub comment trigger:**
Add a comment on any PR with:

```
@nova-ci-rescue fix
```

**Workflow dispatch:**
Go to Actions → Nova CI-Rescue → Run workflow to manually trigger a fix attempt.

**Local CLI:**

```bash
# Install Nova locally
pip install nova-ci-rescue

# Run on any repository
nova fix . --max-iters 5
```

## Frequently Asked Questions

### Q: How much does Nova cost?

**A:** Nova is free during the beta period. We'll announce pricing before any charges begin.

### Q: Can Nova fix issues in private repositories?

**A:** Yes, but you need to explicitly grant access when installing the GitHub App. Nova respects all repository permissions.

### Q: What happens if Nova creates a bad fix?

**A:** Nova always creates a separate branch and opens a PR for review. Never merge without reviewing the changes. If Nova consistently creates poor fixes, please report this as a bug.

### Q: Can I customize Nova's behavior?

**A:** Yes, through environment variables and optional `nova-config.yaml`:

```yaml
model: gpt-4o
timeout: 300
max_iters: 5
blocked_paths:
  - ".github/workflows/*"
  - "*.md"
```

### Q: Why did Nova skip my failing test?

**A:** Nova focuses on unit tests and may skip:

- Integration tests requiring external services
- Tests with complex setup/teardown
- Flaky tests that pass/fail inconsistently
- Tests in unsupported languages/frameworks

### Q: How can I see what Nova actually changed?

**A:** Check the PR Nova opens - it includes:

- Detailed diff of all changes
- Explanation of what was fixed and why
- Test results before and after
- Telemetry artifacts (if enabled)

### Q: Can Nova work with monorepos?

**A:** Limited support. Nova works best with single-service repositories. For monorepos, it may only fix tests in the root directory or specific subdirectories.

## Getting Help

**Bug reports:** [Open an issue](https://github.com/novasolve/ci-auto-rescue/issues/new) with:

- Link to failing PR or workflow run
- Expected vs. actual behavior
- Nova's logs from the Actions tab

**Feature requests:** [Discussions](https://github.com/novasolve/ci-auto-rescue/discussions)

**Enterprise support:** Contact support@novasolve.ai

---

_Last updated: January 2025_
