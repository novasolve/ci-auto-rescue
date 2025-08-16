"""
Unified Tools Module for Nova Deep Agent
=========================================

This module consolidates all LangChain tool definitions into a single authoritative source.
It combines the best of both function-based and class-based implementations, eliminating
duplication and providing a clean interface for the Deep Agent.

Tools included:
- plan_todo: Planning no-op tool (records the plan)
- open_file: File read tool with safety checks
- write_file: File write tool with safety checks  
- RunTestsTool: Docker-based test runner with fallback
- ApplyPatchTool: Patch application with safety checks
- CriticReviewTool: Patch review using LLM and safety checks
"""

from pathlib import Path
import shutil
import subprocess
import json
import tempfile
import time
import re
from typing import Optional, Any, Type, Dict, List, ClassVar
from langchain.agents import tool
from langchain.tools import BaseTool, Tool
from pydantic import BaseModel, Field

# Safety config and checks (reuse existing implementations)
from nova.tools.safety_limits import check_patch_safety, SafetyConfig

# Import telemetry logger if needed
from nova.telemetry.logger import JSONLLogger

# Docker configuration for test runner
DOCKER_IMAGE = "nova-ci-rescue-sandbox:latest"
CPU_LIMIT = "1.0"   # 1 CPU core
MEM_LIMIT = "1g"    # 1 GB RAM
TEST_TIMEOUT = 600  # 10 minutes
PID_LIMIT = "256"   # Process spawn limit

# Blocked file patterns for safety
BLOCKED_PATTERNS = [
    "tests/*", ".env", ".git/*", "secrets/*", ".github/*", 
    "*.pyc", "__pycache__/*", "*.min.js", "*.min.css"
]


# --- Function-based Tools (Simple Operations) ---

@tool("plan_todo", return_direct=True)
def plan_todo(todo: str) -> str:
    """Plan next steps. The agent uses this to outline a TODO list or strategy."""
    # This tool is a no-op that just records the plan in the agent's log.
    return f"Plan noted: {todo}"


@tool("open_file", return_direct=True)
def open_file(path: str) -> str:
    """Read the contents of a file, with safety checks."""
    p = Path(path)
    
    # Block reading certain files
    for pattern in BLOCKED_PATTERNS:
        if p.match(pattern):
            return f"ERROR: Access to {path} is blocked by policy."
    
    try:
        content = Path(path).read_text()
        # Truncate very large files for LLM context safety
        if len(content) > 50000:  # 50KB limit
            content = content[:50000] + "\n... (truncated)"
        return content
    except FileNotFoundError:
        return f"ERROR: File not found: {path}"
    except PermissionError:
        return f"ERROR: Permission denied: {path}"
    except Exception as e:
        return f"ERROR: Could not read file {path}: {e}"


@tool("write_file", return_direct=True)
def write_file(path: str, new_content: str) -> str:
    """Overwrite a file with the given content, with safety checks."""
    p = Path(path)
    
    # Block modifying certain files
    for pattern in BLOCKED_PATTERNS:
        if p.match(pattern):
            return f"ERROR: Modification of {path} is not allowed."
    
    try:
        # Ensure parent directory exists
        p.parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(new_content)
        return f"File {path} updated."
    except PermissionError:
        return f"ERROR: Permission denied: {path}"
    except Exception as e:
        return f"ERROR: Could not write to file {path}: {e}"


# --- Class-based Tools (Complex Operations) ---

class RunTestsInput(BaseModel):
    """Input schema for run_tests tool."""
    max_failures: int = Field(5, description="Max number of failing tests to report")


class RunTestsTool(BaseTool):
    """
    Tool to run tests and collect failing test details.
    
    Combines Docker sandbox execution with local fallback and
    provides formatted output for the agent.
    """
    name: str = "run_tests"
    description: str = (
        "Run the project's test suite inside a sandbox and get failing test info. "
        "Returns a summary with test names and error messages."
    )
    args_schema: Type[BaseModel] = RunTestsInput
    repo_path: Path = Field(default_factory=lambda: Path("."))
    verbose: bool = Field(default=False)

    def __init__(self, repo_path: Optional[Path] = None, verbose: bool = False, **kwargs):
        """Initialize with repository path."""
        if repo_path is not None:
            kwargs['repo_path'] = Path(repo_path)
        if verbose is not False:
            kwargs['verbose'] = verbose
        super().__init__(**kwargs)

    def _run(self, max_failures: int = 5) -> str:
        """Execute tests and return a summary of results."""
        # Ensure .nova directory for test artifacts exists
        nova_path = self.repo_path / ".nova"
        nova_path.mkdir(exist_ok=True)
        
        # Initialize result variables
        result = None
        docker_error = None
        
        # Try Docker-based execution first
        if shutil.which("docker") is not None:
            # Prepare Docker command (sandboxed test run)
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{self.repo_path.absolute()}:/workspace:ro",
                "-v", f"{nova_path.absolute()}:/workspace/.nova:rw",
                "--memory", MEM_LIMIT,
                "--cpus", CPU_LIMIT,
                "--network", "none",
                "--pids-limit", PID_LIMIT,
                DOCKER_IMAGE,
                "python", "/usr/local/bin/run_python.py", "--pytest"
            ]
            
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TEST_TIMEOUT)
                stdout = proc.stdout.strip()
                
                if not stdout:
                    docker_error = "No output from test run"
                else:
                    try:
                        result = json.loads(stdout)
                    except json.JSONDecodeError:
                        docker_error = "Non-JSON output from tests"
                        
            except subprocess.TimeoutExpired:
                docker_error = "Test execution timed out"
            except Exception as e:
                docker_error = f"Docker test run failed: {e}"
        else:
            docker_error = "Docker not available"
        
        # If Docker failed, fall back to local TestRunner
        if docker_error:
            if self.verbose:
                print(f"Docker execution failed: {docker_error}. Falling back to local test run.")
            
            try:
                from nova.runner.test_runner import TestRunner
                runner = TestRunner(self.repo_path, verbose=self.verbose)
                failing_tests, summary = runner.run_tests(max_failures=max_failures)
                
                if not failing_tests:
                    return "FAILURES: 0\nAll tests passed."
                
                # Format local runner results
                output_lines = [f"FAILURES: {len(failing_tests)}"]
                for i, test in enumerate(failing_tests[:max_failures], 1):
                    err_line = (test.short_traceback.split("\n")[0] 
                               if hasattr(test, 'short_traceback') else "Unknown error")
                    output_lines.append(f"{i}. {test.name}: {err_line[:100]}")
                
                if len(failing_tests) > max_failures:
                    output_lines.append(f"... and {len(failing_tests) - max_failures} more")
                
                return "\n".join(output_lines)
                
            except Exception as e:
                return f"ERROR: Test execution failed: {e}"
        
        # Process Docker result if available
        if result is None:
            return f"ERROR: {docker_error or 'Unknown test error'}"
        
        if result.get("exit_code", 0) == 0:
            return "FAILURES: 0\nAll tests passed."
        
        # Extract failures from Docker result
        failures = []
        if "failing_tests" in result:
            for test in result["failing_tests"]:
                name = test.get("nodeid") or test.get("name") or "unknown"
                message = test.get("message") or test.get("error", "")
                failures.append(f"{name}: {message[:200]}")
        elif "test_summary" in result:
            # Use summary if detailed fails not available
            summ = result["test_summary"]
            failed = summ.get("failed", 0)
            passed = summ.get("passed", 0)
            return f"FAILURES: {failed}\nPassed: {passed}\nSkipped: {summ.get('skipped', 0)}"
        
        # Build output string
        output_lines = [f"FAILURES: {len(failures)}"]
        for i, info in enumerate(failures[:max_failures], 1):
            output_lines.append(f"{i}. {info}")
        
        if len(failures) > max_failures:
            output_lines.append(f"... and {len(failures) - max_failures} more")
        
        return "\n".join(output_lines)

    async def _arun(self, max_failures: int = 5) -> str:
        """Async version not implemented."""
        raise NotImplementedError("RunTestsTool does not support async execution")


class ApplyPatchInput(BaseModel):
    """Input schema for ApplyPatchTool."""
    patch_diff: str = Field(..., description="Unified diff patch to apply")


class ApplyPatchTool(BaseTool):
    """
    Tool to apply a unified diff patch to the repository.
    
    Includes safety checks and git integration.
    """
    name: str = "apply_patch"
    description: str = (
        "Apply an approved unified diff patch to the repository. "
        "The patch will be validated for safety and context before applying."
    )
    args_schema: Type[BaseModel] = ApplyPatchInput
    repo_path: Path = Field(default_factory=lambda: Path("."))
    safety_config: Optional[SafetyConfig] = Field(default=None)
    verbose: bool = Field(default=False)
    logger: Optional[JSONLLogger] = Field(default=None)

    def __init__(
        self,
        repo_path: Optional[Path] = None,
        safety_config: Optional[SafetyConfig] = None,
        verbose: bool = False,
        logger: Optional[JSONLLogger] = None,
        **kwargs
    ):
        """Initialize with safety configuration."""
        if repo_path is not None:
            kwargs['repo_path'] = Path(repo_path)
        if safety_config is not None:
            kwargs['safety_config'] = safety_config
        else:
            kwargs['safety_config'] = SafetyConfig()
        if verbose is not False:
            kwargs['verbose'] = verbose
        if logger is not None:
            kwargs['logger'] = logger
        super().__init__(**kwargs)

    def _run(self, patch_diff: str) -> str:
        """Apply the given patch diff to the codebase with safety checks."""
        # Remove any markdown formatting (```diff ``` wrappers) if present
        patch_text = patch_diff.strip()
        if patch_text.startswith("```"):
            lines = patch_text.splitlines()
            # Drop leading ```... and trailing ```
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            patch_text = "\n".join(lines)
        
        # 1. Safety checks on patch content
        is_safe, safe_msg = check_patch_safety(
            patch_text, 
            config=self.safety_config,
            verbose=self.verbose
        )
        
        if not is_safe:
            if self.verbose:
                print(f"Safety check failed: {safe_msg}")
            return f"FAILED: Safety violation – {safe_msg}"
        
        # 2. Preflight check: ensure patch applies cleanly
        tmp_file = None
        try:
            # Write patch to temporary file
            tmp_file = tempfile.NamedTemporaryFile(
                mode='w+', suffix='.patch', delete=False
            )
            tmp_file.write(patch_text)
            tmp_file.flush()
            tmp_file.close()
            
            # Check if patch applies cleanly
            preflight = subprocess.run(
                ["git", "apply", "--check", "--whitespace=nowarn", tmp_file.name],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if preflight.returncode != 0:
                # Git apply --check failed, patch does not apply
                if self.verbose:
                    print(f"Patch preflight failed: {preflight.stderr}")
                return "FAILED: Patch could not be applied (context mismatch)."
            
            # 3. Apply patch
            apply_proc = subprocess.run(
                ["git", "apply", "--whitespace=nowarn", tmp_file.name],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if apply_proc.returncode != 0:
                return f"FAILED: Could not apply patch: {apply_proc.stderr}"
            
            # 4. Commit changes
            subprocess.run(["git", "add", "-A"], cwd=self.repo_path, check=False)
            commit_proc = subprocess.run(
                ["git", "commit", "-m", "Apply patch from Nova Deep Agent"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if self.verbose:
                print("Patch applied and committed successfully")
            
            return "SUCCESS: Patch applied successfully."
            
        except Exception as e:
            return f"FAILED: Could not apply patch: {e}"
        
        finally:
            # Clean up temporary file
            if tmp_file and Path(tmp_file.name).exists():
                try:
                    Path(tmp_file.name).unlink()
                except Exception:
                    pass

    async def _arun(self, patch_diff: str) -> str:
        """Async version not implemented."""
        raise NotImplementedError("ApplyPatchTool does not support async execution")


class CriticReviewInput(BaseModel):
    """Input schema for CriticReviewTool."""
    patch_diff: str = Field(description="The patch diff to review")
    failing_tests: Optional[str] = Field(
        default=None,
        description="Optional context about failing tests"
    )


class CriticReviewTool(BaseTool):
    """
    Tool to critically review a patch before applying.
    
    Combines safety checks with LLM-based semantic review.
    """
    name: str = "critic_review"
    description: str = (
        "Review a patch diff to decide if it should be applied. "
        "Returns 'APPROVED: reason' or 'REJECTED: reason'. "
        "Always review patches before applying them."
    )
    args_schema: Type[BaseModel] = CriticReviewInput
    
    verbose: bool = Field(default=False)
    llm: Optional[Any] = Field(default=None)
    
    # Safety patterns (class constant, not instance attribute)
    FORBIDDEN_PATTERNS: ClassVar[List[str]] = [
        r"test_.*\.py",  # Test files
        r".*_test\.py",  # Test files
        r"/tests?/",     # Test directories
        r"\.github/",    # GitHub workflows
        r"setup\.py",    # Setup files
        r"pyproject\.toml",  # Project config
        r"requirements.*\.txt",  # Dependencies
    ]
    
    def __init__(self, verbose: bool = False, llm: Optional[Any] = None, **kwargs):
        """Initialize with optional LLM for semantic review."""
        if verbose is not False:
            kwargs['verbose'] = verbose
        
        # Initialize LLM if not provided
        if llm is not None:
            kwargs['llm'] = llm
        else:
            try:
                from langchain_openai import ChatOpenAI
            except ImportError:
                from langchain.chat_models import ChatOpenAI
            kwargs['llm'] = ChatOpenAI(model="gpt-4", temperature=0.1)
        
        super().__init__(**kwargs)
    
    def _check_safety(self, patch_diff: str) -> tuple[bool, str]:
        """
        Perform safety checks on the patch.
        
        Returns:
            Tuple of (is_safe, reason)
        """
        lines = patch_diff.split("\n")
        
        # Check for test file modifications
        for line in lines:
            if line.startswith("+++") or line.startswith("---"):
                # Extract file path
                parts = line.split()
                if len(parts) >= 2:
                    file_path = parts[1]
                    if file_path.startswith("a/"):
                        file_path = file_path[2:]
                    elif file_path.startswith("b/"):
                        file_path = file_path[2:]
                    
                    # Check against forbidden patterns
                    for pattern in self.FORBIDDEN_PATTERNS:
                        if re.search(pattern, file_path):
                            return False, f"Modifies forbidden path: {file_path}"
        
        # Check patch size
        added = sum(1 for line in lines if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in lines if line.startswith("-") and not line.startswith("---"))
        
        if added + removed > 500:
            return False, f"Patch too large: {added} additions, {removed} deletions"
        
        # Check for suspicious patterns in additions
        suspicious = [
            r"exec\(",
            r"eval\(",
            r"__import__",
            r"os\.system",
            r"subprocess\.call\(",
            r"rm\s+-rf",
        ]
        
        for line in lines:
            if line.startswith("+"):
                for pattern in suspicious:
                    if re.search(pattern, line, re.IGNORECASE):
                        return False, f"Suspicious pattern detected: {pattern}"
        
        return True, "Safety checks passed"
    
    def _llm_review(self, patch_diff: str, failing_tests: Optional[str] = None) -> tuple[bool, str]:
        """
        Use LLM to semantically review the patch.
        
        Returns:
            Tuple of (approved, reason)
        """
        # Prepare the review prompt
        system_prompt = """You are a code reviewer for an AI test-fixing agent.
Review the patch and decide if it should be applied.
Consider:
1. Does it address the failing tests?
2. Is it minimal and focused?
3. Could it break existing functionality?
4. Does it follow good practices?

Respond with JSON: {"approved": true/false, "reason": "brief explanation"}"""
        
        user_prompt = f"""Review this patch:

```diff
{patch_diff[:3000]}  # Truncate for context window
```"""
        
        if failing_tests:
            user_prompt += f"\n\nFailing tests context:\n{failing_tests[:500]}"
        
        try:
            response = self.llm.predict(user_prompt, system=system_prompt)
            
            # Parse JSON response
            if "{" in response and "}" in response:
                start = response.index("{")
                end = response.rindex("}") + 1
                result = json.loads(response[start:end])
                return result.get("approved", False), result.get("reason", "No reason provided")
            else:
                return False, "Invalid review response format"
                
        except Exception as e:
            if self.verbose:
                print(f"LLM review error: {e}")
            return False, f"LLM review failed: {e}"
    
    def _run(self, patch_diff: str, failing_tests: Optional[str] = None) -> str:
        """
        Review the patch and return decision.
        
        Returns:
            "APPROVED: reason" or "REJECTED: reason"
        """
        # First, run safety checks
        safe, safety_reason = self._check_safety(patch_diff)
        
        if not safe:
            return f"REJECTED: {safety_reason}"
        
        # Then, run LLM review if available
        if self.llm:
            approved, llm_reason = self._llm_review(patch_diff, failing_tests)
            
            if approved:
                return f"APPROVED: {llm_reason}"
            else:
                return f"REJECTED: {llm_reason}"
        else:
            # If no LLM, approve based on safety checks alone
            return f"APPROVED: {safety_reason}"
    
    async def _arun(self, patch_diff: str, failing_tests: Optional[str] = None) -> str:
        """Async version not implemented."""
        raise NotImplementedError("CriticReviewTool does not support async execution")


# --- Convenience Functions for Tool Creation ---

def create_default_tools(
    repo_path: Optional[Path] = None,
    verbose: bool = False,
    safety_config: Optional[SafetyConfig] = None,
    llm: Optional[Any] = None
) -> List[BaseTool]:
    """
    Create the default set of tools for the Deep Agent.
    
    Args:
        repo_path: Repository path for tools that need it
        verbose: Enable verbose output
        safety_config: Safety configuration for patch application
        llm: LLM instance for critic review
    
    Returns:
        List of tool instances ready for use
    """
    tools = []
    
    # Add function-based tools (converted to Tool instances for consistency)
    tools.append(Tool(
        name="plan_todo",
        func=plan_todo,
        description="Plan next steps (no-op tool that records the plan)"
    ))
    
    tools.append(Tool(
        name="open_file",
        func=open_file,
        description="Read the contents of a file"
    ))
    
    tools.append(Tool(
        name="write_file",
        func=write_file,
        description="Overwrite a file with the given content"
    ))
    
    # Add class-based tools
    tools.append(RunTestsTool(
        repo_path=repo_path,
        verbose=verbose
    ))
    
    tools.append(ApplyPatchTool(
        repo_path=repo_path,
        safety_config=safety_config,
        verbose=verbose
    ))
    
    tools.append(CriticReviewTool(
        verbose=verbose,
        llm=llm
    ))
    
    return tools


def get_tool_by_name(name: str, tools: List[BaseTool]) -> Optional[BaseTool]:
    """
    Get a tool by name from a list of tools.
    
    Args:
        name: Name of the tool to find
        tools: List of tools to search
    
    Returns:
        The tool if found, None otherwise
    """
    for tool in tools:
        if hasattr(tool, 'name') and tool.name == name:
            return tool
    return None


# --- Backward Compatibility Shims ---
# These will be removed after full migration

def apply_patch_legacy(
    state: Any,
    patch_text: str,
    git_manager: Optional[Any] = None,
    verbose: bool = False,
    safety_config: Optional[SafetyConfig] = None
) -> Dict[str, Any]:
    """
    Legacy compatibility function for apply_patch.
    
    DEPRECATED: Use ApplyPatchTool directly.
    """
    import warnings
    warnings.warn(
        "apply_patch_legacy is deprecated. Use ApplyPatchTool directly.",
        DeprecationWarning,
        stacklevel=2
    )
    
    tool = ApplyPatchTool(
        repo_path=state.repo_path if state else Path("."),
        safety_config=safety_config,
        verbose=verbose
    )
    
    result = tool._run(patch_text)
    
    # Convert to legacy format
    return {
        "success": result.startswith("SUCCESS"),
        "message": result,
        "safety_violation": "Safety violation" in result,
        "preflight_failed": "context mismatch" in result,
        "error": result if result.startswith("FAILED") else None
    }
