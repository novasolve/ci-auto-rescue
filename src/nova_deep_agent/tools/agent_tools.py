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


# Define the repository root (assuming current working directory is the repo)
REPO_ROOT = Path(".").resolve()

# Define blocked file names and path substrings for safety (no writes/reads to these)
BLOCKED_NAMES = {"setup.py", "pyproject.toml", ".env", "requirements.txt"}
BLOCKED_SUBSTRINGS = [".github/", ".git/"]


def plan_todo_tool(notes: str = "") -> str:
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
