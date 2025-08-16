# Nova CI-Rescue: Migration to LangChain Deep Agent Architecture

## Overview

Nova CI-Rescue has been redesigned from a multi-node pipeline architecture to a unified LangChain Deep Agent approach. This migration brings improved reliability, simpler maintenance, and better extensibility.

## Architecture Comparison

### Previous Architecture (v0.2.0-legacy)

```
┌─────────┐    ┌───────┐    ┌────────┐    ┌─────────┐
│ Planner │ -> │ Actor │ -> │ Critic │ -> │ Reflect │
└─────────┘    └───────┘    └────────┘    └─────────┘
     ↓             ↓            ↓              ↓
  [State]      [State]      [State]       [State]
```

**Components:**

- **Planner**: Analyzed failures and created fix strategies
- **Actor**: Applied code modifications
- **Critic**: Reviewed patches for safety
- **Reflect**: Handled iteration logic
- **State Management**: Complex state passing between nodes

### New Architecture (v0.3.0+)

```
┌─────────────────────────────────┐
│     LangChain Deep Agent        │
│  ┌─────────────────────────┐    │
│  │ Tools: plan, read,      │    │
│  │ write, test             │    │
│  └─────────────────────────┘    │
└─────────────────────────────────┘
           ↓
    [Critic Review]
           ↓
    [Git Operations]
```

**Components:**

- **Deep Agent**: Single intelligent agent with tool access
- **Agent Tools**: Modular tools for planning, file I/O, and testing
- **Critic Module**: Streamlined patch review
- **Sandbox**: Docker-based test isolation

## Key Improvements

### 1. Simplified Architecture

- **Before**: Complex multi-node pipeline with state management
- **After**: Single agent with direct tool access

### 2. Better Tool Integration

- **Before**: Custom tool implementations scattered across nodes
- **After**: Centralized tool definitions with clear interfaces

### 3. Enhanced Reliability

- **Before**: State synchronization issues between nodes
- **After**: Stateless tool calls with consistent behavior

### 4. Improved Maintainability

- **Before**: Complex node interactions to debug
- **After**: Linear agent execution with clear tool usage

## Migration Steps

### Step 1: Install Dependencies

```bash
# Update dependencies
pip install --upgrade pip
pip install langchain langchain-openai openai pytest-timeout

# Or use poetry
poetry update
```

### Step 2: Set Environment Variables

```bash
# Required for OpenAI-based agent
export OPENAI_API_KEY='your-api-key-here'
```

### Step 3: Build Sandbox Image

```bash
# Build the Docker sandbox for test isolation
cd src/nova_deep_agent/sandbox
bash build.sh
```

### Step 4: Update Code References

If you have code that imports from the old structure:

```python
# Old import
from nova.agent.llm_agent import LLMAgent
from nova.nodes.planner import PlannerNode

# New import
from nova_deep_agent.agent import DeepAgent
from nova_deep_agent.pipeline import CIRescuePipeline
```

## Usage Comparison

### Old CLI Usage

```bash
# Old multi-node pipeline
nova fix --repo /path/to/repo
```

### New CLI Usage

```bash
# New deep agent
nova-deep fix --repo /path/to/repo --model gpt-4 --auto-commit
```

### Programmatic Usage

**Old Approach:**

```python
from nova.runner import TestRunner
from nova.nodes import PlannerNode, ActorNode, CriticNode

# Complex initialization
runner = TestRunner(repo_path)
planner = PlannerNode()
actor = ActorNode()
critic = CriticNode()

# Multi-step execution
plan = planner.execute(failing_tests)
patch = actor.execute(plan)
review = critic.execute(patch)
```

**New Approach:**

```python
from nova_deep_agent import DeepAgent
from nova_deep_agent.pipeline import CIRescuePipeline

# Simple initialization
pipeline = CIRescuePipeline(auto_commit=True)

# Single-step execution
results = pipeline.run()
```

## Configuration Changes

### Old Configuration (YAML-based)

```yaml
# config.yaml
planner:
  model: gpt-4
  temperature: 0.1
actor:
  max_retries: 3
critic:
  safety_checks: true
```

### New Configuration (Python-based)

```python
from nova_deep_agent.agent import AgentConfig

config = AgentConfig(
    model_name="gpt-4",
    temperature=0.0,
    max_iterations=5,
    max_patch_lines=1000
)
```

## Feature Mapping

| Old Feature      | New Implementation | Notes                                |
| ---------------- | ------------------ | ------------------------------------ |
| Planner Node     | `plan_todo_tool`   | Integrated as agent tool             |
| Actor Node       | Deep Agent core    | Agent handles modifications directly |
| Critic Node      | `Critic` class     | Streamlined review process           |
| Reflect Node     | Pipeline loop      | Built into pipeline iteration        |
| State Management | Stateless tools    | No complex state passing             |
| Test Runner      | `run_tests_tool`   | Docker-based isolation               |

## Breaking Changes

1. **API Changes**: The old node-based API is no longer available
2. **Config Format**: YAML configuration replaced with Python dataclasses
3. **State Management**: No longer uses LangGraph state graphs
4. **Import Paths**: All imports now under `nova_deep_agent` package

## Rollback Instructions

If you need to use the legacy version:

```bash
# The old code is preserved in releases/v0.2.0-legacy/
cd releases/v0.2.0-legacy/

# Install legacy dependencies
pip install -r requirements.txt

# Use the legacy CLI
python -m nova.cli fix --repo /path/to/repo
```

## Performance Considerations

- **Latency**: Single agent calls may have higher latency than parallel nodes
- **Token Usage**: Deep agent may use more tokens for complex reasoning
- **Caching**: Consider implementing result caching for repeated operations

## Troubleshooting

### Issue: "OPENAI_API_KEY not set"

**Solution**: Export your OpenAI API key:

```bash
export OPENAI_API_KEY='sk-...'
```

### Issue: "Docker sandbox not found"

**Solution**: Build the sandbox image:

```bash
cd src/nova_deep_agent/sandbox
bash build.sh
```

### Issue: Import errors with old code

**Solution**: Update imports to use `nova_deep_agent` package

## Support

For issues or questions about the migration:

1. Check the migration guide examples
2. Review the new API documentation
3. File an issue on GitHub

## Future Roadmap

- **v0.3.1**: Performance optimizations
- **v0.3.2**: Additional agent tools
- **v0.4.0**: Multi-agent collaboration
- **v0.5.0**: Advanced reasoning capabilities

---

_Last updated: January 2025_
