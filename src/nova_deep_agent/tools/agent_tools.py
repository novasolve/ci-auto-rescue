"""
Agent Tools for Nova Deep Agent
================================

This module defines four tools that the LangChain agent will use:
- plan_todo: Generate a plan of action
- open_file: Read file contents with path protection
- write_file: Write to files with path protection  
- run_tests: Run tests in a sandboxed Docker container
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional


class AgentTools:
    """Container class for all agent tools."""
    
    def __init__(self, repo_root: Optional[Path] = None):
        """
        Initialize agent tools with repository root.
        
        Args:
            repo_root: Path to repository root. Defaults to current directory.
        """
        self.repo_root = Path(repo_root or ".").resolve()
        
        # Define blocked file names and path substrings for safety
        self.blocked_names = {
            "setup.py", 
            "pyproject.toml", 
            ".env", 
            "requirements.txt",
            "poetry.lock",
            "Pipfile",
            "Pipfile.lock"
        }
        self.blocked_substrings = [
            ".github/", 
            ".git/",
            "__pycache__/",
            ".venv/",
            "venv/",
            "node_modules/"
        ]
        
    def is_path_allowed(self, file_path: str) -> bool:
        """Check if a file path is allowed for access."""
        full_path = (self.repo_root / file_path).resolve()
        
        # Check if path is within repo root
        if not str(full_path).startswith(str(self.repo_root)):
            return False
            
        # Check for blocked substrings
        if any(substr in file_path for substr in self.blocked_substrings):
            return False
            
        # Check for blocked file names
        if Path(file_path).name in self.blocked_names:
            return False
            
        return True
    
    def plan_todo_tool(self, notes: str = "") -> str:
        """Generate a plan of action in a TODO list format."""
        tasks = [
            "Analyze the failing tests and their error messages to identify the root cause.",
            "Determine which source code files are likely responsible for the failures.",
            "Open and inspect those source files to locate the bug or issue.",
            "Modify the code in the identified files to fix the problems.",
            "Run the test suite to verify if all tests pass after the changes."
        ]
        # Return tasks as a numbered list (each task on a new line)
        plan = "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks))
        
        # If notes are provided, prepend them to the plan
        if notes:
            plan = f"Context: {notes}\n\n{plan}"
        
        return plan
    
    def open_file_tool(self, file_path: str) -> str:
        """Read and return the content of the specified file (if allowed)."""
        full_path = (self.repo_root / file_path).resolve()
        
        # Block access if outside repo or targeting protected paths
        if not str(full_path).startswith(str(self.repo_root)):
            return "Error: Access to this path is not allowed (outside repository)."
        
        if any(substr in file_path for substr in self.blocked_substrings):
            return f"Error: Access to this path is not allowed (blocked path)."
        
        if Path(file_path).name in self.blocked_names:
            return f"Error: Access to this file is not allowed (protected file)."
        
        if not full_path.exists():
            return f"Error: File not found: {file_path}"
        
        if not full_path.is_file():
            return f"Error: Path is not a file: {file_path}"
        
        try:
            content = full_path.read_text()
            return content
        except UnicodeDecodeError:
            return f"Error: Could not read file (binary or non-text file): {file_path}"
        except Exception as e:
            return f"Error: Could not read file: {e}"
    
    def write_file_tool(self, file_path: str, new_content: str) -> str:
        """Write the given content to the specified file (if allowed)."""
        full_path = (self.repo_root / file_path).resolve()
        
        # Block writing if outside repo or targeting protected paths
        if not str(full_path).startswith(str(self.repo_root)):
            return "Error: Access to this path is not allowed (outside repository)."
        
        if any(substr in file_path for substr in self.blocked_substrings):
            return f"Error: Access to this path is not allowed (blocked path)."
        
        if Path(file_path).name in self.blocked_names:
            return f"Error: Access to this file is not allowed (protected file)."
        
        try:
            # Ensure directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the content
            full_path.write_text(new_content)
            
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error: Could not write to file: {e}"
    
    def run_tests_tool(self, _: str = "") -> str:
        """Run all tests in a sandboxed container and return JSON results as a string."""
        image = "nova-ci-rescue-sandbox"
        
        # Ensure the .nova directory exists for output (report file)
        nova_dir = self.repo_root / ".nova"
        nova_dir.mkdir(exist_ok=True)
        
        # Build the Docker command
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{str(self.repo_root)}:/workspace:ro",
            "-v", f"{str(nova_dir)}:/workspace/.nova:rw",
            "--memory", "1g",
            "--cpus", "1.0", 
            "--network", "none",
            image,
            "python", "/usr/local/bin/run_python.py", "--pytest"
        ]
        
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
        except subprocess.TimeoutExpired:
            result = {
                "exit_code": 124,
                "stdout": "",
                "stderr": "Docker sandbox timed out after 10 minutes",
                "timeout": True
            }
            return json.dumps(result)
        except FileNotFoundError:
            result = {
                "exit_code": 127,
                "stdout": "",
                "stderr": "Docker command not found. Please ensure Docker is installed.",
                "error": "Docker not available"
            }
            return json.dumps(result)
        
        stdout = proc.stdout.strip()
        
        if stdout:
            # If sandbox printed JSON to stdout, return it directly
            try:
                json.loads(stdout)  # validate JSON format
                return stdout
            except json.JSONDecodeError:
                # Received non-JSON output; include it in an error structure
                result = {
                    "exit_code": proc.returncode,
                    "stdout": stdout,
                    "stderr": proc.stderr.strip(),
                    "error": "Non-JSON output from sandbox"
                }
                return json.dumps(result)
        else:
            # No output from container; return whatever we have from stderr/exit code
            result = {
                "exit_code": proc.returncode,
                "stdout": "",
                "stderr": proc.stderr.strip()
            }
            return json.dumps(result)


# Define the repository root (assuming current working directory is the repo)
REPO_ROOT = Path(".").resolve()

# Define blocked file names and path substrings for safety (no writes/reads to these)
BLOCKED_NAMES = {"setup.py", "pyproject.toml", ".env", "requirements.txt"}
BLOCKED_SUBSTRINGS = [".github/", ".git/"]


def plan_todo_tool(notes: str = "") -> str:
    """Generate a plan of action in a TODO list format."""
    import json
    failures = []
    if notes:
        try:
            data = json.loads(notes)
        except Exception:
            data = None
        if data:
            # Parse failing tests info if present
            if "failing_tests" in data:
                failures = data["failing_tests"]
            elif "tests" in data:
                for t in data["tests"]:
                    if t.get("outcome") in ["failed", "error"]:
                        failures.append({
                            "file": t.get("nodeid", "").split("::")[0],
                            "name": t.get("nodeid", ""),
                            "message": t.get("call", {}).get("longrepr", "")
                        })
    plan_tasks = []
    if failures:
        # Include each failing test with error class, file, and function
        for test in failures:
            file_path = test.get("file", "<unknown file>")
            test_name = test.get("name", "")
            func_name = test_name.split("::")[-1] if "::" in test_name else test_name
            err_msg = test.get("message") or test.get("error") or ""
            err_class = None
            if err_msg:
                import re
                match = re.search(r"(AssertionError|[A-Za-z]+Exception)", err_msg)
                if match:
                    err_class = match.group(1)
            if not err_class and test.get("outcome") in ["failed", "error"]:
                err_class = "Error"
            plan_tasks.append(f"Fix {err_class or 'issue'} in {file_path}::{func_name}")
        plan_tasks.append("Run the test suite to confirm all failures are resolved")
    else:
        # Default plan if no detailed info available
        plan_tasks = [
            "Analyze failing tests and error messages to identify root causes",
            "Determine which source code files are likely responsible for the failures",
            "Open and inspect those files to find the bug",
            "Modify the code in the identified files to fix the issue",
            "Run the test suite to verify all tests pass after the changes"
        ]
        if notes:
            # Include raw context notes if provided
            plan_tasks.insert(0, f"Context: {notes}")
    plan = "\n".join(f"{i+1}. {task}" for i, task in enumerate(plan_tasks))
    return plan


def open_file_tool(file_path: str) -> str:
    """Read and return the content of the specified file (if allowed)."""
    full_path = (REPO_ROOT / file_path).resolve()
    
    # Block access if outside repo or targeting protected paths
    if not str(full_path).startswith(str(REPO_ROOT)):
        return "Error: Access to this path is not allowed (outside repository)."
    
    if any(substr in file_path for substr in BLOCKED_SUBSTRINGS):
        return f"Error: Access to this path is not allowed (blocked path)."
    
    if Path(file_path).name in BLOCKED_NAMES:
        return f"Error: Access to this file is not allowed (protected file)."
    
    if not full_path.exists():
        # Suggest likely file path if not found
        candidates = list(REPO_ROOT.rglob(Path(file_path).name))
        if candidates:
            suggestions = [str(p.relative_to(REPO_ROOT)) for p in candidates[:3]]
            return f"Error: File not found: {file_path}. Did you mean: {', '.join(suggestions)}?"
        return f"Error: File not found: {file_path}"
    
    if not full_path.is_file():
        return f"Error: Path is not a file: {file_path}"
    
    try:
        content = full_path.read_text()
        return content
    except UnicodeDecodeError:
        return f"Error: Could not read file (binary or non-text file): {file_path}"
    except Exception as e:
        return f"Error: Could not read file: {e}"


def write_file_tool(file_path: str, new_content: str) -> str:
    """Write the given content to the specified file (if allowed)."""
    full_path = (REPO_ROOT / file_path).resolve()
    
    # Block writing if outside repo or targeting protected paths
    if not str(full_path).startswith(str(REPO_ROOT)):
        return "Error: Access to this path is not allowed (outside repository)."
    
    if any(substr in file_path for substr in BLOCKED_SUBSTRINGS):
        return f"Error: Access to this path is not allowed (blocked path)."
    
    if Path(file_path).name in BLOCKED_NAMES:
        return f"Error: Access to this file is not allowed (protected file)."
    # Avoid creating a new file at repo root if module exists elsewhere
    if not full_path.exists():
        if full_path.parent == REPO_ROOT:
            hits = list(REPO_ROOT.rglob(Path(file_path).name))
            if hits:
                hit_dirs = [str(p.parent.relative_to(REPO_ROOT)) for p in hits[:3]]
                return f"Error: Invalid path: '{file_path}'. A file named '{Path(file_path).name}' exists in: {', '.join(hit_dirs)}. Please place the file in the correct directory."
    try:
        # Ensure directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the content
        full_path.write_text(new_content)
        
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error: Could not write to file: {e}"


def run_tests_tool(_: str = "") -> str:
    """Run all tests in a sandboxed container and return JSON results as a string."""
    image = "nova-ci-rescue-sandbox"
    
    # Ensure the .nova directory exists for output (report file)
    nova_dir = REPO_ROOT / ".nova"
    nova_dir.mkdir(exist_ok=True)
    
    # Build the Docker command
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{str(REPO_ROOT)}:/workspace:ro",
        "-v", f"{str(nova_dir)}:/workspace/.nova:rw",
        "--memory", "1g",
        "--cpus", "1.0", 
        "--network", "none",
        image,
        "python", "/usr/local/bin/run_python.py", "--pytest"
    ]
    
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
    except subprocess.TimeoutExpired:
        result = {
            "exit_code": 124,
            "stdout": "",
            "stderr": "Docker sandbox timed out after 10 minutes",
            "timeout": True
        }
        return json.dumps(result)
    except FileNotFoundError:
        result = {
            "exit_code": 127,
            "stdout": "",
            "stderr": "Docker command not found. Please ensure Docker is installed.",
            "error": "Docker not available"
        }
        return json.dumps(result)
    
    stdout = proc.stdout.strip()
    
    if stdout:
        # If sandbox printed JSON to stdout, return it directly
        try:
            json.loads(stdout)  # validate JSON format
            return stdout
        except json.JSONDecodeError:
            # Received non-JSON output; include it in an error structure
            result = {
                "exit_code": proc.returncode,
                "stdout": stdout,
                "stderr": proc.stderr.strip(),
                "error": "Non-JSON output from sandbox"
            }
            return json.dumps(result)
    else:
        # No output from container; return whatever we have from stderr/exit code
        result = {
            "exit_code": proc.returncode,
            "stdout": "",
            "stderr": proc.stderr.strip()
        }
        return json.dumps(result)
