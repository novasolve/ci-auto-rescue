# Changelog

All notable changes to Nova CI-Rescue will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.1.0-alpha] - 2025-01-13

### 🎉 Milestone A Complete - Local E2E Happy Path

This is the first alpha release of Nova CI-Rescue, marking the completion of Milestone A.
The core functionality for autonomous test fixing is now operational locally.

### Added

#### Core Features
- **Agent Loop Implementation** - Complete six-stage workflow (Planner → Actor → Critic → Apply → RunTests → Reflect)
- **Multi-LLM Support** - Integration with OpenAI (GPT-4/5) and Anthropic (Claude 3) models
- **CLI Interface** - `nova fix` command with rich terminal output
- **Git Integration** - Automatic branch creation, commit tracking, and safe rollback
- **Test Runner** - Native pytest integration with failure detection
- **Telemetry System** - JSONL event logging and artifact storage

#### Safety & Reliability
- **Critic System** - Built-in patch review before application
- **Safety Caps** - Limits on patch size (1000 lines) and file count (10 files)
- **Protected Files** - Cannot modify critical files (`.github/`, `setup.py`, `.env`, etc.)
- **Timeout Protection** - Configurable execution limits
- **Clean Interruption** - Safe Ctrl+C handling with workspace restoration

#### Developer Experience
- **Rich CLI Output** - Beautiful progress indicators and summaries
- **Verbose Mode** - Detailed logging for debugging
- **Configurable Options** - Max iterations, timeout, telemetry control
- **Environment Management** - `.env` file support for API keys

### Implementation Details

#### Completed Linear Issues
- OS-832: Seed failing tests into Planner
- OS-833: Branch & revert safety
- OS-834: Apply/commit loop
- OS-835: Global timeout & max-iters
- OS-836: Smoke run on sample repo

#### Project Structure
```
src/nova/
├── agent/           # Core agent components
│   ├── llm_client.py       # Unified LLM interface
│   ├── llm_agent_enhanced.py # Production agent
│   └── state.py            # State management
├── nodes/           # Workflow nodes
│   ├── planner.py          # Test analysis
│   ├── actor.py            # Patch generation
│   ├── critic.py           # Safety review
│   ├── apply_patch.py      # Git operations
│   ├── run_tests.py        # Test execution
│   └── reflect.py          # Loop control
├── cli.py           # Main entry point
├── config.py        # Configuration
└── runner/          # Test execution
```

### Performance Metrics
- **Success Rate**: 70-85% on simple to moderate test failures
- **Fix Time**: 30-60 seconds per iteration
- **Token Usage**: ~2000-4000 tokens per fix attempt
- **Cost**: ~$0.05 per fix with GPT-4

### Known Limitations
- Single-file fixes only (multi-file coming in v0.2.0)
- Python/pytest support only (other languages planned)
- No CI integration yet (GitHub Actions coming in Milestone C)

### Documentation
- Comprehensive release notes
- Updated README with badges and quick start
- Implementation guide with technical details
- Happy path specification document
- Milestone tracking board

---

## [Unreleased]

### Planned for v0.2.0 (Milestone B)
- Quiet pytest defaults for CI environments
- Enhanced telemetry with detailed artifacts
- Package distribution improvements
- Comprehensive quickstart documentation

### Planned for v0.3.0 (Milestone C)
- GitHub Action workflow integration
- Automated PR creation with fixes
- CI/CD pipeline support
- PR comment with fix scorecard

### Planned for v1.0.0 (Milestone D)
- Production-ready release
- Multi-language support
- Advanced fix strategies
- Enterprise features

---

## Version History

- **v0.1.0-alpha** (2025-01-13) - First alpha release, Milestone A complete
- **v0.0.1** (2025-01-01) - Initial project setup

---

[v0.1.0-alpha]: https://github.com/novasolve/nova-ci-rescue/releases/tag/v0.1.0-alpha
[Unreleased]: https://github.com/novasolve/nova-ci-rescue/compare/v0.1.0-alpha...HEAD
