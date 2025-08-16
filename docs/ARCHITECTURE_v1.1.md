# Nova CI-Rescue v1.1 - Deep Agent Architecture

## Overview

Nova CI-Rescue v1.1 represents a fundamental architectural shift from a multi-node pipeline to an intelligent, unified Deep Agent powered by LangChain. This document details the new architecture, its components, and how they work together to fix failing tests.

## Core Architecture

### The Deep Agent

At the heart of v1.1 is the **NovaDeepAgent**, a sophisticated LangChain-based agent that uses ReAct (Reasoning and Acting) patterns to autonomously fix failing tests.

```
┌──────────────────────────────────────────────────┐
│                 NovaDeepAgent                    │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │         LangChain AgentExecutor            │ │
│  │                                            │ │
│  │  ┌─────────────┐      ┌────────────────┐  │ │
│  │  │   LLM       │◄────►│  ReAct Loop    │  │ │
│  │  │  (GPT-4/    │      │                │  │ │
│  │  │  Claude)    │      │  Reason→Act→   │  │ │
│  │  └─────────────┘      │  Observe→Loop  │  │ │
│  │                       └────────────────┘  │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │           Unified Tool System              │ │
│  └────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

### Key Components

#### 1. LangChain AgentExecutor

The AgentExecutor manages the agent's reasoning loop:
- **Input Processing**: Receives test failures and context
- **Tool Selection**: Decides which tools to use based on the situation
- **Execution Management**: Handles tool execution and result processing
- **Iteration Control**: Manages the reasoning loop until success or limits

#### 2. ReAct Loop

The agent follows a Reasoning-Acting-Observing pattern:

1. **Reason**: Analyze the current situation and plan next steps
2. **Act**: Select and execute appropriate tools
3. **Observe**: Process tool results and assess progress
4. **Loop**: Continue until tests pass or limits reached

Example reasoning trace:
```
Thought: I need to understand why test_calculator is failing
Action: open_file
Action Input: {"path": "tests/test_calculator.py"}
Observation: [file contents showing assertion error]

Thought: The test expects add(2,3) to return 5, let me check the implementation
Action: open_file
Action Input: {"path": "src/calculator.py"}
Observation: [file contents showing bug in add function]

Thought: I found the issue - the add function has a typo. I'll fix it.
Action: write_file
Action Input: {"path": "src/calculator.py", "content": "[corrected code]"}
Observation: File written successfully

Thought: Let me run the tests to verify the fix
Action: run_tests
Action Input: {}
Observation: All tests passing!
```

#### 3. Unified Tool System

The Deep Agent uses a comprehensive set of tools:

##### File Operations Tools

**`open_file`**
- Reads file contents with safety checks
- Blocks access to sensitive files (.env, secrets, etc.)
- Returns file content for agent analysis

**`write_file`**
- Writes content to files with validation
- Enforces safety limits (file size, allowed paths)
- Creates necessary directories

##### Testing Tools

**`run_tests`**
- Executes pytest with proper isolation
- Captures detailed failure information
- Returns structured test results

##### Patch Management Tools

**`apply_patch`**
- Applies git-format patches safely
- Validates patch before application
- Handles merge conflicts gracefully

**`critic_review`**
- Reviews patches for safety and correctness
- Uses LLM to assess patch quality
- Enforces safety policies (size limits, scope restrictions)

##### Planning Tools

**`plan_todo`**
- Helps agent organize approach
- Tracks multi-step plans
- (Currently a stub for future enhancement)

### Safety Architecture

```
┌─────────────────────────────────────────┐
│           Safety Layers                 │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   1. Tool-Level Safety            │ │
│  │   - Path restrictions              │ │
│  │   - Size limits                    │ │
│  │   - Content validation             │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   2. Critic Review                │ │
│  │   - Semantic patch analysis        │ │
│  │   - Change scope assessment        │ │
│  │   - Risk evaluation                │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   3. Application Guards            │ │
│  │   - Pre-flight checks               │ │
│  │   - Git validation                 │ │
│  │   - Rollback capability            │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## Execution Flow

### 1. Initialization Phase

```python
# CLI creates Deep Agent with context
deep_agent = NovaDeepAgent(
    state=agent_state,
    telemetry=logger,
    git_manager=git_manager,
    safety_config=safety_config
)
```

### 2. Agent Execution

The agent receives:
- **failures_summary**: Table of failing tests
- **error_details**: Detailed error messages
- **code_snippets**: Relevant source code (optional)

```python
success = deep_agent.run(
    failures_summary=failures_summary,
    error_details=error_details,
    code_snippets=code_snippets
)
```

### 3. Internal Agent Loop

```
START
  │
  ▼
┌─────────────────┐
│ Analyze Failures│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Plan Approach  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Explore Codebase│◄──────┐
└────────┬────────┘       │
         │                │
         ▼                │
┌─────────────────┐       │
│ Generate Fix    │       │
└────────┬────────┘       │
         │                │
         ▼                │
┌─────────────────┐       │
│  Review Patch   │       │
└────────┬────────┘       │
         │                │
         ▼                │
┌─────────────────┐       │
│  Apply Patch    │       │
└────────┬────────┘       │
         │                │
         ▼                │
┌─────────────────┐       │
│   Run Tests     │       │
└────────┬────────┘       │
         │                │
         ▼                │
    ┌────────┐            │
    │Success?│────No──────┘
    └───┬────┘
        │Yes
        ▼
       END
```

## Comparison with v1.0

### v1.0 Multi-Node Pipeline

```
Planner → Actor → Critic → Apply → Test → Reflect
  (Each node is a separate component with limited context)
```

**Limitations**:
- Fixed execution order
- Limited context between nodes
- No ability to adapt strategy
- Rigid retry logic

### v1.1 Deep Agent

```
Unified Agent with Dynamic Tool Selection
  (Single agent maintains full context and chooses actions)
```

**Advantages**:
- Flexible execution based on reasoning
- Full context throughout process
- Adaptive strategy based on observations
- Intelligent retry with different approaches

## Configuration

### Agent Configuration

```yaml
# nova.config.yml
model: gpt-4              # LLM model
agent_temperature: 0.1    # Lower = more deterministic
agent_max_steps: 50       # Max steps per iteration
max_iterations: 6         # Max fix attempts
```

### Safety Configuration

```yaml
# Safety limits
max_patch_lines: 500      # Maximum lines in a patch
max_affected_files: 10    # Maximum files per patch
blocked_paths:            # Paths agent cannot modify
  - .github/
  - .env
  - secrets/
  - deployment/
```

## Tool Implementation Details

### Tool Registration

Tools are registered with the agent during initialization:

```python
def create_default_tools(repo_path, safety_config):
    tools = [
        Tool(name="open_file", func=open_file_tool),
        Tool(name="write_file", func=write_file_tool),
        Tool(name="run_tests", func=run_tests_tool),
        Tool(name="apply_patch", func=apply_patch_tool),
        Tool(name="critic_review", func=critic_review_tool),
    ]
    return tools
```

### Tool Interface

Each tool follows a standard interface:

```python
def tool_function(input_str: str) -> str:
    """
    Tool implementation.
    
    Args:
        input_str: JSON string with tool parameters
    
    Returns:
        String result for agent to observe
    """
    params = json.loads(input_str)
    # Tool logic here
    return result_string
```

## Performance Characteristics

### Reasoning Overhead

The Deep Agent adds ~2-5 seconds of reasoning time per action but makes better decisions, resulting in:
- Fewer overall iterations needed
- Better first-attempt success rate
- More intelligent error recovery

### Resource Usage

- **Memory**: ~500MB for agent and LLM context
- **API Calls**: 5-15 LLM calls per iteration
- **Disk I/O**: Minimal, only for file operations
- **CPU**: Light usage, mainly for test execution

## Advanced Features

### Context Window Management

The agent intelligently manages its context window:
- Summarizes long file contents
- Focuses on relevant code sections
- Maintains essential context across iterations

### Multi-Step Planning

The agent can plan complex multi-step fixes:
1. Identify root cause across multiple files
2. Fix primary issue
3. Update dependent code
4. Verify all tests pass

### Self-Correction

When a fix doesn't work, the agent:
- Analyzes why the fix failed
- Adjusts its approach
- Tries alternative solutions
- Learns from previous attempts

## Integration Points

### CLI Integration

The CLI initializes and runs the Deep Agent:

```python
# src/nova/cli.py
deep_agent = NovaDeepAgent(state=state, ...)
success = deep_agent.run(...)
```

### Telemetry Integration

All agent actions are logged:
- Tool invocations
- Reasoning traces
- Patch generation
- Test results

### Git Integration

The agent works with GitBranchManager:
- Creates fix branches
- Commits successful patches
- Manages working directory state

## Future Enhancements

### Planned Improvements

1. **Enhanced Planning**: More sophisticated multi-step planning
2. **Code Understanding**: Better semantic code analysis
3. **Learning**: Agent learns from successful fixes
4. **Parallelization**: Run multiple fix attempts in parallel
5. **Custom Tools**: Plugin system for domain-specific tools

### Extension Points

The architecture is designed for extension:
- Add new tools by implementing the tool interface
- Customize safety policies via configuration
- Integrate alternative LLMs
- Add specialized reasoning strategies

## Conclusion

The v1.1 Deep Agent architecture represents a significant advancement in automated test fixing:

- **Intelligence**: ReAct-style reasoning for better decision-making
- **Flexibility**: Dynamic tool selection based on context
- **Reliability**: Multiple safety layers and validation
- **Performance**: Higher success rates with fewer iterations
- **Extensibility**: Clean architecture for future enhancements

This architecture positions Nova CI-Rescue as a truly intelligent coding assistant capable of complex problem-solving while maintaining safety and reliability.
