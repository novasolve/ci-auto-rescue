# Nova CI-Rescue: Updated to Match Specification

## Overview

The Nova CI-Rescue implementation has been updated to exactly match the provided LangChain Deep Agent specification. This includes:

1. **LangChain Tools with @tool decorator**
2. **NovaDeepAgent class** integrating with existing Nova components
3. **Docker sandbox** with enhanced security
4. **Orchestration loop** matching the pseudo-code specification

## Key Components Updated

### 1. Agent Tools (`src/nova/agent/tools.py`)

Four tools using LangChain's `@tool` decorator:

```python
@tool("plan_todo", return_direct=True)
def plan_todo(todo: str) -> str:
    """Plan next steps - no-op that records the plan"""

@tool("open_file", return_direct=True)
def open_file(path: str) -> str:
    """Read file contents with safety checks"""

@tool("write_file", return_direct=True)
def write_file(path: str, new_content: str) -> str:
    """Write to files with safety checks"""

@tool("run_tests", return_direct=True)
def run_tests() -> str:
    """Run tests in Docker sandbox, return JSON results"""
```

**Key Features:**

- Pattern-based file blocking (`tests/*`, `.env`, `.git/*`, `secrets/*`)
- Docker sandbox with resource limits (1 CPU, 1GB RAM, 256 PID limit)
- JSON output from test runs
- 600-second timeout

### 2. NovaDeepAgent Class (`src/nova/agent/deep_agent.py`)

Integrates with existing Nova architecture:

```python
class NovaDeepAgent:
    def __init__(self, state: AgentState, telemetry: JSONLLogger, ...):
        # Uses existing Nova components
        self.state = state
        self.telemetry = telemetry
        self.git_manager = git_manager
        self.legacy_agent = LLMAgent(state.repo_path)  # For critic review
```

**Integration Points:**

- Uses `AgentState` for tracking iterations and failures
- Logs events to `JSONLLogger` telemetry
- Leverages existing `GitBranchManager` for version control
- Falls back to `LLMAgent` for critic review

### 3. Docker Sandbox (`docker/`)

Enhanced security configuration:

```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
WORKDIR /workspace
ENTRYPOINT ["python", "/usr/local/bin/run_python.py"]
```

**Docker Run Command:**

```bash
docker run --rm \
  -v "${repo_path}:/workspace:ro" \        # Read-only code mount
  -v "${nova_path}:/workspace/.nova:rw" \  # Writable test reports
  --memory "1g" \                          # Memory limit
  --cpus "1.0" \                          # CPU limit
  --network "none" \                       # No network access
  --pids-limit "256" \                     # Process limit
  nova-ci-rescue-sandbox:latest --pytest
```

### 4. Orchestration Loop (`src/nova/orchestrator.py`)

Matches the provided pseudo-code exactly:

```python
for iteration in range(1, max_iters+1):
    # 1. Planner: analyze test failures and strategy
    failing_tests = gather_failing_tests()
    plan_notes = Planner.plan(failing_tests)

    # 2. Deep Agent: attempt fix with tools
    agent.run(user_prompt)

    # 3. Collect diff of changes
    diff = get_git_diff()

    # 4. Critic review
    critic_verdict = Critic.review(diff)
    if critic_verdict == "reject" or patch_too_large(diff):
        rollback_working_copy()
        continue

    # 5. Apply patch
    git_add_all()
    git_commit(f"Nova DeepAgent fix iteration {iteration}")

    # 6. Verify tests
    final_results = run_tests_in_sandbox()
    if final_results.all_passed:
        break
```

## Usage

### Building the Docker Sandbox

```bash
cd docker/
bash build.sh
```

### Running the Deep Agent

```python
from nova.agent.deep_agent import NovaDeepAgent
from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger

# Initialize components
state = AgentState(repo_path="/path/to/repo")
telemetry = JSONLLogger()

# Create and run agent
deep_agent = NovaDeepAgent(state, telemetry, verbose=True)
success = deep_agent.run(
    failures_summary="test_calc.py::test_add - AssertionError",
    error_details="Expected 5 but got 6",
    code_snippets=""
)
```

### CLI Integration

The deep agent can be integrated into the existing CLI:

```python
# In src/nova/cli.py (after gathering failing tests)
from nova.agent.deep_agent import NovaDeepAgent

deep_agent = NovaDeepAgent(state, telemetry, git_manager, verbose, safety_config)
success = deep_agent.run(failures_table, error_details, code_snippets)
```

## Differences from Original Implementation

| Component       | Original                              | Updated                                     |
| --------------- | ------------------------------------- | ------------------------------------------- |
| Tool Definition | Regular functions with `Tool` wrapper | `@tool` decorator with `return_direct=True` |
| File Protection | Substring checks                      | Pattern matching with `Path.match()`        |
| Docker Security | Basic isolation                       | Added `--pids-limit 256`                    |
| Agent Class     | Standalone `DeepAgent`                | `NovaDeepAgent` integrated with Nova        |
| Orchestration   | Pipeline class                        | Explicit loop matching pseudo-code          |
| System Prompt   | Generic fixing prompt                 | Specific ReAct-style prompt                 |

## Environment Setup

### Required Environment Variables

```bash
export OPENAI_API_KEY="sk-..."  # For GPT-4 model
```

### Python Dependencies

```bash
pip install langchain langchain-openai openai
```

### Docker Setup

```bash
# Build sandbox image
cd docker/
docker build -t nova-ci-rescue-sandbox:latest .

# Test the sandbox
docker run --rm nova-ci-rescue-sandbox:latest --pytest
```

## Testing

### Unit Test for Tools

```python
from nova.agent.tools import plan_todo, open_file, write_file, run_tests

# Test planning tool
result = plan_todo("Fix calculator add function")
assert "Plan noted:" in result

# Test file operations
content = open_file("src/calculator.py")
assert "ERROR" not in content or "not found" in content

# Test Docker sandbox
test_results = run_tests()
import json
results = json.loads(test_results)
assert "exit_code" in results
```

## Safety Features

1. **File Protection**: Blocks access to sensitive paths

   - Test files (`tests/*`)
   - Environment files (`.env`)
   - Git internals (`.git/*`)
   - Secrets (`secrets/*`)

2. **Docker Isolation**:

   - Read-only code mount
   - No network access
   - Resource limits (CPU, memory, PIDs)
   - Timeout protection

3. **Patch Review**:
   - Critic LLM review before applying
   - Size limits enforcement
   - Safety configuration checks

## Migration Notes

To migrate from the previous implementation:

1. Replace `src/nova_deep_agent/` with the new `src/nova/agent/` components
2. Update imports to use `nova.agent.deep_agent.NovaDeepAgent`
3. Build the new Docker image from `docker/` directory
4. Update CLI to use the new orchestrator loop

## Next Steps

1. Test with real failing repositories
2. Fine-tune the system prompt for better results
3. Add caching for faster iterations
4. Implement additional safety checks
5. Add metrics and monitoring

---

_Updated to match specification: January 2025_
