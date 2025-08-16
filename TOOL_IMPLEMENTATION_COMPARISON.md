# Tool Implementation Deep Dive: Detailed Comparison

## Overview

This document provides a detailed technical comparison of tool implementations between the provided LangChain-based code and the existing Nova CI-Rescue codebase.

## 1. Test Execution Tools

### Provided: RunTestsTool

```python
def _run_tests_tool_func(input_text: str = "") -> str:
    # Execute tests and update AgentState
    result = run_tests(self.state, self.telemetry, self.repo_path, verbose=self.verbose)
    if "error" in result:
        return f"Test run failed: {result.get('error')}"

    failure_count = result.get("failure_count", 0)
    if failure_count == 0:
        self.state.final_status = "success"
        return "All tests passed."

    # Format failing tests for agent observation
    failing_list = result.get("failing_tests", [])
    obs_lines = [f"{failure_count} tests failing:"]
    for test in failing_list[:5]:
        name = test.get("name") or "unknown"
        error_msg = (test.get("short_traceback") or "").split('\n')[0]
        if len(error_msg) > 100:
            error_msg = error_msg[:100] + "..."
        obs_lines.append(f"- {name}: {error_msg}")
    return "\n".join(obs_lines)
```

**Key Features:**

- Integrates with AgentState for tracking
- Returns human-readable summary
- Updates state.final_status on success
- Limits output to 5 failures for clarity

### Existing: run_tests Tool

```python
@tool("run_tests", return_direct=True)
def run_tests() -> str:
    """Run the project's test suite inside a Docker container."""
    if shutil.which("docker") is None:
        return json.dumps({"error": "Docker is not available", "exit_code": 127})

    repo_path = Path(".").resolve()
    nova_path = repo_path / ".nova"
    nova_path.mkdir(exist_ok=True)

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{repo_path}:/workspace:ro",
        "-v", f"{nova_path}:/workspace/.nova:rw",
        "--memory", MEM_LIMIT,
        "--cpus", CPU_LIMIT,
        "--network", "none",
        "--pids-limit", PID_LIMIT,
        DOCKER_IMAGE,
        "python", "/usr/local/bin/run_python.py", "--pytest"
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TEST_TIMEOUT)
    return json.dumps(result)
```

**Key Features:**

- Docker sandboxing for security
- Resource limits (CPU, memory, PIDs)
- Network isolation
- JSON output format
- Timeout protection

### Comparison

| Aspect                    | Provided RunTestsTool           | Existing run_tests       |
| ------------------------- | ------------------------------- | ------------------------ |
| **Execution Environment** | Native (uses existing runner)   | Docker container         |
| **Security**              | Relies on runner implementation | Full sandboxing          |
| **Output Format**         | Human-readable summary          | JSON structure           |
| **State Integration**     | ✅ Updates AgentState           | ❌ Stateless             |
| **Resource Limits**       | Not specified                   | ✅ CPU/Memory/PID limits |
| **Network Access**        | Not restricted                  | ❌ Disabled              |
| **Failure Details**       | Truncated traceback             | Full JSON result         |

## 2. Patch/File Modification Tools

### Provided: ApplyPatchTool

```python
def _apply_patch_tool_func(patch_diff: str) -> str:
    # Increment iteration if not after critic
    if not self._critic_called:
        self.state.increment_iteration()

    # Apply patch using ApplyPatchNode
    apply_node = ApplyPatchNode(verbose=self.verbose, safety_config=self.safety_config)
    result = apply_node.execute(
        self.state, patch_diff,
        git_manager=self.git_manager,
        skip_safety_check=False,
        logger=self.telemetry,
        iteration=self.state.current_iteration
    )

    if not result.get("success"):
        if result.get("safety_violation"):
            self.state.final_status = "safety_violation"
            return "Patch rejected due to safety limits."
        if result.get("preflight_failed"):
            self.state.critic_feedback = "Patch application failed (context mismatch)."
            return "Patch apply failed: context mismatch."
        return "Failed to apply patch."

    return "Patch applied successfully."
```

**Implementation in ApplyPatchNode:**

- Preflight validation with `git apply --check`
- Safety checks via `patch_guard.preflight_patch_checks()`
- Git commit integration
- Detailed error messages
- Rollback capability

### Existing: write_file Tool

```python
@tool("write_file", return_direct=True)
def write_file(path: str, new_content: str) -> str:
    """Overwrite a file with the given content."""
    p = Path(path)
    for pattern in blocked_patterns:
        if p.match(pattern):
            return f"ERROR: Modification of {path} is not allowed."

    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(new_content)
        return f"File {path} updated."
    except Exception as e:
        return f"ERROR: Could not write to file {path}: {e}"
```

**Key Features:**

- Direct file overwrite
- Simple pattern-based blocking
- Creates parent directories
- Basic error handling

### Comparison

| Aspect                | ApplyPatchTool              | write_file              |
| --------------------- | --------------------------- | ----------------------- |
| **Input Format**      | Unified diff                | Full file content       |
| **Granularity**       | Line-level changes          | File-level replacement  |
| **Safety Checks**     | Comprehensive (patch_guard) | Pattern matching        |
| **Validation**        | Preflight with git apply    | None                    |
| **Version Control**   | Git commit integration      | No VCS integration      |
| **Rollback**          | Supported                   | Not supported           |
| **Context Awareness** | ✅ Validates context        | ❌ Overwrites blindly   |
| **Error Recovery**    | Detailed error types        | Basic exception message |

## 3. Review/Validation Tools

### Provided: CriticReviewTool

```python
def _critic_review_tool_func(patch_diff: str) -> str:
    # Increment iteration for each review
    self.state.increment_iteration()
    self._critic_called = True

    # Log critic start
    self.telemetry.log_event("critic_start", {...})

    # LLM review
    system_prompt = (
        "You are a code reviewer tasked with evaluating a patch..."
        "Respond with JSON: {\"approved\": true/false, \"reason\": \"...\"}"
    )

    response = self._llm_client.complete(
        system=system_prompt,
        user=user_prompt,
        temperature=0.1
    )

    # Parse JSON response
    review_json = json.loads(response[start_idx:end_idx+1])
    approved = review_json.get("approved", False)
    reason = review_json.get("reason", "")

    if approved:
        self.state.critic_feedback = None
        return f"APPROVED: {reason}"
    else:
        self.state.critic_feedback = reason
        return f"REJECTED: {reason}"
```

### Existing: No Direct Equivalent

The existing codebase has a CriticNode in `/src/nova/nodes/critic.py` but it's not exposed as a tool to the agent.

### Comparison

| Aspect                 | CriticReviewTool        | Existing Approach         |
| ---------------------- | ----------------------- | ------------------------- |
| **Availability**       | Tool for agent          | Node in pipeline only     |
| **Integration**        | In-agent review         | External to agent         |
| **Feedback Loop**      | Immediate               | Requires orchestration    |
| **State Updates**      | Updates critic_feedback | Separate state management |
| **Iteration Counting** | Integrated              | External                  |

## 4. Planning Tools

### Provided: No Explicit Planning Tool

Planning is handled through the ReAct pattern's "Thought" phase.

### Existing: plan_todo Tool

```python
@tool("plan_todo", return_direct=True)
def plan_todo(todo: str) -> str:
    """Plan next steps. The agent uses this to outline a TODO list."""
    return f"Plan noted: {todo}"
```

**Comparison:**

- Existing has explicit planning tool (though it's a no-op)
- Provided uses ReAct thought process for planning
- Neither actually enforces plan execution

## 5. Standalone ApplyPatchTool Implementation (Provided Separately)

The provided code includes a standalone LangChain-compatible `ApplyPatchTool`:

```python
class ApplyPatchTool(BaseTool):
    name: str = "apply_patch"
    description: str = "Apply a unified diff patch to the repository..."
    args_schema = ApplyPatchToolInput

    def _run(self, patch: str) -> str:
        self._step_count += 1

        # Telemetry logging
        if self.telemetry_logger:
            self.telemetry_logger.log_event("apply_start", {...})

        # Safety checks
        is_safe, issues = patch_guard.preflight_patch_checks(
            patch, forbid_test_edits=True, forbid_config_edits=True
        )
        if not is_safe:
            result = ApplyPatchToolOutput(
                success=False,
                safety_issues=issues,
                changed_files=[]
            )
            return result.json()

        # Apply patch
        success, changed_paths = apply_and_commit_patch(...)

        output = ApplyPatchToolOutput(
            success=success,
            safety_issues=[],
            changed_files=changed_files
        )
        return output.json()
```

**Notable Features:**

- Pydantic schemas for input/output
- Structured JSON responses
- Step counting for commits
- Comprehensive telemetry

## 6. Integration Patterns

### Provided Implementation

```python
# Tools are methods within the agent class
class NovaDeepAgent:
    def __init__(self, ...):
        self.state = state
        self.git_manager = git_manager
        self.telemetry = telemetry

        # Tools access shared state through closures
        def _run_tests_tool_func():
            result = run_tests(self.state, self.telemetry, ...)
```

### Existing Implementation

```python
# Tools are standalone functions with decorators
@tool("run_tests", return_direct=True)
def run_tests() -> str:
    # Self-contained, no shared state
    repo_path = Path(".").resolve()
    ...
```

**Key Differences:**

- Provided: Tools share state through agent instance
- Existing: Tools are stateless, independent functions
- Provided: Tight coupling for state management
- Existing: Loose coupling, requires external orchestration

## 7. Error Handling Comparison

### Provided Approach

```python
if not result.get("success"):
    if result.get("safety_violation"):
        self.state.final_status = "safety_violation"
        return "Patch rejected due to safety limits."
    if result.get("preflight_failed"):
        self.state.critic_feedback = "Patch application failed..."
        return "Patch apply failed: context mismatch."
    return "Failed to apply patch."
```

- Structured error types
- State updates on errors
- Human-readable messages

### Existing Approach

```python
try:
    with open(path, "w") as f:
        f.write(new_content)
    return f"File {path} updated."
except Exception as e:
    return f"ERROR: Could not write to file {path}: {e}"
```

- Simple try-catch
- Generic error messages
- No state updates

## 8. Security Model Comparison

### Provided Implementation

1. **Patch Validation**: Git apply --check before modifications
2. **Content Analysis**: AST validation, duplicate detection
3. **Scope Limiting**: Forbids test/config modifications
4. **Audit Trail**: Comprehensive telemetry logging

### Existing Implementation

1. **Sandboxing**: Docker container isolation
2. **Resource Limits**: CPU, memory, process limits
3. **Network Isolation**: No network access
4. **File Patterns**: Blocked file patterns

### Security Comparison Table

| Security Feature        | Provided          | Existing           |
| ----------------------- | ----------------- | ------------------ |
| **Container Isolation** | ❌                | ✅ Docker          |
| **Resource Limits**     | ❌                | ✅ Enforced        |
| **Network Isolation**   | ❌                | ✅ Disabled        |
| **Code Analysis**       | ✅ AST checks     | ❌                 |
| **Pattern Blocking**    | ✅ In patch_guard | ✅ Simple patterns |
| **Audit Logging**       | ✅ Detailed       | ⚠️ Basic           |

## 9. Performance Characteristics

### Provided Tools

- **Latency**: Higher (multiple validation steps)
- **Throughput**: Lower (comprehensive checks)
- **Memory**: Higher (state tracking)
- **CPU**: Higher (AST analysis)

### Existing Tools

- **Latency**: Lower (direct operations)
- **Throughput**: Higher (minimal overhead)
- **Memory**: Lower (stateless)
- **CPU**: Lower (no analysis)

## 10. Recommendations for Tool Improvements

### High Priority

1. **Merge Security Models**: Combine Docker sandboxing with patch validation
2. **Add Structured Output**: JSON schemas for all tools
3. **Implement State Sharing**: Allow tools to share AgentState

### Medium Priority

1. **Enhance Error Types**: Structured error codes/types
2. **Add Telemetry**: Comprehensive event logging
3. **Implement Rollback**: Git-based rollback for all modifications

### Low Priority

1. **Tool Composition**: Allow tools to call other tools
2. **Async Support**: Implement async versions
3. **Caching**: Cache file reads and test results

## Conclusion

The provided implementation offers more sophisticated validation and state management, while the existing implementation provides better security through sandboxing. The optimal solution would combine:

1. **Docker sandboxing** from existing (for test execution)
2. **Patch validation** from provided (for code changes)
3. **State management** from provided (for tracking)
4. **Structured output** from provided (for parsing)
5. **Pattern blocking** from both (layered security)

This hybrid approach would provide maximum security, reliability, and debuggability.
