# 🚀 Nova CI-Rescue

[![Version](https://img.shields.io/badge/version-v0.1.0--alpha-blue)](https://github.com/nova-solve/ci-auto-rescue/releases)
[![Milestone](https://img.shields.io/badge/milestone-A%20Complete-success)](docs/04-milestone-board.md)
[![Status](https://img.shields.io/badge/status-alpha-orange)](RELEASE_NOTES_v0.1.0-alpha.md)

**Autonomous test fixing powered by Large Language Models**

Nova CI-Rescue automatically detects and fixes failing tests in your repository using GPT-4/5 or Claude. Simply run `nova fix` and watch your tests turn green!

## 🎉 Latest Release: v0.1.0-alpha

**Milestone A Complete!** - Local E2E Happy Path is now fully functional. [Read the full release notes →](RELEASE_NOTES_v0.1.0-alpha.md)

### ✨ Key Features
- 🤖 **Autonomous Agent Loop** - Six-stage workflow: Plan → Generate → Review → Apply → Test → Reflect
- 🧠 **Multi-LLM Support** - Works with OpenAI (GPT-4/5) and Anthropic (Claude 3)
- 🔄 **Git Integration** - Automatic branch creation and commit tracking
- 📊 **Full Telemetry** - Comprehensive logging and artifact storage
- 🛡️ **Safety First** - Built-in critic system and safety caps

## 🚀 Quick Start

### Installation
```bash
# Clone the repository
git clone https://github.com/nova-solve/ci-auto-rescue.git
cd ci-auto-rescue

# Install in development mode
pip install -e .

# Configure API keys
cp env.example .env
# Edit .env with your OpenAI or Anthropic API key
```

### Basic Usage
```bash
# Fix failing tests in current directory
nova fix

# Fix with specific options
nova fix /path/to/repo --max-iters 10 --timeout 1800 --verbose
```

### Demo
```bash
# Run the happy path demo
python demo_happy_path.py
```

## 📋 Current Status

### ✅ Completed (Milestone A)
- Core agent loop implementation
- CLI interface with rich output
- LLM integration (OpenAI & Anthropic)
- Git branch management
- Test runner integration
- Basic telemetry system
- Safety checks and limits

### 🔄 In Progress (Milestone B)
- Quiet pytest defaults for CI
- Enhanced telemetry with artifacts
- Package distribution improvements
- Comprehensive documentation

### 📅 Upcoming (Milestones C & D)
- GitHub Action integration
- PR creation automation
- Multi-language support
- Advanced fix strategies

## 📚 Documentation

### Core Documentation
- [Release Notes v0.1.0-alpha](RELEASE_NOTES_v0.1.0-alpha.md) - Latest release details
- [Implementation Guide](IMPLEMENTATION_GUIDE.md) - Technical deep dive
- [Happy Path Documentation](CI_RESCUE_HAPPY_PATH.md) - Complete specification
- [Action Plan](ACTION_PLAN.md) - Development roadmap
- [Milestone Board](docs/04-milestone-board.md) - Project tracking

### Technical Guides
- [Architecture Overview](docs/02-architecture-diagram.md) - System design
- [Task Dependencies](docs/03-task-dependency-graph.md) - Development flow
- [Quickstart Guide](docs/06-quickstart-guide.md) - Getting started
- [Demo Script](docs/08-demo-script.md) - Running demonstrations

## 🛠️ Configuration

Environment variables (`.env` file):
```bash
# API Keys (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Model Selection
NOVA_DEFAULT_LLM_MODEL=gpt-4o  # or claude-3-5-sonnet

# Limits
NOVA_MAX_ITERS=6
NOVA_RUN_TIMEOUT_SEC=1200
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=nova --cov-report=html

# Run integration test
python demo_happy_path.py
```

## 📊 Performance

- **Success Rate**: 70-85% on simple to moderate failures
- **Fix Time**: 30-60 seconds per iteration
- **Token Usage**: ~2000-4000 tokens per attempt
- **Cost**: ~$0.05 per fix with GPT-4

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) (coming soon).

## 📝 License

This project is currently in development. License information will be added in v1.0.0.

## 🔗 Links

- [Linear Project](https://linear.app/nova-solve/project/ci-rescue-v10-happy-path-536aaf0d73d7) - Task tracking
- [GitHub Issues](https://github.com/nova-solve/ci-auto-rescue/issues) - Bug reports
- [Slite Documentation](https://nova-solve.slite.com) - Team knowledge base

## 🙏 Acknowledgments

Special thanks to the OpenAI, Anthropic, and pytest communities for making this project possible.

---

**Nova CI-Rescue v0.1.0-alpha** - The beginning of autonomous test fixing!

