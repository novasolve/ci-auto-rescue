# Nova CI-Rescue Project Structure

## 📁 Directory Overview

```
nova-ci-rescue/
├── 📦 src/nova/                 # Core library code
│   ├── agent/                   # LLM agent implementations
│   ├── nodes/                   # Workflow nodes (planner, actor, critic)
│   ├── runner/                  # Test execution framework
│   ├── telemetry/              # Telemetry and logging
│   ├── tools/                   # Utilities (git, fs, sandbox)
│   ├── cli.py                   # Command-line interface
│   └── config.py               # Configuration management
│
├── 🧪 tests/                    # Test suite
│   ├── test_*.py               # Unit and integration tests
│   └── nova_smoke_test.py      # Smoke tests
│
├── 📚 docs/                     # Documentation
│   ├── archive/                # Archived/old documentation
│   ├── development/            # Development notes and guides
│   ├── QUICKSTART.md          # Getting started guide
│   ├── INSTALLATION.md        # Installation instructions
│   ├── CONFIGURATION.md       # Configuration reference
│   └── TROUBLESHOOTING.md     # FAQ and troubleshooting
│
├── 🎯 examples/demos/           # Example projects and demos
│   ├── demo_broken_project/    # Sample failing project
│   ├── scripts/                # Demo scripts
│   └── nova-demo-repo/         # Full demo repository
│
├── 🔧 patches/                  # Sample patches and improvements
│
├── 🚀 github-app/              # GitHub App integration
│
├── 📜 scripts/                  # Development and utility scripts
│
└── 📄 Root Files
    ├── README.md               # Project overview and quickstart
    ├── pyproject.toml          # Project configuration
    ├── poetry.lock             # Dependency lock file
    ├── LICENSE                 # MIT license
    └── CHANGELOG.md            # Version history
```

## 🗂️ Key Components

### Core Library (`src/nova/`)

- **`agent/`** - Contains the LLM agent logic for analyzing and fixing code
- **`nodes/`** - Implements the Planner → Actor → Critic workflow
- **`runner/`** - Handles test execution and result parsing
- **`tools/`** - Provides utilities for Git operations, file system access, and sandboxing

### Documentation (`docs/`)

- **User Guides** - Quickstart, installation, and configuration docs
- **Development** - Internal development notes and implementation details
- **Archive** - Historical documentation for reference

### Examples (`examples/demos/`)

- **Demo Projects** - Various broken projects to test Nova's capabilities
- **Scripts** - Demonstration scripts showing Nova in action

## 🔍 Important Files

| File | Description |
|------|-------------|
| `src/nova/cli.py` | Main entry point for the `nova` command |
| `src/nova/config.py` | Environment variable and configuration handling |
| `pyproject.toml` | Project metadata and dependencies |
| `.env.example` | Example environment configuration |

## 🚦 Getting Started

1. Install Nova: `pip install nova-ci-rescue`
2. Set up your API key: `export OPENAI_API_KEY=sk-...`
3. Try the demo: `nova fix examples/demos/demo_broken_project`

For more details, see the [Quickstart Guide](QUICKSTART.md).
