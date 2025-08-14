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

## 🚀 Local Quickstart Guide

**Get Nova CI-Rescue running in ≤15 minutes!** Follow these 10 steps to fix your first failing test automatically.

### Step 1: Prerequisites Check (1 min)

Verify you have the required tools installed:

```bash
# Check Python version (3.10+ required)
python3 --version

# Check pip is installed
pip3 --version

# Check git is installed
git --version
```

**Troubleshooting:**

- **Python < 3.10?** Install via [python.org](https://python.org) or use `pyenv`/`conda`
- **pip missing?** Run `python3 -m ensurepip --upgrade`
- **git missing?** Install from [git-scm.com](https://git-scm.com)

### Step 2: Clone & Setup (2 min)

```bash
# Clone the repository
git clone https://github.com/nova-solve/ci-auto-rescue.git
cd ci-auto-rescue

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Troubleshooting:**

- **Permission denied?** Use `git clone https://` instead of `git@`
- **venv fails?** Try `python3 -m pip install --user virtualenv` first
- **Windows?** Use Git Bash or WSL for best compatibility

### Step 3: Install Dependencies (2 min)

```bash
# Install Nova in development mode
pip install -e .

# Verify installation
nova --version
```

**Troubleshooting:**

- **Installation fails?** Update pip first: `pip install --upgrade pip setuptools wheel`
- **Command not found?** Ensure venv is activated or use `python -m nova.cli`
- **SSL errors?** Add `--trusted-host pypi.org --trusted-host files.pythonhosted.org`

### Step 4: Configure API Keys (2 min)

```bash
# Copy environment template
cp env.example .env

# Edit .env file (use your preferred editor)
nano .env  # or vim, code, notepad, etc.
```

Add ONE of these API keys (get free trials):

```bash
# Option A: OpenAI (Recommended for beginners)
OPENAI_API_KEY=sk-proj-xxxxx...
# Get key at: https://platform.openai.com/api-keys

# Option B: Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-xxxxx...
# Get key at: https://console.anthropic.com/settings/keys
```

**Troubleshooting:**

- **No API key?** OpenAI offers $5 free credits for new accounts
- **Key not working?** Check for extra spaces/quotes, key should start with `sk-`
- **Budget concerns?** Set `NOVA_DEFAULT_LLM_MODEL=gpt-4o-mini` for lowest cost

### Step 5: Test Installation (1 min)

```bash
# Verify Nova can read your config
nova config

# Should output:
# ✅ API Key: Configured (OpenAI/Anthropic)
# ✅ Model: gpt-4o-mini
# ✅ Max Iterations: 6
# ✅ Timeout: 1200s
```

**Troubleshooting:**

- **API key not found?** Check `.env` is in project root, not in `src/`
- **Config command fails?** Try `export OPENAI_API_KEY=sk-...` directly
- **Permission issues?** Ensure `.env` is readable: `chmod 644 .env`

### Step 6: Run Demo Test (3 min)

Try the built-in demo first:

```bash
# Run the happy path demo
python demo_happy_path.py

# Expected output:
# Nova CI-Rescue Happy Path Demo
# ✓ LLM Agent initialized
# ✓ Created branch: nova-fix-20250115-123456
# Found 3 failing test(s)
# ...
# ✅ HAPPY PATH COMPLETE - All tests fixed!
```

**Troubleshooting:**

- **Import errors?** Ensure you're in the project root and venv is active
- **API errors?** Check your API key has credits/is valid
- **Timeout?** Demo should complete in 30-60 seconds with good connection

### Step 7: Prepare Your Repository (1 min)

For your own repository:

```bash
# Navigate to your project
cd /path/to/your/project

# Ensure you have pytest installed
pip install pytest

# Create a backup branch (safety first!)
git checkout -b backup-before-nova
git checkout -
```

**Troubleshooting:**

- **No tests?** Nova works with pytest test files (`test_*.py` or `*_test.py`)
- **Different test framework?** Currently only pytest is supported
- **Uncommitted changes?** Commit or stash them first: `git stash`

### Step 8: Run Nova on Your Code (2 min)

```bash
# Basic usage - fix all failing tests
nova fix

# Or specify path and options
nova fix . --max-iters 3 --timeout 300 --verbose

# Monitor progress
# You'll see:
# 🔍 Running initial tests...
# 📝 Planning fixes...
# 🔧 Applying patches...
# ✅ Tests passing!
```

**Troubleshooting:**

- **No failing tests found?** Run `pytest` first to confirm failures exist
- **Takes too long?** Reduce iterations: `--max-iters 2`
- **Too many changes?** Limit scope: `nova fix tests/test_specific.py`

### Step 9: Review Changes (1 min)

```bash
# See what Nova changed
git diff

# Check test results
pytest

# View detailed logs
cat telemetry/latest/trace.jsonl | jq '.'  # Pretty print JSON logs
```

**Troubleshooting:**

- **Don't like changes?** Reset: `git checkout -- .` or `git reset --hard HEAD`
- **Partially working?** Re-run Nova with `--continue` flag
- **Want to keep some changes?** Use `git add -p` for selective staging

### Step 10: Commit or Rollback (1 min)

```bash
# Option A: Keep the fixes
git add -A
git commit -m "fix: Auto-fixed failing tests via Nova CI-Rescue"

# Option B: Discard changes
git reset --hard HEAD
git clean -fd
```

**Troubleshooting:**

- **Branch issues?** Nova creates branches like `nova-fix-TIMESTAMP`
- **Merge conflicts?** Nova's branch is based on your current HEAD
- **CI integration?** See [CI Integration Guide](docs/08-demo-script.md)

---

### 🎯 Quick Success Test

For immediate success verification, run our quickstart test:

```bash
# Run the automated quickstart test
python quickstart_test.py

# This script will:
# 1. Create a test project with intentional bugs
# 2. Run Nova to fix them automatically
# 3. Verify all tests pass after fixing
# 4. Clean up temporary files
```

Or try this minimal manual example:

```bash
# Create test file with intentional bug
cat > test_sample.py << 'EOF'
def add(a, b):
    return a + b + 1  # Bug: adds extra 1

def test_add():
    assert add(2, 3) == 5  # Will fail: gets 6
EOF

# Run Nova to fix it
nova fix --max-iters 1

# Verify fix
python -m pytest test_sample.py  # Should pass!
```

### ⚡ Performance Tips

- **Faster runs:** Use `gpt-4o-mini` model (5-10x faster than gpt-4o)
- **Reduce tokens:** Add `--concise` flag for shorter responses
- **Local caching:** Reuse telemetry with `--cache` flag
- **Parallel tests:** Use `pytest -n auto` for faster test execution

### 🚨 Common Issues & Solutions

| Issue                     | Solution                                     |
| ------------------------- | -------------------------------------------- |
| "API rate limit exceeded" | Wait 60s or switch API keys                  |
| "No module named 'nova'"  | Activate venv: `source venv/bin/activate`    |
| "Permission denied"       | Check file permissions: `ls -la`             |
| "Git uncommitted changes" | Stash: `git stash` or commit changes         |
| "Tests still failing"     | Increase iterations: `--max-iters 10`        |
| "Out of memory"           | Limit test scope or use smaller model        |
| "Connection timeout"      | Check internet/firewall, use `--timeout 600` |

### 📚 Next Steps

- Read [Full Documentation](docs/06-quickstart-guide.md)
- Try [Advanced Examples](docs/08-demo-script.md)
- Join [Discord Community](https://discord.gg/nova-solve)
- Report issues on [GitHub](https://github.com/nova-solve/ci-auto-rescue/issues)

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
