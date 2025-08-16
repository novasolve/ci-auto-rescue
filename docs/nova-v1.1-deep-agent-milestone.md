# Nova CI-Rescue v1.1 – Deep Agent Integration Milestone

## v1.1 Summary and Scope

Nova CI-Rescue v1.1 introduces a **Deep Agent powered by LangChain**, replacing the earlier multi-node pipeline with a single intelligent agent. The goal is to improve modularity, safety, and predictability of the automated test-fixing process, while simplifying the codebase. Key changes and goals include:

1. **Unified Agent Architecture**: A single `NovaDeepAgent` class using a ReAct-style LLM agent with tool access, instead of separate Planner/Actor/Critic nodes. This simplifies control flow and state management.

2. **Embedded Guardrail Prompts**: The agent's system prompt explicitly reinforces Nova's core rules – never modify tests, minimize diff size, use only available tools (no hallucinated tools), follow safety policies, and produce valid patches. These guidelines ensure the LLM adheres to safety and scope constraints when generating fixes.

3. **LangChain Tools for Actions**: Core actions (running tests, applying patches, etc.) are encapsulated as LangChain tools with well-defined interfaces. Tools enforce structured I/O (e.g. JSON results, standardized patch format) and internal safety checks. This prevents the agent from performing unsupported operations and makes its outputs predictable.

4. **Safety & Validations**: Enhanced safety limits (max lines changed, forbidden file patterns) are applied to any patch before it's committed. JSON schemas and parsing are used to validate outputs from tools (e.g. test results, patch reviews) to catch format errors.

5. **Minimal Diff Fixes**: Both the prompt instructions and the patch validation logic encourage the smallest necessary changes to fix tests. The Critic review tool will reject patches that are too large or risky, and the system prompt tells the agent to keep changes focused and minimal.

6. **Improved Docker Sandbox**: The test runner uses a Docker sandbox with strict isolation (no network, limited CPU/memory, process cap) to safely execute tests. This ensures reproducible test results and prevents malicious code from affecting the host.

7. **Documentation & Examples**: v1.1 provides comprehensive docs on prompt design, tool interfaces, usage, and an updated architecture diagram. A migration guide helps upgrade from v1.0, and sample regression scripts demonstrate testing the agent on real repositories using the sandbox.

Overall, Nova CI-Rescue v1.1 focuses on a more robust, secure, and maintainable system that yields high success rates in fixing CI test failures, with clear structure and guardrails to maintain code quality and safety.

## Architecture and Agent Orchestration

In v1.1, Nova's architecture centers around the `NovaDeepAgent` and its toolset. The agent uses an LLM (like GPT-4/GPT-5 via LangChain) orchestrated in a loop of Plan → Act → Test → Critique steps until tests pass or limits are reached. The high-level flow is:

```mermaid
flowchart TD
    subgraph CLI["CLI (nova fix command)"]
        A[Start: Detect failing tests] --> B{{List failing tests}}
        B --> C[Initialize NovaDeepAgent]
        C --> D[DeepAgent.run()]
    end
    
    subgraph NovaDeepAgent["NovaDeepAgent (LLM Agent + Tools)"]
        D --> |plan_todo tool| E["Plan next steps"]
        D --> |open_file tool| F["Read source file"]
        D --> |write_file tool| G["Modify source code"]
        D --> |run_tests tool| H["Run tests in sandbox (JSON output)"]
        D --> |critic_review tool| I["Review patch safety"]
        D --> |apply_patch tool| J["Apply patch & commit"]
    end
    
    H --> K{{All tests passed?}}
    I --> |REJECTED| L["Abort or adjust patch"]
    I --> |APPROVED| J
    K -- No, still failing --> E
    K -- Yes, success --> M[Tests fixed 🎉]
```

**Figure**: Nova CI-Rescue v1.1 architecture. The CLI collects initial failing tests, then invokes the Deep Agent. The agent iteratively uses tools to plan, read code, write fixes, run tests, and (optionally) review/apply patches. It loops internally until all tests pass or it determines no further progress can be made. A Critic review and safety checks gate the patch application step to prevent unsafe or invalid changes.

## Deep Agent and System Prompt Design

The `NovaDeepAgent` is implemented as a wrapper around a LangChain `AgentExecutor` configured with our custom tools and a specialized prompt. The agent supports both OpenAI Functions agent type (for GPT-4/GPT-3.5) and ReAct pattern (for GPT-5 and other models), allowing flexible model compatibility. Key aspects:

### System Prompt
Defines the agent's role and core rules. For example:

```python
system_message = (
    "You are Nova, an advanced AI software engineer specialized in automatically fixing failing tests.\n\n"
    "## CRITICAL RULES - NEVER VIOLATE THESE:\n"
    "1. **NEVER MODIFY TEST FILES**: You must NEVER edit any file in tests/, test_*.py, or *_test.py\n"
    "   - If a test is wrong, document it but DO NOT change it\n"
    "   - Only fix source code to make tests pass\n\n"
    "2. **MINIMIZE DIFF SIZE**: Keep changes as small as possible\n"
    "   - Fix only what's necessary for tests to pass\n"
    "   - Don't refactor or improve unrelated code\n"
    "   - Each change should have a clear purpose\n\n"
    "3. **NO HALLUCINATING TOOLS**: Only use tools that actually exist\n"
    "   - Available tools: plan_todo, open_file, write_file, run_tests, apply_patch, critic_review\n"
    "   - Never invent or reference non-existent tools\n\n"
    "4. **SAFETY GUARDRAILS**: Respect all safety limits\n"
    "   - Max patch size: 500 lines\n"
    "   - Max files per patch: 10\n"
    "   - Never modify: .env, .git/, secrets/, .github/, CI/CD configs\n\n"
    "5. **VALID PATCHES ONLY**: Ensure all patches are syntactically valid\n"
    "   - Preserve indentation (spaces vs tabs)\n"
    "   - Maintain code style consistency\n"
    "   - Ensure no syntax errors introduced"
)
```

This prompt clearly tells the LLM what it can and cannot do, addressing the "no hallucinated tools" rule and emphasizing minimal, safe changes.

### User Prompt
When `deep_agent.run()` is called, it constructs a user prompt with specific failing test names, error messages, and expected workflow:

```python
user_prompt = f"""Fix the following failing tests:

## FAILURES SUMMARY:
{failures_summary}

## ERROR DETAILS (Stack traces and messages):
{error_details}

## YOUR TASK:
Use the available tools to fix the failing tests. Follow this workflow:

1. **Plan your approach** using 'plan_todo' - Outline what needs to be fixed
2. **Read relevant files** using 'open_file' - Understand the code structure
3. **Modify source code** using 'write_file' - Apply minimal fixes
4. **Run tests** using 'run_tests' - Verify your fixes work
5. **(Optional) Review patches** using 'critic_review' - Validate changes before applying
6. **(Optional) Apply patches** using 'apply_patch' - Commit validated changes

Remember: Do not modify test files. Keep changes minimal...
"""
```

This guides the agent's ReAct chain-of-thought, encouraging a structured approach.

### ReAct Loop via LangChain
For models that don't support function calling (like GPT-5), we use the ReAct pattern with a structured prompt:

```python
react_prompt = PromptTemplate(
    template=system_message + """
    
## Available Tools:
{tool_descriptions}

## ReAct Process:
Use the following format for each step:

Thought: [Your reasoning about what to do next]
Action: [The action/tool to use, should be one of: {tool_names}]
Action Input: [The input to the action]
Observation: [The result of the action - this will be filled automatically]
... (repeat Thought/Action/Observation as needed)
Thought: [Final reasoning when problem is solved]
Final Answer: [Summary of what was fixed]

## Task:
{input}
""",
    input_variables=["input", "agent_scratchpad"],
    partial_variables={
        "tool_descriptions": tool_descriptions,
        "tool_names": ", ".join([tool.name for tool in tools])
    }
)
```

The agent handles iterations internally using LangChain's `AgentExecutor`, eliminating the legacy Python while-loop in the CLI.

## LangChain Tool Implementations

Nova v1.1 defines a set of LangChain tools that the Deep Agent can use. Each tool has an explicit name, description, and safety checks. The core tools are:

### Planning Tool (plan_todo)
A no-op tool used to record the agent's plan:

```python
@tool("plan_todo", return_direct=False)
def plan_todo(todo: str) -> str:
    """Plan next steps. The agent uses this to outline a TODO list or strategy."""
    return f"Plan noted: {todo}"
```

### File Read Tool (open_file)
Allows the agent to safely read file contents:

```python
@tool("open_file", return_direct=False)
def open_file(path: str) -> str:
    """Read the contents of a file, with enhanced safety checks."""
    # Block forbidden patterns (tests/, secrets, configs, etc.)
    for pattern in BLOCKED_PATTERNS:
        if fnmatch.fnmatch(path, pattern):
            return f"ERROR: Access to {path} is blocked by policy"
    
    # Additional test file check
    if any(part.startswith('test') for part in Path(path).parts):
        return f"ERROR: Access to test file {path} is blocked by policy"
    
    try:
        content = Path(path).read_text()
        if len(content) > 50000:  # Truncate large files
            content = content[:50000] + "\n... (truncated)"
        return content
    except FileNotFoundError:
        return f"ERROR: File not found: {path}"
```

### File Write Tool (write_file)
Allows the agent to modify code with safety checks:

```python
@tool("write_file", return_direct=False)
def write_file(path: str, new_content: str) -> str:
    """Overwrite a file with the given content, with enhanced safety checks."""
    # Similar blocking as open_file
    # Check file size limit
    if len(new_content) > 100000:  # 100KB limit
        return f"ERROR: Content too large"
    
    Path(path).write_text(new_content)
    return f"SUCCESS: File {path} updated successfully"
```

### Test Run Tool (run_tests)
Executes tests in Docker sandbox and returns JSON:

```python
class RunTestsTool(BaseTool):
    name = "run_tests"
    description = "Run the project's test suite inside a sandbox and get failing test info."
    
    def _run(self, max_failures: int = 5) -> str:
        # Docker execution with resource limits
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{self.repo_path.absolute()}:/workspace:ro",
            "--memory", "1g", "--cpus", "1.0",
            "--network", "none", "--pids-limit", "256",
            DOCKER_IMAGE, "python", "/usr/local/bin/run_python.py", "--pytest"
        ]
        
        # Always return JSON formatted results
        if result.get("exit_code", 0) == 0:
            return json.dumps({
                "exit_code": 0,
                "failures": 0,
                "message": "All tests passed",
                "failing_tests": []
            })
        else:
            return json.dumps({
                "exit_code": 1,
                "failures": len(failures),
                "message": f"{len(failures)} test(s) failed",
                "failing_tests": failures[:max_failures]
            })
```

### Patch Application Tool (apply_patch)
Applies unified diff patches with thorough safety checks:

```python
class ApplyPatchTool(BaseTool):
    name = "apply_patch"
    description = "Apply an approved unified diff patch to the repository."
    
    def _run(self, patch_diff: str) -> str:
        # 1. Safety checks on patch content
        is_safe, safe_msg = check_patch_safety(patch_text, config=self.safety_config)
        if not is_safe:
            return f"FAILED: Safety violation – {safe_msg}"
        
        # 2. Preflight: ensure patch applies cleanly
        if git_apply_check_fails:
            return "FAILED: Patch could not be applied (context mismatch)"
        
        # 3. Apply and commit
        subprocess.run(["git", "apply", patch_file])
        subprocess.run(["git", "commit", "-m", "Apply patch from Nova Deep Agent"])
        return "SUCCESS: Patch applied successfully."
```

### Critic Review Tool (critic_review)
Performs multi-layer patch review:

```python
class CriticReviewTool(BaseTool):
    name = "critic_review"
    description = "Review a patch diff to decide if it should be applied."
    
    def _run(self, patch_diff: str, failing_tests: Optional[str] = None) -> str:
        # Safety checks (40+ forbidden patterns, size limits, suspicious code)
        safe, safety_reason = self._check_safety(patch_diff)
        if not safe:
            return f"REJECTED: {safety_reason}"
        
        # LLM semantic review
        approved, llm_reason = self._llm_review(patch_diff, failing_tests)
        return f"APPROVED: {llm_reason}" if approved else f"REJECTED: {llm_reason}"
```

## Agent Execution Loop and CLI Integration

The CLI command `nova fix` orchestrates the high-level flow:

### Initial Test Discovery
The CLI first runs tests to collect failing test details:

```python
# In nova/cli.py
runner = TestRunner(repo_path)
failing_tests, summary = runner.run_tests()
failures_summary = format_failures_table(failing_tests)
error_details = extract_error_snippets(failing_tests)
```

### Agent Initialization
Creates the Deep Agent with all necessary components:

```python
state = AgentState(repo_path=repo_path)
telemetry = JSONLLogger()
deep_agent = NovaDeepAgent(
    state=state,
    telemetry=telemetry,
    verbose=verbose,
    safety_config=safety_config
)
```

### Running the Agent
Invokes the agent with failing test information:

```python
success = deep_agent.run(
    failures_summary=failures_summary,
    error_details=error_details,
    code_snippets=code_snippets
)
```

The agent internally:
1. Assembles the prompt (system + user)
2. Invokes LangChain `AgentExecutor`
3. Iterates through tools (plan → read → write → test)
4. Stops when tests pass or no progress

### Post-Agent Verification
After execution, verifies all tests pass:

```python
# Final test run to confirm success
test_tool = RunTestsTool(repo_path=state.repo_path)
final_result = json.loads(test_tool._run())

if final_result["exit_code"] == 0:
    state.final_status = "success"
    print("✅ SUCCESS - All tests fixed!")
```

## Structured Outputs and Validation

Throughout v1.1, emphasis on structured outputs for reliability:

### JSON Test Results
The `run_tests` tool always outputs JSON:

```json
{
  "exit_code": 0,
  "failures": 0,
  "passed": 15,
  "message": "All tests passed",
  "failing_tests": []
}
```

### Patch Diff Format
Enforces unified diff format with validation:
- Strips markdown formatting (```diff blocks)
- Validates with `git apply --check`
- Ensures proper context lines

### Schema Validation via Pydantic
Complex tool inputs use Pydantic models:

```python
class RunTestsInput(BaseModel):
    max_failures: int = Field(5, description="Max failing tests to report")

class ApplyPatchInput(BaseModel):
    patch_diff: str = Field(..., description="Unified diff patch")
```

### Safety Checks
Multi-layer validation:
- **File patterns**: 40+ blocked patterns
- **Code patterns**: 20+ suspicious patterns
- **Size limits**: Max 500 lines, 10 files
- **Semantic review**: LLM-based validation

## Model Compatibility (GPT-5 Support)

v1.1 includes special handling for GPT-5 and future models:

```python
# Detect model capabilities
if model_name == "gpt-5":
    llm = ChatOpenAI(model_name="gpt-5", temperature=0)
    use_react = True  # GPT-5 may not support function calling
    print("🚀 Using GPT-5 model with ReAct pattern")
```

The system automatically:
- Uses ReAct pattern for GPT-5
- Falls back to GPT-4 if GPT-5 unavailable
- Adapts agent type based on model capabilities

## Usage Examples

### Basic CLI Usage
```bash
# Fix tests in current repository
nova fix --repo .

# Verbose mode with custom iterations
nova fix --repo /path/to/repo -v --max-iters 10
```

### Programmatic Use
```python
from nova.agent.deep_agent import NovaDeepAgent
from nova.agent.state import AgentState

state = AgentState(repo_path="/path/to/repo")
agent = NovaDeepAgent(state, verbose=True)

success = agent.run(
    failures_summary="test_math.py::test_addition failed",
    error_details="AssertionError: expected 4, got 5"
)
print("Tests fixed?", success)
```

### Configuration via YAML
```yaml
# nova.config.yml
default_llm_model: gpt-5
max_iterations: 8
safety:
  max_lines_changed: 500
  denied_paths:
    - "test_*.*"
    - ".github/*"
```

## Migration Notes (v1.0 to v1.1)

Key changes for upgrading:

1. **Single Agent vs Pipeline**: Old Planner/Actor/Critic steps now internalized
2. **Tool Definitions**: Moved to `nova.agent.unified_tools`
3. **Config**: New `NovaSettings` dataclass, YAML support
4. **AI Model**: All interactions via LangChain
5. **Output**: JSON-formatted test results
6. **Git**: Automatic commits with descriptive messages

## Safety Features Summary

### Never Modify Tests
- System prompt instruction
- File pattern blocking (40+ patterns)
- Critic validation

### Minimal Changes
- 500 line limit
- 10 file limit
- No refactoring rule

### No Tool Hallucination
- Function calling / ReAct pattern only
- Limited tool set
- Explicit tool definitions

### Docker Sandbox
- CPU: 1.0 core
- Memory: 1GB
- Network: Disabled
- Process limit: 256
- Timeout: 600 seconds

## Telemetry and Monitoring

Events tracked:
- `deep_agent_start`
- `deep_agent_success`
- `deep_agent_incomplete`
- `deep_agent_error`
- Tool usage metrics

## Next Steps

With Deep Agent integration in v1.1, Nova CI-Rescue becomes more powerful and maintainable. Future enhancements:
- Additional tools (linters, formatters)
- Multi-language support
- Custom rule engines
- Performance optimizations

---

*Nova CI-Rescue v1.1 - Deep Agent Integration Complete*
