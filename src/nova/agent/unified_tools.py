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

# Comprehensive blocked file patterns for enhanced safety
BLOCKED_PATTERNS = [
    # Test files and directories
    "tests/*", "test/*", "test_*.py", "*_test.py", "**/tests/*", "**/test/*",
    # Environment and secrets
    ".env", ".env.*", "*.env", "secrets/*", "credentials/*", 
    # Version control
    ".git/*", ".gitignore", ".gitmodules",
    # CI/CD configurations  
    ".github/*", ".gitlab-ci.yml", ".travis.yml", "jenkins*", "Jenkinsfile",
    # Build and dependency files
    "*.pyc", "__pycache__/*", "*.pyo", "*.pyd", ".Python", "build/*", "dist/*",
    "*.egg-info/*", "*.egg", "pip-log.txt", "pip-delete-this-directory.txt",
    # Package managers and configs
    "pyproject.toml", "setup.py", "setup.cfg", "requirements*.txt", 
    "poetry.lock", "Pipfile", "Pipfile.lock", "package.json", "package-lock.json",
    # IDE and editor files
    ".vscode/*", ".idea/*", "*.swp", "*.swo", "*~", ".DS_Store",
    # Minified and compiled files
    "*.min.js", "*.min.css", "*.wasm", "*.so", "*.dll", "*.dylib",
    # Documentation (unless explicitly needed)
    "docs/*", "documentation/*", "*.md", "README*", "LICENSE*",
    # Security-sensitive paths
    "private/*", "config/*", "settings/*", ".ssh/*", "*.key", "*.pem", "*.crt"
]


# --- Function-based Tools (Simple Operations) ---
# These remain as functions for backward compatibility, but are wrapped in classes below

def plan_todo(todo: str) -> str:
    """Plan next steps. The agent uses this to outline a TODO list or strategy."""
    # This tool is a no-op that just records the plan in the agent's log.
    return f"Plan noted: {todo}"


def open_file(path: str) -> str:
    """Read the contents of a file, with enhanced safety checks."""
    import fnmatch
    p = Path(path)
    path_str = str(p)
    
    # Enhanced blocking with glob pattern matching
    for pattern in BLOCKED_PATTERNS:
        # Handle glob patterns properly
        if '*' in pattern or '?' in pattern:
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(p.name, pattern):
                return f"ERROR: Access to {path} is blocked by policy (pattern: {pattern})"
        else:
            # Direct path/name matching
            if pattern in path_str or p.name == pattern:
                return f"ERROR: Access to {path} is blocked by policy"
    
    # Additional check for test files specifically
    if any(part.startswith('test') for part in p.parts) or p.name.startswith('test_') or p.name.endswith('_test.py'):
        return f"ERROR: Access to test file {path} is blocked by policy"
    
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


def write_file(path: str, new_content: str) -> str:
    """Overwrite a file with the given content, with enhanced safety checks."""
    import fnmatch
    p = Path(path)
    path_str = str(p)
    
    # Enhanced blocking with glob pattern matching
    for pattern in BLOCKED_PATTERNS:
        # Handle glob patterns properly
        if '*' in pattern or '?' in pattern:
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(p.name, pattern):
                return f"ERROR: Modification of {path} is not allowed (pattern: {pattern})"
        else:
            # Direct path/name matching
            if pattern in path_str or p.name == pattern:
                return f"ERROR: Modification of {path} is not allowed"
    
    # Additional check for test files specifically
    if any(part.startswith('test') for part in p.parts) or p.name.startswith('test_') or p.name.endswith('_test.py'):
        return f"ERROR: Modification of test file {path} is not allowed"
    
    # Check file size limit (prevent writing huge files)
    if len(new_content) > 100000:  # 100KB limit for new content
        return f"ERROR: Content too large ({len(new_content)} bytes). Max allowed: 100000 bytes"
    
    try:
        # Ensure parent directory exists
        p.parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(new_content)
        return f"SUCCESS: File {path} updated successfully"
    except PermissionError:
        return f"ERROR: Permission denied: {path}"
    except Exception as e:
        return f"ERROR: Could not write to file {path}: {e}"


# --- Pydantic-based Tool Classes for Simple Tools ---

class PlanTodoInput(BaseModel):
    """Input schema for plan_todo tool."""
    todo: str = Field(..., description="The plan or TODO description to record")


class PlanTodoTool(BaseTool):
    """Tool to plan next steps by outlining a TODO list or strategy."""
    name: str = "plan_todo"
    description: str = "Plan next steps by outlining a TODO list or strategy."
    args_schema: Type[BaseModel] = PlanTodoInput
    
    def _run(self, todo: str) -> str:
        """Execute the plan_todo function."""
        # No-op tool: just logs the plan
        return f"Plan noted: {todo}"
    
    async def _arun(self, todo: str) -> str:
        """Async version not implemented."""
        raise NotImplementedError("PlanTodoTool does not support async execution")


class OpenFileInput(BaseModel):
    """Input schema for open_file tool."""
    path: str = Field(..., description="Path of the file to read from the repository")


class OpenFileTool(BaseTool):
    """Tool to read the contents of a file."""
    name: str = "open_file"
    description: str = "Read the contents of a file from the repository (with safety checks)."
    args_schema: Type[BaseModel] = OpenFileInput
    
    def _run(self, path: str) -> str:
        """Execute the open_file function with safety checks."""
        # Same logic as the original open_file function, with safety guardrails
        import fnmatch
        import os
        p = Path(path)
        path_str = str(p)
        for pattern in BLOCKED_PATTERNS:
            if ('*' in pattern or '?' in pattern):
                if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(p.name, pattern):
                    return f"ERROR: Access to {path} is blocked by policy (pattern: {pattern})"
            else:
                if pattern in path_str or p.name == pattern:
                    return f"ERROR: Access to {path} is blocked by policy"
        # Block any test files explicitly
        if any(part.startswith('test') for part in p.parts) or p.name.startswith('test_') or p.name.endswith('_test.py'):
            return f"ERROR: Access to test file {path} is blocked by policy"
        try:
            content = p.read_text()
            if len(content) > 50000:  # 50KB limit
                content = content[:50000] + "\n... (truncated)"
            return content
        except FileNotFoundError:
            return f"ERROR: File not found: {path}"
        except PermissionError:
            return f"ERROR: Permission denied: {path}"
        except Exception as e:
            return f"ERROR: Could not read file {path}: {e}"
    
    async def _arun(self, path: str) -> str:
        """Async version not implemented."""
        raise NotImplementedError("OpenFileTool does not support async execution")


class WriteFileInput(BaseModel):
    """Input schema for write_file tool."""
    path: str = Field(..., description="Path of the file to write/overwrite")
    new_content: str = Field(..., description="The new content to write into the file")


class WriteFileTool(BaseTool):
    """Tool to write or overwrite a file with new content."""
    name: str = "write_file"
    description: str = "Write or overwrite a file with new content (with safety checks)."
    args_schema: Type[BaseModel] = WriteFileInput
    
    def _run(self, path: str, new_content: str) -> str:
        """Execute the write_file function with safety checks."""
        import fnmatch
        import os
        p = Path(path)
        path_str = str(p)
        for pattern in BLOCKED_PATTERNS:
            if ('*' in pattern or '?' in pattern):
                if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(p.name, pattern):
                    return f"ERROR: Modification of {path} is not allowed (pattern: {pattern})"
            else:
                if pattern in path_str or p.name == pattern:
                    return f"ERROR: Modification of {path} is not allowed"
        # Block any test files explicitly
        if any(part.startswith('test') for part in p.parts) or p.name.startswith('test_') or p.name.endswith('_test.py'):
            return f"ERROR: Modification of test file {path} is not allowed"
        if len(new_content) > 100000:  # 100KB write limit
            return f"ERROR: Content too large ({len(new_content)} bytes). Max allowed: 100000 bytes"
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(new_content)
            return f"SUCCESS: File {path} updated successfully"
        except PermissionError:
            return f"ERROR: Permission denied: {path}"
        except Exception as e:
            return f"ERROR: Could not write to file {path}: {e}"
    
    async def _arun(self, path: str, new_content: str) -> str:
        """Async version not implemented."""
        raise NotImplementedError("WriteFileTool does not support async execution")


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
        """Execute tests and return a JSON summary of results."""
        # Ensure .nova directory for test artifacts exists
        nova_path = self.repo_path / ".nova"
        nova_path.mkdir(exist_ok=True)
        
        # Initialize result variables
        result = None
        docker_error = None
        
        # Try Docker-based execution first (with enhanced security limits)
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
            # Warn the user that we are falling back to local execution (no isolation)
            try:
                from rich.console import Console
                Console().print("[bold yellow]⚠️ Sandbox unavailable – running tests without isolation.[/bold yellow]")
            except ImportError:
                print("⚠️ Sandbox unavailable – running tests without isolation.")
            if self.verbose:
                print(f"Docker execution failed: {docker_error}. Falling back to local test run.")
            
            try:
                from nova.runner.test_runner import TestRunner
                runner = TestRunner(self.repo_path, verbose=self.verbose)
                failing_tests, summary = runner.run_tests(max_failures=max_failures)
                
                if not failing_tests:
                    # All tests passing, return JSON
                    return json.dumps({
                        "exit_code": 0,
                        "failures": 0,
                        "passed": summary.get("passed", 0) if summary else "unknown",
                        "message": "All tests passed",
                        "failing_tests": []
                    })
                
                # Format local runner results as JSON
                failures_json = []
                for test in failing_tests[:max_failures]:
                    failures_json.append({
                        "name": test.name if hasattr(test, 'name') else "unknown",
                        "error": (test.short_traceback.split("\n")[0][:500] 
                                 if hasattr(test, 'short_traceback') else "Unknown error"),
                        "traceback": (test.short_traceback[:1000] 
                                     if hasattr(test, 'short_traceback') else "")
                    })
                
                return json.dumps({
                    "exit_code": 1,
                    "failures": len(failing_tests),
                    "passed": summary.get("passed", 0) if summary else 0,
                    "message": f"{len(failing_tests)} test(s) failed",
                    "failing_tests": failures_json
                })
                
            except Exception as e:
                # Return error as JSON
                return json.dumps({
                    "exit_code": 1,
                    "error": f"Test execution failed: {e}",
                    "failures": 0,
                    "passed": 0,
                    "stderr": str(e)
                })
        
        # Always return JSON formatted results for consistent parsing
        if result is None:
            # Docker execution failed, return error as JSON
            return json.dumps({
                "exit_code": 1,
                "error": docker_error or "Unknown test error",
                "failures": 0,
                "passed": 0,
                "stderr": docker_error
            })
        
        if result.get("exit_code", 0) == 0:
            # All tests passing
            return json.dumps({
                "exit_code": 0,
                "failures": 0,
                "passed": result.get("test_summary", {}).get("passed", "unknown"),
                "message": "All tests passed",
                "failing_tests": []
            })
        
        # Extract failures from Docker result
        failures = []
        if "failing_tests" in result:
            for test in result["failing_tests"]:
                name = test.get("nodeid") or test.get("name") or "unknown"
                message = test.get("message") or test.get("error", "")
                failures.append({
                    "name": name,
                    "error": message[:500],  # Truncate long errors
                    "traceback": test.get("traceback", "")[:1000] if test.get("traceback") else ""
                })
        elif "test_summary" in result:
            # Use summary if detailed fails not available
            summ = result["test_summary"]
            return json.dumps({
                "exit_code": result.get("exit_code", 1),
                "failures": summ.get("failed", 0),
                "passed": summ.get("passed", 0),
                "skipped": summ.get("skipped", 0),
                "message": f"Tests failed: {summ.get('failed', 0)}",
                "failing_tests": []
            })
        
        # Return JSON with failure details
        return json.dumps({
            "exit_code": result.get("exit_code", 1),
            "failures": len(failures),
            "passed": result.get("test_summary", {}).get("passed", 0) if result.get("test_summary") else 0,
            "message": f"{len(failures)} test(s) failed",
            "failing_tests": failures[:max_failures]
        })

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
        safety_config: Optional[Any] = None,
        verbose: bool = False,
        logger: Optional[JSONLLogger] = None,
        **kwargs
    ):
        """Initialize with safety configuration."""
        # Set all fields in kwargs before super().__init__
        if repo_path is not None:
            kwargs['repo_path'] = Path(repo_path)
        kwargs['safety_config'] = safety_config or SafetyConfig()
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
            
            # 5. Success! Update state to clear the review
            if self.state:
                self.state.last_review_approved = False  # Reset for next patch
                self.state.last_reviewed_patch = None
                self.state.pending_patch = None
                # Add to patches applied list
                if hasattr(self.state, 'patches_applied'):
                    self.state.patches_applied.append(patch_text)
            
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
    state: Optional[Any] = Field(default=None)  # Agent state for tracking reviews
    
    # Comprehensive safety patterns for patch review
    FORBIDDEN_PATTERNS: ClassVar[List[str]] = [
        # Test files and directories (high priority)
        r"test_.*\.py",  # Test files starting with test_
        r".*_test\.py",  # Test files ending with _test.py
        r".*\/tests?\/",  # Test directories
        r"spec_.*\.py",  # Spec files
        r".*_spec\.py",  # Spec files
        r".*\/spec\/",  # Spec directories
        
        # CI/CD and automation (critical)
        r"\.github\/",  # GitHub workflows
        r"\.gitlab.*",  # GitLab CI
        r"\.travis\.yml",  # Travis CI
        r"jenkins.*",  # Jenkins files
        r"\.circleci\/",  # CircleCI
        r"azure-pipelines.*",  # Azure DevOps
        
        # Package and dependency management (high risk)
        r"setup\.py",  # Setup files
        r"setup\.cfg",  # Setup config
        r"pyproject\.toml",  # Project config
        r"requirements.*\.txt",  # Dependencies
        r"Pipfile.*",  # Pipenv files
        r"poetry\.lock",  # Poetry lock
        r"package.*\.json",  # Node packages
        r"Gemfile.*",  # Ruby gems
        r"go\.mod",  # Go modules
        r"Cargo\.toml",  # Rust cargo
        
        # Security and secrets (critical)
        r"\.env.*",  # Environment files
        r".*\.key",  # Key files
        r".*\.pem",  # Certificate files
        r".*\.crt",  # Certificate files
        r".*secrets.*",  # Secret files
        r".*credentials.*",  # Credential files
        r".*token.*",  # Token files
        r".*password.*",  # Password files
        
        # Version control (protected)
        r"\.git\/",  # Git directory
        r"\.gitignore",  # Gitignore
        r"\.gitmodules",  # Git submodules
    ]
    
    # Enhanced suspicious code patterns
    SUSPICIOUS_CODE_PATTERNS: ClassVar[List[str]] = [
        # Code execution (dangerous)
        r"exec\s*\(",
        r"eval\s*\(",
        r"compile\s*\(",
        r"__import__",
        
        # System commands (dangerous)
        r"os\.system\s*\(",
        r"subprocess\.(call|run|Popen)\s*\(",
        r"shell\s*=\s*True",
        
        # File system operations (risky)
        r"shutil\.rmtree",
        r"os\.remove",
        r"os\.unlink",
        r"rm\s+-rf",
        r"del\s+\/",
        
        # Network operations (suspicious)
        r"urllib.*urlopen",
        r"requests\.(get|post|put|delete)",
        r"socket\.",
        
        # Database operations (careful)
        r"DROP\s+(TABLE|DATABASE)",
        r"DELETE\s+FROM",
        r"TRUNCATE",
        
        # Dangerous Python operations
        r"globals\s*\(\)",
        r"locals\s*\(\)",
        r"setattr\s*\(",
        r"delattr\s*\(",
        r"__dict__",
        
        # Crypto mining patterns
        r"bitcoin",
        r"ethereum",
        r"monero",
        r"crypto.*mine",
    ]
    
    def __init__(self, verbose: bool = False, llm: Optional[Any] = None, state: Optional[Any] = None, **kwargs):
        """Initialize with optional LLM for semantic review and agent state."""
        if verbose is not False:
            kwargs['verbose'] = verbose
        
        # Store agent state for tracking reviews
        if state is not None:
            kwargs['state'] = state
        
        # Initialize LLM if not provided and API key is available
        if llm is not None:
            kwargs['llm'] = llm
        else:
            # Only create LLM if API key is available
            import os
            if os.getenv("OPENAI_API_KEY"):
                try:
                    from langchain_openai import ChatOpenAI
                except ImportError:
                    from langchain.chat_models import ChatOpenAI
                kwargs['llm'] = ChatOpenAI(model_name="gpt-4", temperature=0.1)
            else:
                # No LLM for critic review in mock mode
                kwargs['llm'] = None
        
        super().__init__(**kwargs)
    
    def _check_safety(self, patch_diff: str) -> tuple[bool, str]:
        """
        Perform comprehensive safety checks on the patch.
        
        Returns:
            Tuple of (is_safe, reason)
        """
        lines = patch_diff.split("\n")
        
        # Track statistics for comprehensive analysis
        files_modified = set()
        added_lines = 0
        removed_lines = 0
        
        # Check for forbidden file modifications
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
                    
                    files_modified.add(file_path)
                    
                    # Check against forbidden patterns
                    for pattern in self.FORBIDDEN_PATTERNS:
                        if re.search(pattern, file_path, re.IGNORECASE):
                            return False, f"Modifies forbidden file: {file_path} (matches pattern: {pattern})"
            
            # Count additions and deletions
            elif line.startswith("+") and not line.startswith("+++"):
                added_lines += 1
            elif line.startswith("-") and not line.startswith("---"):
                removed_lines += 1
        
        # Check number of files modified
        if len(files_modified) > 10:
            return False, f"Too many files modified: {len(files_modified)} (max: 10)"
        
        # Check patch size limits
        total_changes = added_lines + removed_lines
        if total_changes > 500:
            return False, f"Patch too large: {added_lines} additions, {removed_lines} deletions (total: {total_changes}, max: 500)"
        
        if added_lines > 300:
            return False, f"Too many additions: {added_lines} (max: 300)"
        
        if removed_lines > 300:
            return False, f"Too many deletions: {removed_lines} (max: 300)"
        
        # Check for suspicious code patterns in additions
        for line in lines:
            if line.startswith("+") and not line.startswith("+++"):
                # Check each suspicious pattern
                for pattern in self.SUSPICIOUS_CODE_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Extract context for better error message
                        code_snippet = line[1:].strip()[:50]  # First 50 chars after +
                        return False, f"Suspicious code pattern detected: '{pattern}' in line: {code_snippet}..."
        
        # Additional checks for specific dangerous operations
        patch_text = "\n".join(lines)
        
        # Check for attempts to disable safety features
        if re.search(r"BLOCKED_PATTERNS\s*=\s*\[\]", patch_text):
            return False, "Attempt to disable safety patterns detected"
        
        # Check for environment variable access that might leak secrets
        if re.search(r"os\.environ\.get\(['\"].*KEY.*['\"]", patch_text, re.IGNORECASE):
            return False, "Potential secret key access detected"
        
        # All checks passed
        return True, f"Safety checks passed ({len(files_modified)} files, {added_lines} additions, {removed_lines} deletions)"
    
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
            # Update state to indicate rejection
            if self.state:
                self.state.last_review_approved = False
                self.state.last_reviewed_patch = patch_diff
                self.state.critic_feedback = safety_reason
            return f"REJECTED: {safety_reason}"
        
        # Then, run LLM review if available
        if self.llm:
            approved, llm_reason = self._llm_review(patch_diff, failing_tests)
            
            # Update state based on review result
            if self.state:
                self.state.last_review_approved = approved
                self.state.last_reviewed_patch = patch_diff
                self.state.pending_patch = patch_diff if approved else None
                if not approved:
                    self.state.critic_feedback = llm_reason
            
            if approved:
                return f"APPROVED: {llm_reason}"
            else:
                return f"REJECTED: {llm_reason}"
        else:
            # If no LLM, approve based on safety checks alone
            if self.state:
                self.state.last_review_approved = True
                self.state.last_reviewed_patch = patch_diff
                self.state.pending_patch = patch_diff
            return f"APPROVED: {safety_reason}"
    
    async def _arun(self, patch_diff: str, failing_tests: Optional[str] = None) -> str:
        """Async version not implemented."""
        raise NotImplementedError("CriticReviewTool does not support async execution")


# --- Convenience Functions for Tool Creation ---

def create_default_tools(
    repo_path: Optional[Path] = None,
    verbose: bool = False,
    safety_config: Optional[SafetyConfig] = None,
    llm: Optional[Any] = None,
    state: Optional[Any] = None
) -> List[BaseTool]:
    """
    Create the default set of tools for the Deep Agent (v1.1).
    
    Provides all tools needed for the ReAct-style agent to fix failing tests:
    - plan_todo: Record planning steps
    - open_file: Read source files with safety checks
    - write_file: Modify source files with safety checks
    - run_tests: Execute tests in Docker sandbox
    - apply_patch: Apply unified diff patches with validation
    - critic_review: Review patches before application
    
    Args:
        repo_path: Repository path for tools that need it
        verbose: Enable verbose output
        safety_config: Safety configuration for patch application
        llm: LLM instance for critic review (optional)
    
    Returns:
        List of tool instances ready for use in LangChain agent
    """
    tools = []
    
    # Add tools with defined schemas for consistent function calling
    tools.append(PlanTodoTool())
    tools.append(OpenFileTool())
    tools.append(WriteFileTool())
    
    # Add class-based tools
    tools.append(RunTestsTool(
        repo_path=repo_path,
        verbose=verbose
    ))
    
    tools.append(ApplyPatchTool(
        repo_path=repo_path,
        safety_config=safety_config,
        verbose=verbose,
        state=state
    ))
    
    tools.append(CriticReviewTool(
        verbose=verbose,
        llm=llm,
        state=state
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
