# Nova CI-Rescue - Frequently Asked Questions (FAQ)

## General Questions

### What is Nova CI-Rescue?

Nova CI-Rescue is an AI-powered tool that automatically detects and fixes failing tests in your CI/CD pipeline. It uses large language models (LLMs) to understand test failures, generate targeted code fixes, and verify the solutions.

### How does Nova work?

Nova follows a six-step agent loop:

1. **Analyze** failing test errors
2. **Plan** a fix strategy
3. **Generate** code patches
4. **Review** changes for safety
5. **Apply** patches and run tests
6. **Iterate** if tests still fail

### What makes Nova different from GitHub Copilot?

| Feature          | Nova CI-Rescue        | GitHub Copilot            |
| ---------------- | --------------------- | ------------------------- |
| **Purpose**      | Fix failing tests     | Generate code suggestions |
| **Trigger**      | Test failures         | While typing code         |
| **Scope**        | Complete fix workflow | Line/function completion  |
| **Verification** | Runs tests to verify  | No verification           |
| **Integration**  | CI/CD pipeline        | IDE/Editor                |

### Is Nova a replacement for developers?

No. Nova is a developer tool that handles routine test fixes, allowing developers to focus on complex problems. It's like having an assistant who handles the tedious debugging while you work on features.

## Setup & Installation

### What are the system requirements?

- **Python**: 3.10 or higher
- **OS**: Linux, macOS, Windows (WSL recommended)
- **Memory**: 4GB RAM minimum
- **Dependencies**: Git, pytest

### Which API keys do I need?

You need at least one:

- **OpenAI API key** (for GPT-4) - Recommended
- **Anthropic API key** (for Claude) - Alternative

### How do I get an API key?

**OpenAI:**

1. Visit [platform.openai.com](https://platform.openai.com)
2. Sign up or log in
3. Go to API keys section
4. Create new secret key

**Anthropic:**

1. Visit [console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Navigate to API keys
4. Generate new key

### Where do I put my API key?

Three options:

```bash
# Option 1: Environment variable
export OPENAI_API_KEY="sk-..."

# Option 2: .env file
echo "OPENAI_API_KEY=sk-..." > .env

# Option 3: Config file
# In nova-config.yaml:
api_key: sk-...
```

### Can I use Nova without an API key?

No, Nova requires access to an LLM to function. However, you can:

- Use your company's API key
- Use Nova in dry-run mode to preview
- Run Nova in CI with shared keys

## Usage Questions

### How do I run Nova on my project?

```bash
# Basic usage
nova fix .

# With options
nova fix . --max-iters 3 --timeout 300

# With config file
nova fix . --config nova-config.yaml
```

### What if Nova can't fix my tests?

Nova will:

1. Report what it tried
2. Show partial fixes if any
3. Provide debugging hints
4. Save analysis in `.nova/` folder

You can then:

- Review Nova's attempts for insights
- Apply partial fixes selectively
- Complete the fix manually

### How long does Nova take to fix tests?

| Complexity     | Time            | Iterations |
| -------------- | --------------- | ---------- |
| Simple errors  | 30-60 seconds   | 1-2        |
| Logic bugs     | 60-180 seconds  | 2-4        |
| Complex issues | 180-600 seconds | 4-6        |

### Can Nova fix multiple failing tests?

Yes, Nova attempts to fix all failing tests within its iteration limit. It prioritizes simpler fixes first and may fix multiple tests in a single iteration.

### Does Nova work with test frameworks other than pytest?

Currently, Nova has:

- **Full support**: pytest
- **Basic support**: unittest
- **Coming soon**: Jest, Mocha (JavaScript)
- **Planned**: JUnit (Java), RSpec (Ruby)

## Safety & Security

### Is my code sent to OpenAI/Anthropic?

Only relevant portions are sent:

- Test failure messages
- Related source code snippets
- Not your entire codebase

This is similar to how GitHub Copilot works.

### Can Nova break my code?

Nova has multiple safety measures:

- **Change limits**: Max 200 lines per iteration
- **File limits**: Max 10 files per iteration
- **Blocked paths**: Won't modify configs, secrets
- **Git branch**: Creates separate branch for fixes
- **Review step**: AI reviews changes before applying

### What files will Nova never modify?

Nova blocks modifications to:

- `.github/workflows/*` (CI configs)
- `*.env` (environment files)
- `deploy/*` (deployment scripts)
- `secrets/*` (sensitive data)
- Database migrations
- Package lock files

### Can I customize safety limits?

Yes, via configuration:

```yaml
max_changed_lines: 100 # Lower limit
max_changed_files: 5 # Fewer files
blocked_paths:
  - "production/*" # Add custom blocks
  - "*.prod.yml"
```

### How do I review Nova's changes?

```bash
# See what changed
git diff

# Review patches
cat .nova/latest/diffs/*.patch

# Check commit history
git log --oneline

# Selective staging
git add -p
```

## CI/CD Integration

### How do I add Nova to GitHub Actions?

Create `.github/workflows/nova.yml`:

```yaml
name: Nova Auto-Fix
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  nova-fix:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
      - run: pip install nova-ci-rescue
      - run: nova fix . --max-iters 3
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

### Does Nova work with other CI systems?

Yes, Nova works with any CI that can:

- Run Python scripts
- Set environment variables
- Execute shell commands

Examples: Jenkins, GitLab CI, CircleCI, Travis CI

### Can Nova automatically commit fixes?

Yes, but it's configurable:

```bash
# Auto-commit in CI
nova fix . && git commit -am "Nova: Fix tests"

# Or manual review
nova fix . --dry-run  # Preview only
```

### How do I see Nova's results in PRs?

Nova can post PR comments with:

- Number of tests fixed
- Time taken
- Files changed
- Success/failure status

This requires `GITHUB_TOKEN` with PR write permissions.

## Cost & Performance

### How much does Nova cost to run?

API costs per run:
| Model | Simple Fix | Complex Fix |
|-------|------------|-------------|
| GPT-4 | $0.05-0.10 | $0.20-0.50 |
| GPT-4-mini | $0.01-0.03 | $0.05-0.15 |
| Claude-3 | $0.03-0.08 | $0.15-0.40 |

### How can I reduce API costs?

1. **Use cheaper models** for simple fixes:

   ```yaml
   model: gpt-4-mini # Cheaper than gpt-4
   ```

2. **Limit iterations**:

   ```bash
   nova fix . --max-iters 2  # Fewer attempts
   ```

3. **Target specific tests**:
   ```bash
   nova fix . --test-file tests/test_simple.py
   ```

### Will Nova make many API calls?

Nova optimizes API usage:

- Batches context in single calls
- Caches successful fixes
- Stops early when tests pass
- Typical fix: 2-5 API calls

### Can I track Nova's usage?

Yes, Nova provides metrics:

```bash
# View run summary
cat .nova/latest/summary.json

# Track over time
nova history --stats
```

## Troubleshooting

### "API Key Not Found" error

**Check:**

1. Is key set? `echo $OPENAI_API_KEY`
2. Is .env file in current directory?
3. Is key valid? Test with curl
4. Are quotes correct in .env?

### "No tests found" error

**Solutions:**

1. Check test file naming (test\_\*.py)
2. Verify pytest is installed
3. Try: `pytest --collect-only`
4. Specify test dir: `nova fix . --test-dir tests/`

### "Timeout reached" error

**Solutions:**

1. Increase timeout: `--timeout 600`
2. Reduce scope: focus on specific tests
3. Use fewer iterations: `--max-iters 2`
4. Check for hanging tests

### "Patch failed to apply" error

**Causes:**

1. Uncommitted changes in working directory
2. File was modified since Nova started
3. Merge conflict with existing code

**Fix:**

```bash
git stash  # Save current changes
nova fix . # Run Nova
git stash pop  # Restore changes
```

### Nova made wrong fixes

**What to do:**

1. Don't merge the fixes
2. Review Nova's reasoning: `.nova/latest/trace.jsonl`
3. Report issue with example
4. Revert: `git reset --hard HEAD~1`

## Best Practices

### When should I use Nova?

**Good use cases:**

- ✅ After refactoring breaks tests
- ✅ Simple assertion failures
- ✅ Type errors and null checks
- ✅ CI failures on PRs
- ✅ Dependency update breaks

**Poor use cases:**

- ❌ Flaky/intermittent failures
- ❌ Performance issues
- ❌ External service failures
- ❌ Missing dependencies
- ❌ Infrastructure problems

### How do I maximize success rate?

1. **Start simple**: Fix one test at a time
2. **Clean state**: Commit before running
3. **Good tests**: Ensure tests have clear assertions
4. **Limit scope**: Use `--test-file` for focus
5. **Review always**: Check Nova's logic

### Should I run Nova locally or in CI?

**Local development:**

- Faster feedback
- Interactive review
- Good for learning

**CI/CD pipeline:**

- Automatic on PRs
- Consistent environment
- Team visibility

**Recommendation:** Both! Local for quick fixes, CI for automation.

### How do I introduce Nova to my team?

1. **Start small**: Personal use first
2. **Share wins**: Show successful fixes
3. **Set guidelines**: Document when to use
4. **Track metrics**: Measure time saved
5. **Iterate**: Adjust based on feedback

## Advanced Topics

### Can Nova learn from previous fixes?

Not yet in v1.0. Future versions will include:

- Learning from successful patterns
- Team-specific customization
- Fix history analysis

### Does Nova support monorepos?

Yes, with configuration:

```yaml
# Focus on specific package
working_dir: packages/api
test_command: npm test

# Or multiple packages
packages:
  - packages/api
  - packages/web
```

### Can I extend Nova with custom tools?

API for extensions coming in v2.0. Currently:

- Custom test commands supported
- Webhook notifications possible
- Scriptable via CLI exit codes

### How do I debug Nova's decisions?

```python
# Parse Nova's reasoning
import json

with open('.nova/latest/trace.jsonl') as f:
    for line in f:
        event = json.loads(line)
        if event['type'] == 'reasoning':
            print(event['content'])
```

### Can Nova fix non-test code?

Nova is optimized for test fixes. For general code:

- Use GitHub Copilot for generation
- Use Nova when tests catch bugs
- Future versions may expand scope

## Getting Help

### Where can I get support?

1. **Documentation**: [docs.nova.ai](https://docs.nova.ai)
2. **Discord**: [discord.gg/nova](https://discord.gg/nova)
3. **GitHub Issues**: [github.com/nova-solve/ci-auto-rescue](https://github.com/nova-solve/ci-auto-rescue)
4. **Email**: support@joinnova.com

### How do I report a bug?

Create a GitHub issue with:

1. Nova version (`nova --version`)
2. Error message
3. Minimal reproduction case
4. `.nova/latest/trace.jsonl` (if possible)

### Can I contribute to Nova?

Yes! We welcome:

- Bug reports
- Feature requests
- Documentation improvements
- Code contributions

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

### Is there a roadmap?

**v1.1 (Q2 2024)**

- JavaScript/TypeScript support
- Better multi-file handling

**v1.2 (Q3 2024)**

- Java and Go support
- Learning from fixes

**v2.0 (Q4 2024)**

- Full refactoring capability
- Custom extensions API

## Still Have Questions?

If your question isn't answered here:

1. Check [detailed documentation](./nova-v1-documentation.md)
2. Search [GitHub issues](https://github.com/nova-solve/ci-auto-rescue/issues)
3. Ask on [Discord](https://discord.gg/nova)
4. Email support@joinnova.com

Remember: No question is too simple! We're here to help you succeed with Nova.
