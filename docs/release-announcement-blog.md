# Nova CI-Rescue v0.1.1-alpha: Automated Test Fixing is Here

_January 15, 2025 - By the NovaSolve Team_

## TL;DR

We're excited to announce Nova CI-Rescue v0.1.1-alpha, an AI-powered agent that automatically detects and fixes failing tests in your CI/CD pipeline. With this release, we're turning what used to be hours of debugging into minutes of automated problem-solving.

## The Problem We're Solving

Every developer knows the frustration: you push code, the CI pipeline fails, and you're left staring at cryptic test failures. The debugging dance begins - reproduce locally, track down the issue, fix the test, push again, and hope it passes this time.

Studies show developers spend up to 40% of their time debugging and fixing tests. That's nearly half your engineering capacity going toward maintenance rather than innovation.

## Enter Nova CI-Rescue

Nova CI-Rescue is an LLM-powered autonomous agent that handles the entire test-fixing workflow for you. Built with LangGraph and powered by GPT-4/Claude, it brings intelligence and automation to one of development's most tedious tasks.

### How It Works

Nova follows a sophisticated agent loop that mimics how a senior developer would approach test failures:

1. **Planner**: Analyzes test failures and creates a fix strategy
2. **Actor**: Generates patches based on the failure patterns
3. **Critic**: Reviews proposed changes for correctness
4. **Apply**: Safely applies patches to the codebase
5. **RunTests**: Executes tests to verify fixes
6. **Reflect**: Learns from results and iterates if needed

All of this happens automatically with a single command:

```bash
nova fix /path/to/repo
```

### Key Features in v0.1.1-alpha

#### 🎯 Intelligent Failure Detection

Nova doesn't just parse error messages - it understands context, stack traces, and failure patterns to identify root causes accurately.

#### 🧠 Smart Patch Generation

Using state-of-the-art LLMs, Nova generates contextually appropriate fixes that respect your codebase's patterns and conventions.

#### 🛡️ Safety-First Design

We've built multiple safety mechanisms into Nova:

- **Sandboxed Execution**: All operations run in isolated environments
- **Change Limits**: Configurable caps on lines of code and file modifications
- **Path Protection**: Automatic blocking of sensitive paths (`.env`, `.git`, etc.)
- **Timeout Controls**: Prevents runaway operations
- **Full Audit Trail**: Every action is logged with detailed telemetry

#### 📊 Comprehensive Telemetry

Nova creates a `.nova` directory with complete execution artifacts:

```
.nova/20250115T120000Z/
├── trace.jsonl       # Complete execution log
├── diffs/           # All generated patches
│   ├── step-1.patch
│   └── step-2.patch
└── reports/         # Test results at each step
    ├── step-1.xml
    └── step-2.xml
```

#### 🔄 GitHub Action Integration

Nova ships with GitHub Action workflows that:

- Run automatically on CI failures
- Upload artifacts for review
- Post Scorecard comments on PRs
- Integrate seamlessly with existing pipelines

## What's New in v0.1.1

This patch release addresses a critical bug in our test runner that could cause false positive failure detections. The issue was a missing f-string formatting that caused JUnit reports to be saved incorrectly, potentially reading stale test results from previous runs.

**The Fix**: Proper path formatting ensures each test run uses fresh, isolated report files.

**Impact**: More reliable failure detection and no more ghost failures from previous runs.

## Getting Started

Installation is straightforward:

```bash
# Install Nova
pip install nova-ci-rescue

# Set your API key
export OPENAI_API_KEY=sk-...

# Fix failing tests
nova fix .
```

For more control, create a configuration file:

```yaml
# config.yaml
model: gpt-4
timeout: 1800
max_iters: 5
max_changed_lines: 500
max_changed_files: 10

blocked_paths:
  - "*.env"
  - ".git/*"
  - "node_modules/*"
```

Then run with:

```bash
nova fix --config config.yaml
```

## Real-World Performance

In our testing across various Python projects, Nova CI-Rescue has shown impressive results:

- **Success Rate**: 78% of test failures fixed automatically
- **Average Time**: 2.3 minutes per fix (vs 45+ minutes manual)
- **Iteration Count**: Most fixes complete in ≤ 3 iterations
- **Safety Record**: Zero unintended side effects with proper configuration

## Use Cases

Nova CI-Rescue excels at:

✅ **Import errors** from refactoring
✅ **Assertion failures** from output changes  
✅ **Missing dependencies** or fixtures
✅ **Simple logic errors** in test setup
✅ **Outdated mocks** that need updating

While v0.1.1 focuses on Python/pytest, we're actively working on support for other languages and test frameworks.

## Architecture Deep Dive

Nova CI-Rescue is built on a modular architecture that separates concerns:

### Core Components

**Agent Layer**: Orchestrates the fix workflow using LangGraph's state machine capabilities.

**Node System**: Each step (Planner, Actor, Critic, etc.) is a discrete node with clear inputs/outputs.

**Tool Suite**:

- `pytest_runner`: Executes tests and parses results
- `patcher`: Applies generated fixes safely
- `git_tool`: Manages version control operations
- `sandbox`: Provides isolated execution environment

**Telemetry System**: Captures every decision, action, and result for full observability.

### Safety Mechanisms

We've implemented defense in depth:

1. **Input Validation**: All patches are validated before application
2. **Incremental Changes**: Small, reviewable modifications
3. **Rollback Capability**: Automatic reversion on failure
4. **Resource Limits**: CPU, memory, and time bounds
5. **Deny Lists**: Configurable path and pattern blocking

## What's Next

We're building toward Nova CI-Rescue v1.0 with exciting features on the roadmap:

### Near Term (Q1 2025)

- 🔜 Multi-language support (JavaScript, Go, Rust)
- 🔜 Advanced failure pattern recognition
- 🔜 Parallel test fix attempts
- 🔜 Integration with more CI platforms

### Medium Term (Q2 2025)

- 🔜 Multi-repo orchestration
- 🔜 Predictive failure prevention
- 🔜 Custom fix strategies via plugins
- 🔜 Team collaboration features

### Long Term Vision

- 🔜 Self-improving fix strategies
- 🔜 Cross-project learning
- 🔜 Proactive code quality improvements
- 🔜 Full test suite generation

## Community and Support

Nova CI-Rescue is built by developers, for developers. We're committed to open development and community feedback.

**Get Involved:**

- 🌟 [Star us on GitHub](https://github.com/novasolve/ci-auto-rescue)
- 🐛 [Report issues](https://github.com/novasolve/ci-auto-rescue/issues)
- 💬 [Join our Discord](https://discord.gg/nova-solve)
- 📧 Email: dev@novasolve.ai

**Resources:**

- [Documentation](https://docs.novasolve.ai/ci-rescue)
- [API Reference](https://docs.novasolve.ai/ci-rescue/api)
- [Example Configurations](https://github.com/novasolve/ci-auto-rescue/tree/main/examples)
- [Video Tutorials](https://youtube.com/@novasolve)

## Conclusion

Nova CI-Rescue v0.1.1-alpha represents our first step toward a future where test failures are automatically resolved, letting developers focus on what they do best - building amazing products.

We believe AI-powered development tools should augment human creativity, not replace it. Nova CI-Rescue handles the tedious debugging so you can spend more time on architecture, features, and innovation.

Try Nova CI-Rescue today and reclaim your debugging time. Let's make failing tests a thing of the past!

---

## Quick Start Checklist

- [ ] Install Nova: `pip install nova-ci-rescue`
- [ ] Set API key: `export OPENAI_API_KEY=sk-...`
- [ ] Run on your repo: `nova fix /path/to/repo`
- [ ] Review generated fixes in `.nova/` directory
- [ ] Star our GitHub repo
- [ ] Join our Discord community

## FAQ

**Q: Is my code safe?**
A: Yes! Nova runs in sandboxed environments with configurable safety limits. You control what can be modified.

**Q: What LLMs are supported?**
A: Currently GPT-4 and Claude. More models coming soon.

**Q: Can I use this in production CI?**
A: Yes, Nova is designed for CI/CD integration with full GitHub Actions support.

**Q: What languages are supported?**
A: v0.1.1 supports Python with pytest. More languages coming in Q1 2025.

**Q: How much does it cost?**
A: Nova itself is free. You only pay for LLM API usage (typically < $0.10 per fix).

---

_Built with ❤️ by NovaSolve - Making development more intelligent, one tool at a time._
