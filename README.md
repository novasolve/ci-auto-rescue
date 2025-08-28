# Nova CI-Rescue 🚀

[![Release](https://img.shields.io/github/v/release/novasolve/ci-auto-rescue?label=Release)](https://github.com/novasolve/ci-auto-rescue/releases/latest)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org)
[![Install Nova CI-Rescue](https://img.shields.io/badge/Install-GitHub%20App-blue?logo=github)](https://github.com/apps/nova-ci-rescue/installations/new)

**Never let failing tests block your CI/CD pipeline again!** 🎯

Nova CI-Rescue automatically fixes failing tests by analyzing failures, generating targeted patches, and creating reviewable pull requests. Powered by advanced LLMs with a sophisticated Planner → Actor → Critic workflow.

## ✨ Features

- 🤖 **Autonomous Test Fixing** - Analyzes failures and generates intelligent patches
- 🎯 **High Success Rate** - 85-95% success on moderately complex test failures  
- ⚡ **Multiple LLM Support** - GPT-5, GPT-4, Claude 3.5 Sonnet
- 🔒 **Built-in Safety** - Critic validates all patches before application
- 📊 **Full Auditability** - Saves patches, test reports, and execution logs
- 🚀 **CI/CD Ready** - Direct integration with GitHub Actions and other CI systems

## 🎬 Quick Demo

Try Nova on a demo repository with intentionally broken tests:

```bash
# Install Nova
pip install git+https://github.com/novasolve/ci-auto-rescue.git@v0.4.1

# Set your API key
export OPENAI_API_KEY=sk-...  # or ANTHROPIC_API_KEY for Claude

# Fix the demo project
nova fix examples/demos/demo_broken_project
```

Watch as Nova creates a fix branch, analyzes failures, and automatically repairs the tests! 

## 📦 Installation

### From GitHub (Recommended)
```bash
pip install git+https://github.com/novasolve/ci-auto-rescue.git@v0.4.1
```

### For Development
```bash
git clone https://github.com/novasolve/ci-auto-rescue.git
cd ci-auto-rescue
pip install -e .
```

### Requirements
- Python 3.10+
- OpenAI API key (or Anthropic API key for Claude)

## 🚀 Usage

### Basic Usage
```bash
# Fix failing tests in current directory
nova fix .

# Fix with specific parameters
nova fix /path/to/repo --max-iters 5 --timeout 600

# Target specific failing tests
nova fix . --test "test_calculator_multiply"

# Use CI mode (fixes on current branch)
nova fix . --ci
```

### Advanced Options
```bash
nova fix . \
  --whole-file           # Use whole-file replacement mode
  --verbose              # Show detailed execution logs
  --max-iters 10         # Maximum fix attempts
  --timeout 900          # Global timeout in seconds
  --reasoning high       # GPT-5 reasoning effort (low/medium/high)
```

## ⚙️ Configuration

Create a `.env` file in your project root:

```bash
# LLM Configuration
OPENAI_API_KEY=sk-...
# Or use Anthropic
# ANTHROPIC_API_KEY=...
# NOVA_DEFAULT_LLM_MODEL=claude-3-5-sonnet

# Optional: GPT-5 reasoning effort
NOVA_REASONING_EFFORT=high  # low, medium, high

# Optional: Enable telemetry for artifacts
NOVA_ENABLE_TELEMETRY=true
```

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for all options.

## 🛡️ Safety & Limits

Nova includes multiple safety mechanisms:

- **Timeout Protection**: 300s default global timeout
- **Iteration Limits**: Maximum 5 fix attempts by default
- **File Protection**: Cannot modify `.github/`, `setup.py`, `.env`
- **Patch Size Limits**: Maximum 1000 lines per patch
- **Branch Isolation**: Creates isolated `nova-fix/*` branches
- **Automatic Rollback**: Reverts changes on failure

## 📊 Performance

Based on production usage:
- **Success Rate**: 85-95% on Python test failures
- **Average Fix Time**: 15-45 seconds per iteration
- **Cost**: $0.02-0.08 per fix (GPT-5 high reasoning)
- **Token Usage**: ~2-4k tokens per fix attempt

## 🔄 CI/CD Integration

### GitHub Actions
```yaml
- name: Fix failing tests
  if: failure()
  run: |
    pip install git+https://github.com/novasolve/ci-auto-rescue.git@v0.4.1
    nova fix . --ci --max-iters 3
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

### Local Development
```bash
# Install as a development tool
pip install --user git+https://github.com/novasolve/ci-auto-rescue.git@v0.4.1

# Add to your workflow
alias fix-tests='nova fix . --verbose'
```

## 📚 Documentation

- [Quickstart Guide](docs/QUICKSTART.md)
- [Configuration Reference](docs/CONFIGURATION.md)
- [Troubleshooting & FAQ](docs/TROUBLESHOOTING.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Privacy & Security](docs/PRIVACY.md)

## 🤝 Contributing

We welcome contributions! Priority areas:
- Additional language support (JavaScript, Java, Go)
- More test framework integrations
- Performance optimizations
- Documentation improvements

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built with ❤️ by the [NovaSolve](https://github.com/novasolve) team.

Special thanks to our contributors and the open-source community for making this project possible.

---

**Questions?** [Open an issue](https://github.com/novasolve/ci-auto-rescue/issues) or join our [discussions](https://github.com/novasolve/ci-auto-rescue/discussions).

**Ready to get started?** Install Nova and never let failing tests slow you down again! 🚀