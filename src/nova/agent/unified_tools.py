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

def plan_todo(input: str) -> str:
    """Plan next steps. The agent uses this to outline a TODO list or strategy."""
    # This tool is a no-op that just records the plan in the agent's log.
    # Store the plan (in real implementation, this would save to state)
    return "Plan recorded. Continue with the next action."


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
    state: Optional[Any] = None
    
    def _run(self, todo: str) -> str:
        """Execute the plan_todo function."""
        # Check for duplicate plan with same todo and no new changes
        if self.state and (self.name, todo, self.state.modifications_count) in self.state.used_actions:
            return f"Plan already noted: {todo}"  # Skip duplicate plan
        
        # Update phase to implementing after planning
        if self.state and hasattr(self.state, 'phase'):
            self.state.phase = 'implementing'
        
        # Record this action
        if self.state:
            self.state.used_actions.add((self.name, todo, self.state.modifications_count))
        
        # Store the plan (in real implementation, this would save to state)
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
    settings: Optional[Any] = None  # Store Nova settings
    state: Optional[Any] = None  # Agent state for loop prevention
    
    def _run(self, path: str) -> str:
        """Execute the open_file function with safety checks."""
        # Check for duplicate file read with no new changes
        if self.state and (self.name, path, self.state.modifications_count) in self.state.used_actions:
            return f"ERROR: File already opened (duplicate invocation skipped)"
        
        # Same logic as the original open_file function, with safety guardrails
        import fnmatch
        import os
        p = Path(path)
        path_str = str(p)
        
        # First check if this is a test file
        is_test_file = any(part.startswith('test') for part in p.parts) or p.name.startswith('test_') or p.name.endswith('_test.py')
        
        # If it's a test file, check if we're allowed to read it
        if is_test_file:
            allow_test_read = True  # Default to True
            if self.settings and hasattr(self.settings, 'allow_test_file_read'):
                allow_test_read = self.settings.allow_test_file_read
            
            if allow_test_read:
                # Skip BLOCKED_PATTERNS check for test files when read is allowed
                pass
            else:
                # Provide helpful guidance when test files are blocked
                hint = ""
                if "test_broken.py" in path:
                    hint = "\nHINT: Look for source file: broken.py or src/broken.py"
                elif path.endswith('_test.py'):
                    module_name = path.replace('_test.py', '.py')
                    hint = f"\nHINT: Look for source file: {module_name}"
                elif path.startswith('test_'):
                    module_name = path.replace('test_', '', 1)
                    hint = f"\nHINT: Look for source file: {module_name}"
                return f"ERROR: Access to test file {path} is blocked by policy. Use error messages to understand what to fix.{hint}"
        else:
            # For non-test files, check BLOCKED_PATTERNS
            for pattern in BLOCKED_PATTERNS:
                if ('*' in pattern or '?' in pattern):
                    if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(p.name, pattern):
                        return f"ERROR: Access to {path} is blocked by policy (pattern: {pattern})"
                else:
                    if pattern in path_str or p.name == pattern:
                        return f"ERROR: Access to {path} is blocked by policy"
        
        # If we reach here, access is allowed - read the file
        if is_test_file:
            # If it's a test file that we're allowed to read, add a header comment
            try:
                content = p.read_text()
                if len(content) > 50000:  # 50KB limit
                    content = content[:50000] + "\n... (truncated)"
                # Record successful file read
                if self.state:
                    self.state.used_actions.add((self.name, path, self.state.modifications_count))
                return f"# TEST FILE (READ-ONLY): {path}\n# DO NOT MODIFY TEST FILES - Fix the source code to make tests pass\n\n{content}"
            except FileNotFoundError:
                if self.state:
                    self.state.used_actions.add((self.name, path, self.state.modifications_count))
                return f"ERROR: File not found: {path}"
            except PermissionError:
                if self.state:
                    self.state.used_actions.add((self.name, path, self.state.modifications_count))
                return f"ERROR: Permission denied: {path}"
            except Exception as e:
                if self.state:
                    self.state.used_actions.add((self.name, path, self.state.modifications_count))
                return f"ERROR: Could not read file {path}: {e}"
        
        # For non-test files, read normally
        try:
            content = p.read_text()
            if len(content) > 50000:  # 50KB limit
                content = content[:50000] + "\n... (truncated)"
            # Record successful file read
            if self.state:
                self.state.used_actions.add((self.name, path, self.state.modifications_count))
            return content
        except FileNotFoundError:
            if self.state:
                self.state.used_actions.add((self.name, path, self.state.modifications_count))
            return f"ERROR: File not found: {path}"
        except PermissionError:
            if self.state:
                self.state.used_actions.add((self.name, path, self.state.modifications_count))
            return f"ERROR: Permission denied: {path}"
        except Exception as e:
            if self.state:
                self.state.used_actions.add((self.name, path, self.state.modifications_count))
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
    state: Optional[Any] = None  # Agent state for loop prevention
    
    def _run(self, path: str, new_content: str) -> str:
        """Execute the write_file function with safety checks."""
        # Check for duplicate write with same content and no new changes
        if self.state and (self.name, path, new_content, self.state.modifications_count) in self.state.used_actions:
            return f"SUCCESS: File {path} already up-to-date (duplicate write skipped)"
        
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
            # Record successful write and increment modifications count
            if self.state:
                self.state.used_actions.add((self.name, path, new_content, self.state.modifications_count))
                self.state.modifications_count += 1  # Count this modification
            return f"SUCCESS: File {path} updated successfully"
        except PermissionError:
            if self.state:
                self.state.used_actions.add((self.name, path, new_content, self.state.modifications_count))
            return f"ERROR: Permission denied: {path}"
        except Exception as e:
            if self.state:
                self.state.used_actions.add((self.name, path, new_content, self.state.modifications_count))
            return f"ERROR: Could not write to file {path}: {e}"
    
    async def _arun(self, path: str, new_content: str) -> str:
        """Async version not implemented."""
        raise NotImplementedError("WriteFileTool does not support async execution")


# --- Class-based Tools (Complex Operations) ---

class RunTestsTool(BaseTool):
    """
    Tool to run tests and collect failing test details.
    
    Combines Docker sandbox execution with local fallback and
    provides formatted output for the agent.
    """
    name: str = "run_tests"
    description: str = (
        "Run the project's test suite inside a sandbox and get failing test info. "
        "Returns a summary with test names and error messages. "
        "No input required - just call run_tests"
    )
    # No args_schema - makes it accept any input including empty string
    repo_path: Path = Field(default_factory=lambda: Path("."))
    verbose: bool = Field(default=False)
    # NEW: Allow injection of telemetry logger and settings if needed
    logger: Optional[JSONLLogger] = Field(default=None)
    use_docker: bool = Field(default=True)
    state: Optional[Any] = Field(default=None)  # Agent state for loop prevention

    def __init__(self, repo_path: Optional[Path] = None, verbose: bool = False,
                 logger: Optional[JSONLLogger] = None, use_docker: bool = True, 
                 state: Optional[Any] = None, **kwargs):
        """Initialize with repository path and optional logger."""
        if repo_path is not None:
            kwargs['repo_path'] = Path(repo_path)
        if verbose:
            kwargs['verbose'] = True
        if logger is not None:
            kwargs['logger'] = logger
        kwargs['use_docker'] = use_docker
        if state is not None:
            kwargs['state'] = state
        super().__init__(**kwargs)

    def _run(self, *args, **kwargs) -> str:
        """Execute tests and return a JSON summary of results."""
        # Extract max_failures from kwargs or use default
        max_failures = kwargs.get('max_failures', 5)
        if args and isinstance(args[0], int):
            max_failures = args[0]
        
        # Check for duplicate test run with no new code changes
        if self.state and (self.name, str(max_failures), self.state.modifications_count) in self.state.used_actions:
            # Skip duplicate test run with no new code changes
            if self.verbose:
                print("⚠️ Skipping redundant test run (no code changes since last run)")
            return json.dumps({
                "exit_code": 1,
                "failures": self.state.total_failures or 0,
                "message": "No changes since last run - tests not re-run",
                "failing_tests": [],
                "error": "Duplicate test run skipped"
            })
        
        # Ensure .nova directory for test artifacts exists
        nova_path = self.repo_path / ".nova"
        nova_path.mkdir(exist_ok=True)
        
        # Initialize result variables
        result = None
        docker_error = None
        
        # Determine whether to use Docker sandbox
        if self.use_docker and shutil.which("docker") is not None:
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
                    # Include stderr in error for debugging
                    docker_error += f" (stderr: {proc.stderr.strip()[:200]})"
                else:
                    try:
                        result = json.loads(stdout)
                    except json.JSONDecodeError:
                        docker_error = "Non-JSON output from tests"
                        # Save a snippet of raw output for context
                        docker_error += f" (output starts: {stdout[:100]}...)"
                        
            except subprocess.TimeoutExpired:
                docker_error = "Test execution timed out"
            except Exception as e:
                docker_error = f"Docker test run failed: {e}"
        else:
            if self.use_docker and shutil.which("docker") is None:
                # Docker was desired but not available
                docker_error = "Docker not available"
            # If Docker not used or failed, fall back to local execution
        
        if docker_error:
            if self.verbose:
                print(f"⚠️ Sandbox unavailable – running tests locally. Reason: {docker_error}")
            # Log the fallback event
            if self.logger:
                self.logger.log_event("sandbox_fallback", {
                    "reason": docker_error
                })
            
            try:
                from nova.runner.test_runner import TestRunner
                runner = TestRunner(self.repo_path, verbose=self.verbose)
                failing_tests, junit_xml = runner.run_tests(max_failures=max_failures)
                
                if not failing_tests:
                    # All tests passing, set result dict
                    result = {
                        "exit_code": 0,
                        "failures": 0,
                        "passed": "unknown",  # We don't have the count from the runner
                        "message": "All tests passed",
                        "failing_tests": []
                    }
                else:
                    # Format local runner results as dict
                    failures_json = []
                    for test in failing_tests[:max_failures]:
                        failures_json.append({
                            "name": test.name if hasattr(test, 'name') else "unknown",
                            "error": (test.short_traceback.split("\n")[0][:500] 
                                     if hasattr(test, 'short_traceback') else "Unknown error"),
                            "traceback": (test.short_traceback[:1000] 
                                         if hasattr(test, 'short_traceback') else "")
                        })
                    
                    result = {
                        "exit_code": 1,
                        "failures": len(failing_tests),
                        "passed": 0,  # We don't have the count from the runner
                        "message": f"{len(failing_tests)} test(s) failed",
                        "failing_tests": failures_json
                    }
                
            except Exception as e:
                # Set error result dict
                # Local test run failed (e.g., test runner internal error)
                result = {
                    "exit_code": 1,
                    "error": f"Test execution failed: {e}",
                    "failures": 0,
                    "passed": 0
                }
        
        # Ensure result is a dict by this point
        if result is None:
            # Docker path set result only if tests failed (exit_code 1). If it's still None, treat as error.
            result = {
                "exit_code": 1,
                "error": docker_error or "Unknown error",
                "failures": 0,
                "passed": 0
            }
        
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
        
        # Flake detection: Re-run failing tests to check if they're flaky
        if failures and len(failures) <= 10:  # Only check if reasonable number of failures
            flaky_tests, consistent_test_names = self._detect_flaky_tests(failures)
            
            if flaky_tests:
                # Remove flaky tests from the failures list
                failures = [f for f in failures if f.get("name") not in flaky_tests]
                
                # Update the result message
                flaky_count = len(flaky_tests)
                real_failure_count = len(failures)
                
                if real_failure_count == 0:
                    # All failures were flaky
                    result["exit_code"] = 0
                    result["message"] = f"All tests passed ({flaky_count} flaky test(s) ignored)"
                else:
                    result["message"] = f"{real_failure_count} test(s) failed, {flaky_count} flaky test(s) ignored"
                
                # Add flaky tests to result for transparency
                result["flaky_tests"] = flaky_tests
                
                # Log flaky test detection
                if self.logger:
                    self.logger.log_event("flaky_tests_detected", {
                        "count": flaky_count,
                        "tests": flaky_tests
                    })
        
        # Log the test results event for telemetry
        if self.logger:
            evt = {"exit_code": result.get("exit_code", 1)}
            if "failures" in result:
                evt["failures"] = len(failures)  # Use updated failure count
                evt["passed"] = result.get("passed", 0)
            if "error" in result:
                evt["error"] = result["error"]
            if "flaky_tests" in result:
                evt["flaky_tests"] = result["flaky_tests"]
            self.logger.log_event("test_run_completed", evt)
        
        # Build final result
        final_result = {
            "exit_code": result.get("exit_code", 1),
            "failures": len(failures),
            "passed": result.get("test_summary", {}).get("passed", 0) if result.get("test_summary") else 0,
            "message": result.get("message", f"{len(failures)} test(s) failed"),
            "failing_tests": failures[:max_failures]
        }
        
        # Include flaky tests if any were detected
        if "flaky_tests" in result:
            final_result["flaky_tests"] = result["flaky_tests"]
        
        # Record this test run
        if self.state:
            self.state.used_actions.add((self.name, str(max_failures), self.state.modifications_count))
        
        # Return JSON with failure details
        return json.dumps(final_result)

    def _detect_flaky_tests(self, failing_tests: list) -> tuple[list, list]:
        """Detect flaky tests by re-running them once.
        
        Returns:
            (flaky_tests, consistent_failures): Lists of test names
        """
        flaky_tests = []
        consistent_failures = []
        
        if not failing_tests or len(failing_tests) > 10:
            # Skip flake detection if too many failures (likely not flaky)
            return [], [test.get("name", "unknown") for test in failing_tests]
        
        if self.verbose:
            print("\n[DEBUG] Checking for flaky tests by re-running failures...")
        
        for test in failing_tests:
            test_name = test.get("name", "")
            if not test_name or " " in test_name or "::" not in test_name:
                # Skip if we don't have a reliable test identifier
                consistent_failures.append(test_name)
                continue
                
            try:
                # Re-run the single test
                cmd = ["pytest", "-q", "-x", test_name]
                proc = subprocess.run(
                    cmd, 
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60  # Shorter timeout for single test
                )
                
                if proc.returncode == 0:
                    # Test passed on retry - it's flaky
                    flaky_tests.append(test_name)
                    if self.verbose:
                        print(f"  ✓ {test_name} - FLAKY (passed on retry)")
                else:
                    # Test failed again - it's a real failure
                    consistent_failures.append(test_name)
                    if self.verbose:
                        print(f"  ✗ {test_name} - CONSISTENT failure")
                        
            except subprocess.TimeoutExpired:
                # Timeout - treat as consistent failure
                consistent_failures.append(test_name)
                if self.verbose:
                    print(f"  ⏱ {test_name} - TIMEOUT (treating as failure)")
            except Exception as e:
                # Any other error - treat as consistent failure
                consistent_failures.append(test_name)
                if self.verbose:
                    print(f"  ⚠ {test_name} - ERROR during retry: {e}")
        
        return flaky_tests, consistent_failures

    async def _arun(self, *args, **kwargs) -> str:
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
    state: Optional[Any] = Field(default=None)

    def __init__(
        self,
        repo_path: Optional[Path] = None,
        safety_config: Optional[Any] = None,
        verbose: bool = False,
        logger: Optional[JSONLLogger] = None,
        state: Optional[Any] = None,
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
        if state is not None:
            kwargs['state'] = state
        
        super().__init__(**kwargs)

    def _run(self, patch_diff: str) -> str:
        """Apply the given patch diff to the codebase with safety checks."""
        # Check for duplicate patch application
        if self.state and (self.name, patch_diff, self.state.modifications_count) in self.state.used_actions:
            return "SUCCESS: Patch already applied (duplicate skipped)"
        
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
            # Log safety violation
            if self.logger:
                self.logger.log_event("patch_rejected", {
                    "reason": f"Safety violation – {safe_msg}"
                })
            return f"FAILED: Safety violation – {safe_msg}"
        
        # 1.5. Test verification warning - check if tests may still be failing
        if self.state and hasattr(self.state, 'total_failures'):
            if self.state.total_failures > 0:
                # Initial failures exist, warn that tests should be passing before applying
                if self.verbose:
                    print("⚠️  [ApplyPatchTool] Warning: Tests may still be failing.")
                    print("    Ensure run_tests shows all passing before applying patches.")
                if self.logger:
                    self.logger.log_event("patch_apply_warning", {
                        "type": "tests_may_be_failing",
                        "initial_failures": self.state.total_failures
                    })
        
        # 1.6. Critic review check (enforce review before applying)
        # Check if we have state-based review tracking
        if self.state and hasattr(self.state, 'last_review_approved'):
            # Check if this exact patch was already reviewed and approved
            if hasattr(self.state, 'last_reviewed_patch') and self.state.last_reviewed_patch:
                normalized_input = '\n'.join(line.rstrip() for line in patch_text.strip().split('\n'))
                normalized_reviewed = '\n'.join(line.rstrip() for line in self.state.last_reviewed_patch.strip().split('\n'))
                
                if normalized_input == normalized_reviewed and self.state.last_review_approved:
                    # This patch was already reviewed and approved, proceed
                    if self.verbose:
                        print("✓ Patch was already reviewed and approved")
                else:
                    # Patch not reviewed or different from reviewed patch - run critic now
                    if self.verbose:
                        print("Running critic review on patch before applying...")
                    critic_tool = CriticReviewTool(
                        verbose=self.verbose, 
                        llm=getattr(self, 'llm', None),
                        state=self.state
                    )
                    review_result = critic_tool._run(patch_text)
                    if review_result.startswith("REJECTED"):
                        reason = review_result.split(':', 1)[1].strip() if ':' in review_result else review_result
                        if self.verbose:
                            print(f"Critic rejected patch: {reason}")
                        if self.logger:
                            self.logger.log_event("patch_rejected", {
                                "reason": f"Critic rejection – {reason}"
                            })
                        return f"FAILED: Patch rejected by critic - {reason}"
        else:
            # No state tracking available - run critic review inline
            if self.verbose:
                print("Running critic review on patch...")
            critic_tool = CriticReviewTool(verbose=self.verbose, llm=getattr(self, 'llm', None))
            review_result = critic_tool._run(patch_text)
            if review_result.startswith("REJECTED"):
                reason = review_result.split(':', 1)[1].strip() if ':' in review_result else review_result
                if self.verbose:
                    print(f"Critic rejected patch: {reason}")
                if self.logger:
                    self.logger.log_event("patch_rejected", {
                        "reason": f"Critic rejection – {reason}"
                    })
                return f"FAILED: Patch rejected by critic - {reason}"
        
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
                
                # Fallback: apply patch by writing files directly
                fallback_success = True
                file_edits = []  # track files edited for logging
                
                try:
                    lines = patch_text.splitlines()
                    i = 0
                    while i < len(lines):
                        # Identify new file header in diff
                        if lines[i].startswith("+++ "):
                            new_file = lines[i][4:].strip()
                            if new_file.startswith("/dev/null"):
                                # skip deletions
                                i += 1
                                continue
                            # Normalize path (remove "b/" prefix if present)
                            if new_file.startswith("b/") or new_file.startswith("a/"):
                                new_file = new_file[2:]
                            
                            # Collect all lines for new file content
                            content_lines = []
                            i += 1
                            
                            # Advance to hunk content (skip context lines until @@)
                            while i < len(lines) and not lines[i].startswith("@@"):
                                i += 1
                            
                            while i < len(lines):
                                if lines[i].startswith("diff --git") or lines[i].startswith("+++"):
                                    break  # next file diff begins
                                elif lines[i].startswith("@@"):
                                    i += 1
                                    continue  # skip hunk header
                                elif lines[i].startswith("+"):
                                    # Added line
                                    content_lines.append(lines[i][1:])
                                elif lines[i].startswith(" "):
                                    # Context line
                                    content_lines.append(lines[i][1:])
                                # Skip lines starting with '-' (removed lines)
                                i += 1
                            
                            # Write the reconstructed new content to the file
                            file_path = Path(self.repo_path) / new_file
                            file_path.parent.mkdir(parents=True, exist_ok=True)
                            file_path.write_text("\n".join(content_lines))
                            file_edits.append(new_file)
                        else:
                            i += 1
                            
                except Exception as fe:
                    fallback_success = False
                    if self.verbose:
                        print(f"Fallback patch application failed: {fe}")
                    if self.logger:
                        self.logger.log_event("patch_fallback_failed", {
                            "reason": str(fe),
                            "details": str(fe)[:200]
                        })
                
                if fallback_success and file_edits:
                    # Stage and commit the changes as a single patch
                    subprocess.run(["git", "add", "-A"], cwd=self.repo_path, check=False)
                    commit_proc = subprocess.run(
                        ["git", "commit", "-m", "Apply patch (fallback) from Nova Deep Agent"],
                        cwd=self.repo_path,
                        capture_output=True,
                        text=True
                    )
                    
                    if commit_proc.returncode != 0 and "nothing to commit" not in commit_proc.stdout:
                        if self.verbose:
                            print(f"Git commit warning: {commit_proc.stdout}")
                    
                    if self.state:
                        self.state.last_review_approved = False
                        self.state.last_reviewed_patch = None
                        self.state.pending_patch = None
                        self.state.patches_applied.append(patch_text)
                        self.state.modifications_count += 1
                        self.state.used_actions.add((self.name, patch_diff, self.state.modifications_count))
                    
                    if self.verbose:
                        edited_list = ", ".join(file_edits)
                        print(f"✓ Patch applied via fallback to files: {edited_list}")
                    
                    if self.logger:
                        self.logger.log_event("patch_applied_fallback", {
                            "files_edited": file_edits,
                            "reason": "Context mismatch - used fallback"
                        })
                    
                    return "SUCCESS: Patch applied successfully (fallback used)"
                else:
                    # Fallback also failed
                    if self.logger:
                        self.logger.log_event("patch_apply_failed", {
                            "reason": "Context mismatch/preflight failed and fallback failed",
                            "details": preflight.stderr.strip()[:200]
                        })
                    if self.state:
                        self.state.final_status = "patch_error"
                    return "FAILED: Patch could not be applied (even with fallback)."
            
            # 3. Apply patch
            apply_proc = subprocess.run(
                ["git", "apply", "--whitespace=nowarn", tmp_file.name],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if apply_proc.returncode != 0:
                if self.verbose:
                    print(f"git apply failed: {apply_proc.stderr.strip()}")
                if self.logger:
                    self.logger.log_event("patch_apply_failed", {
                        "reason": "Git apply error",
                        "details": apply_proc.stderr.strip()[:200]
                    })
                # Update state to indicate patch error
                if self.state:
                    self.state.final_status = "patch_error"
                return f"FAILED: Could not apply patch: {apply_proc.stderr}"
            
            # 4. Commit changes
            subprocess.run(["git", "add", "-A"], cwd=self.repo_path, check=False)
            
            # Create commit message with iteration number
            iteration_num = 1
            if self.state and hasattr(self.state, 'current_iteration'):
                iteration_num = self.state.current_iteration + 1
            commit_msg = f"Apply patch from Nova Deep Agent (iteration {iteration_num})"
            
            commit_proc = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if commit_proc.returncode != 0:
                # Commit failed (e.g., no changes to commit)
                if self.verbose:
                    print(f"git commit failed: {commit_proc.stderr.strip()}")
                if self.logger:
                    self.logger.log_event("patch_apply_failed", {
                        "reason": "Git commit failed",
                        "details": commit_proc.stderr.strip()
                    })
                if self.state:
                    self.state.final_status = "patch_error"
                return f"FAILED: Patch applied but not committed: {commit_proc.stderr.strip()}"
            
            # 5. Success! Update state to clear the review
            if self.state:
                # Reset review approval for next patch cycle
                if hasattr(self.state, 'last_review_approved'):
                    self.state.last_review_approved = False
                if hasattr(self.state, 'last_reviewed_patch'):
                    self.state.last_reviewed_patch = None
                if hasattr(self.state, 'pending_patch'):
                    self.state.pending_patch = None
                if hasattr(self.state, 'patches_applied'):
                    self.state.patches_applied.append(patch_text)
                # Increment iteration count for tracking
                if hasattr(self.state, 'current_iteration'):
                    self.state.current_iteration += 1
            if self.logger:
                self.logger.log_event("patch_applied", {
                    "message": "Patch applied successfully",
                    "lines_changed": patch_text.count("\n+") + patch_text.count("\n-")
                })
            if self.verbose:
                print("✅ Patch applied and committed successfully.")
            return "SUCCESS: Patch applied successfully."
            
        except Exception as e:
            if self.logger:
                self.logger.log_event("patch_apply_failed", {
                    "reason": f"Exception during apply: {e}"
                })
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
            # Combine system and user prompts since predict doesn't accept system parameter
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = self.llm.predict(combined_prompt)
            
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


class CodeSearchInput(BaseModel):
    """Input schema for CodeSearchTool."""
    query: str = Field(..., description="Keyword or regex to search for in the codebase")
    max_results: int = Field(10, description="Maximum number of results to return")


class CodeSearchTool(BaseTool):
    """
    Tool to search the repository's source code for keywords or patterns.
    
    Helps locate function definitions, class implementations, or error strings.
    """
    name: str = "search_code"
    description: str = (
        "Search the repository's source code for a given query string. "
        "Use this to find where functions, classes, or errors are defined. "
        "Returns a brief list of file names and snippets matching the query. "
        "Note: Test files and certain paths are excluded for safety."
    )
    args_schema: Type[BaseModel] = CodeSearchInput
    repo_path: Path = Field(default_factory=lambda: Path("."))
    verbose: bool = Field(default=False)
    
    def __init__(self, repo_path: Optional[Path] = None, verbose: bool = False, **kwargs):
        """Initialize with repository path."""
        if repo_path is not None:
            kwargs['repo_path'] = Path(repo_path)
        kwargs['verbose'] = verbose
        super().__init__(**kwargs)
    
    def _run(self, query: str, max_results: int = 10) -> str:
        """Search for the query in the codebase."""
        import re
        import fnmatch
        
        results = []
        query_regex = None
        try:
            # Treat query as a case-insensitive regex
            query_regex = re.compile(query, re.IGNORECASE)
        except re.error:
            # If query is not a valid regex, escape it
            query_regex = re.compile(re.escape(query), re.IGNORECASE)
        
        # Walk through files
        for file_path in self.repo_path.rglob("*"):
            if len(results) >= max_results:
                break
            
            if not file_path.is_file():
                continue
                
            rel_path = str(file_path.relative_to(self.repo_path))
            
            # Skip blocked patterns
            skip = False
            for pattern in BLOCKED_PATTERNS:
                # Use fnmatch for glob patterns
                if "*" in pattern or "?" in pattern:
                    if fnmatch.fnmatch(rel_path, pattern):
                        skip = True
                        break
                else:
                    if pattern in rel_path:
                        skip = True
                        break
            
            if skip:
                continue
            
            # Skip binary files by extension
            if file_path.suffix.lower() in [".pyc", ".png", ".jpg", ".jpeg", ".gif", 
                                             ".pdf", ".exe", ".so", ".dylib", ".dll",
                                             ".zip", ".tar", ".gz", ".bz2", ".7z"]:
                continue
            
            try:
                text = file_path.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            
            # Search for matches
            matches = list(query_regex.finditer(text))
            if matches:
                # Find line number and snippet for first match
                lines = text.splitlines()
                for i, line in enumerate(lines, start=1):
                    if query_regex.search(line):
                        snippet = line.strip()
                        if len(snippet) > 100:
                            snippet = snippet[:97] + "..."
                        results.append(f"{rel_path}:{i}: {snippet}")
                        break
        
        if not results:
            return "No results found for query."
        
        # Format output
        output = "Found matches:\n" + "\n".join(results[:max_results])
        if len(results) > max_results:
            output += f"\n...and {len(results) - max_results} more."
        
        return output
    
    async def _arun(self, query: str, max_results: int = 10) -> str:
        """Async version not implemented."""
        raise NotImplementedError("CodeSearchTool does not support async execution")


class RunSingleTestInput(BaseModel):
    """Input schema for RunSingleTestTool."""
    test_name: str = Field(..., description="The specific test identifier or file::name to run")


class RunSingleTestTool(BaseTool):
    """
    Tool to run a single test for focused debugging.
    
    Useful for quick iteration on specific failing tests.
    """
    name: str = "run_test"
    description: str = (
        "Run a specific test (by name or file::test_id) to get its result. "
        "Use this to retest a single failing test for more details or after a fix. "
        "Example: 'tests/test_math.py::test_addition' or 'test_math.py'"
    )
    args_schema: Type[BaseModel] = RunSingleTestInput
    repo_path: Path = Field(default_factory=lambda: Path("."))
    verbose: bool = Field(default=False)
    logger: Optional[JSONLLogger] = Field(default=None)
    
    def __init__(self, repo_path: Optional[Path] = None, verbose: bool = False, 
                 logger: Optional[JSONLLogger] = None, **kwargs):
        """Initialize with repository path and optional logger."""
        if repo_path is not None:
            kwargs['repo_path'] = Path(repo_path)
        kwargs['verbose'] = verbose
        if logger is not None:
            kwargs['logger'] = logger
        super().__init__(**kwargs)
    
    def _run(self, test_name: str) -> str:
        """Run the specific test and return JSON result."""
        import subprocess
        import json
        
        # Build pytest command
        cmd = ["pytest", "-xvs", test_name]
        
        if self.verbose:
            print(f"Running single test: {test_name}")
        
        try:
            proc = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for single test
            )
        except subprocess.TimeoutExpired:
            return json.dumps({
                "exit_code": 124,
                "error": f"Test '{test_name}' timed out after 5 minutes"
            })
        except Exception as e:
            return json.dumps({
                "exit_code": 1,
                "error": f"Failed to run test: {str(e)}"
            })
        
        # Parse output
        output = proc.stdout.strip()
        stderr = proc.stderr.strip()
        
        # Log the test run
        if self.logger:
            self.logger.log_event("single_test_run", {
                "test_name": test_name,
                "exit_code": proc.returncode,
                "passed": proc.returncode == 0
            })
        
        if proc.returncode == 0:
            # Test passed
            return json.dumps({
                "exit_code": 0,
                "message": f"Test {test_name} passed",
                "output": output[-500:] if output else ""  # Last 500 chars
            })
        else:
            # Test failed - extract error info
            error_msg = ""
            full_output = output + "\n" + stderr if stderr else output
            
            # Try to find the actual error in output
            lines = full_output.splitlines()
            for i, line in enumerate(lines):
                if "FAILED" in line or "ERROR" in line or "AssertionError" in line:
                    # Take this line and a few after it
                    error_lines = lines[i:i+10]
                    error_msg = "\n".join(error_lines)[:1000]
                    break
            
            if not error_msg:
                # Fallback to last part of output
                error_msg = full_output[-1000:]
            
            return json.dumps({
                "exit_code": proc.returncode,
                "error": error_msg,
                "test_name": test_name,
                "message": f"Test {test_name} failed"
            })
    
    async def _arun(self, test_name: str) -> str:
        """Async version not implemented."""
        raise NotImplementedError("RunSingleTestTool does not support async execution")


# --- Convenience Functions for Tool Creation ---

def create_default_tools(
    repo_path: Optional[Path] = None,
    verbose: bool = False,
    safety_config: Optional[SafetyConfig] = None,
    llm: Optional[Any] = None,
    state: Optional[Any] = None,
    settings: Optional[Any] = None,
    logger: Optional[JSONLLogger] = None
) -> List[BaseTool]:
    """
    Create the default set of tools for the Deep Agent (v1.1).
    
    Provides all tools needed for the ReAct-style agent to fix failing tests:
    - plan_todo: Record planning steps
    - open_file: Read source files with safety checks
    - write_file: Modify source files with safety checks
    - run_tests: Execute tests in Docker sandbox with flake detection
    - apply_patch: Apply unified diff patches with validation
    - critic_review: Review patches before application
    - search_code: Search codebase for keywords or patterns
    - run_test: Run a single test for focused debugging
    
    Args:
        repo_path: Repository path for tools that need it
        verbose: Enable verbose output
        safety_config: Safety configuration for patch application
        llm: LLM instance for critic review (optional)
        state: Agent state for tracking
        settings: Nova settings for configuration
        logger: Telemetry logger for recording events (optional)
    
    Returns:
        List of tool instances ready for use in LangChain agent
    """
    tools = []
    
    # Import get_settings if no settings provided
    if settings is None:
        from nova.config import get_settings
        settings = get_settings()
    
    # Add tools with defined schemas for consistent function calling
    tools.append(PlanTodoTool())
    tools.append(OpenFileTool(settings=settings))
    tools.append(WriteFileTool())
    
    # Add handler for invalid responses
    def handle_invalid_response(input: str = "") -> str:
        """Handle parsing errors by returning a helpful message."""
        return ("I noticed my previous response had formatting issues. Let me continue with the task. "
                "To proceed, I should use one of the available tools: plan_todo, open_file, write_file, "
                "run_tests, apply_patch, or critic_review.")
    
    # Removed invalid response handler tool - it was causing confusion with GPT-5
    
    # Add class-based tools
    # Get use_docker setting from settings if available
    use_docker = True
    if settings and hasattr(settings, 'use_docker'):
        use_docker = settings.use_docker
    
    tools.append(RunTestsTool(
        repo_path=repo_path,
        verbose=verbose,
        logger=logger,
        use_docker=use_docker
    ))
    
    tools.append(ApplyPatchTool(
        repo_path=repo_path,
        safety_config=safety_config,
        verbose=verbose,
        state=state,
        logger=logger
    ))
    
    tools.append(CriticReviewTool(
        verbose=verbose,
        llm=llm,
        state=state
    ))
    
    # Add new search and test tools
    tools.append(CodeSearchTool(
        repo_path=repo_path,
        verbose=verbose
    ))
    
    tools.append(RunSingleTestTool(
        repo_path=repo_path,
        verbose=verbose,
        logger=logger
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
