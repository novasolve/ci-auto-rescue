# Nova CI-Rescue - Frequently Asked Questions

## General Questions

### What is Nova CI-Rescue?

Nova CI-Rescue is an AI-powered tool that automatically fixes failing tests in your codebase. It uses advanced language models to understand test failures, generate fixes, and verify solutions - all without human intervention.

### What's new in v1.1?

Version 1.1 introduces the **Deep Agent Architecture**, powered by LangChain. This is a complete reimplementation that replaces the old multi-node pipeline with an intelligent agent that can:
- Reason through problems step-by-step
- Dynamically choose which tools to use
- Self-correct when initial approaches fail
- Maintain context throughout the fixing process

### Do I need to change how I use Nova?

No! The CLI interface remains exactly the same. Just run `nova fix` as before, but enjoy better results.

## Deep Agent Questions

### What is the Deep Agent?

The Deep Agent is Nova's new intelligent core - a LangChain-powered agent that uses ReAct (Reasoning and Acting) patterns to fix tests. Instead of following a fixed pipeline, it:
1. **Reasons** about the problem
2. **Acts** by using appropriate tools
3. **Observes** the results
4. **Adapts** its approach based on what it learns

### How is the Deep Agent different from v1.0?

| Aspect | v1.0 Pipeline | v1.1 Deep Agent |
|--------|---------------|-----------------|
| Architecture | Separate nodes (Planner→Actor→Critic) | Unified intelligent agent |
| Decision Making | Fixed logic | Dynamic reasoning |
| Context | Limited between nodes | Full context throughout |
| Adaptability | Basic retry logic | Intelligent strategy adjustment |
| Success Rate | 70-85% simple, 40-50% complex | 85-95% simple, 65-75% complex |

### What tools does the Deep Agent use?

The Deep Agent has access to specialized tools:
- **open_file**: Read code files intelligently
- **write_file**: Write code with validation
- **run_tests**: Execute tests and analyze results
- **apply_patch**: Apply changes safely
- **critic_review**: Review patches before application

### Can I see what the Deep Agent is thinking?

Yes! Use the `--verbose` flag to see the agent's reasoning:
```bash
nova fix --verbose
```

This will show the agent's thought process, tool selections, and decision-making.

## Performance Questions

### Is v1.1 faster than v1.0?

Yes! Despite the added intelligence, v1.1 is actually faster:
- Average fix time: 30-60s (vs 45-90s in v1.0)
- Fewer iterations needed: 2-3 (vs 3-5 in v1.0)
- Better first-attempt success rate

### What are the success rates?

v1.1 shows significant improvements:
- Simple fixes: 85-95% (up from 70-85%)
- Complex multi-file issues: 65-75% (up from 40-50%)
- Major refactoring: 50-60% (up from 20-30%)

### Why does the Deep Agent sometimes seem to pause?

The agent is reasoning through the problem. This 2-5 second "thinking time" leads to better decisions and fewer failed attempts overall.

## Safety Questions

### Is the Deep Agent safe to use?

Yes! The Deep Agent has multiple safety layers:
1. **Tool-level safety**: Restricted paths, size limits
2. **Critic review**: Every patch is reviewed before application
3. **Application guards**: Pre-flight checks and validation
4. **Automatic rollback**: On safety violations

### What files will Nova never modify?

By default, Nova won't modify:
- Test files (unless specifically fixing test code)
- Configuration files (.env, config.yml, etc.)
- CI/CD files (.github/, .gitlab-ci.yml)
- Secret files (anything with 'secret' or 'key' in the name)
- Deployment files

### Can I customize safety limits?

Yes! In your `nova.config.yml`:
```yaml
max_patch_lines: 500      # Maximum lines per patch
max_affected_files: 10    # Maximum files per patch
blocked_paths:            # Additional paths to block
  - production/
  - sensitive_data/
```

## Configuration Questions

### What models does v1.1 support?

Nova v1.1 supports:
- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude-3 (Opus, Sonnet, Haiku)

### How do I switch between models?

In your config file:
```yaml
model: gpt-4  # or gpt-3.5-turbo, claude-3-opus, etc.
```

Or via environment:
```bash
export NOVA_MODEL=claude-3-opus
```

### What happened to the --enhanced flag?

It's gone! The Deep Agent is now the only implementation. There's no need for flags to choose between agents.

## Troubleshooting Questions

### "No valid API key found"

Make sure you've set your API key:
```bash
export OPENAI_API_KEY="sk-..."
# or
export ANTHROPIC_API_KEY="sk-ant-..."
```

Verify with:
```bash
nova config
```

### The agent seems stuck

The Deep Agent might be exploring the codebase. Use `--verbose` to see what it's doing. For complex problems, consider increasing the timeout:
```bash
nova fix --timeout 1800  # 30 minutes
```

### Tests still failing after Nova runs

This can happen with:
- Tests requiring external services
- Flaky tests with race conditions
- Tests needing specific environment setup

Try running Nova again - it often succeeds on a second attempt with the context from the first run.

### How do I limit the scope of changes?

Use configuration to restrict the agent:
```yaml
max_iterations: 3         # Fewer attempts
max_patch_lines: 200      # Smaller patches
max_affected_files: 3     # Fewer files
```

## Migration Questions

### How do I upgrade from v1.0?

Simply upgrade the package:
```bash
pip install --upgrade nova-ci-rescue
```

No other changes needed!

### Will my v1.0 config files work?

Yes! All v1.0 configuration is compatible with v1.1.

### What about my CI/CD pipelines?

No changes needed. Your existing CI/CD configurations will work with v1.1.

### Can I rollback to v1.0?

Yes, but we don't recommend it:
```bash
pip install nova-ci-rescue==1.0.0
```

v1.1 is superior in every way.

## Advanced Questions

### Can I extend the Deep Agent with custom tools?

Not yet in v1.1, but this is planned for v1.2. The architecture is designed to support custom tools in the future.

### Does the agent learn from previous fixes?

Not persistently in v1.1. Each run starts fresh. Learning across runs is planned for a future release.

### Can I see the agent's reasoning after the run?

Yes! Check the telemetry logs in `.nova/telemetry/` for complete reasoning traces.

### How does the agent handle large codebases?

The agent intelligently focuses on relevant files. For very large codebases (>10k files), it may take longer to explore, but it won't try to load everything into context.

## Integration Questions

### Does Nova work with GitHub Actions?

Yes! Here's a simple GitHub Action:
```yaml
- name: Fix failing tests
  run: nova fix
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

### Can Nova create pull requests?

Not directly, but it creates a branch with fixes. You can then create a PR:
```bash
nova fix
git push origin HEAD
# Then create PR via GitHub UI or CLI
```

### Does Nova work with languages other than Python?

Currently Python/pytest only. JavaScript/TypeScript support is coming in v1.2.

### Can Nova fix integration tests?

It can try! Success depends on whether the fix is in code (likely to work) or requires external service configuration (less likely).

## Getting Help

### Where can I report issues?

Report issues on GitHub: https://github.com/nova-solve/ci-auto-rescue/issues

### Is there a community forum?

Yes! Join our Discord: https://discord.gg/nova-rescue

### How can I contribute?

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Where can I find more examples?

Check out:
- [Demo repository](https://github.com/nova-solve/demo-failing-tests)
- [Video tutorials](https://youtube.com/nova-rescue)
- [Blog posts](https://nova-solve.com/blog)

## Quick Answers

**Q: Is v1.1 production-ready?**
A: Yes! It's more stable and reliable than v1.0.

**Q: Will it break my code?**
A: Nova has multiple safety guards and works in a separate branch.

**Q: How much does it cost in API fees?**
A: Typically $0.10-0.50 per fix with GPT-4, less with GPT-3.5.

**Q: Can it fix all test failures?**
A: No, but it handles 85-95% of common issues.

**Q: Should I review the fixes?**
A: Yes, always review AI-generated code before merging.

**Q: Is my code sent to OpenAI/Anthropic?**
A: Only the relevant parts needed to fix tests, not your entire codebase.

---

Still have questions? Check the [documentation](README.md) or [open an issue](https://github.com/nova-solve/ci-auto-rescue/issues)!
