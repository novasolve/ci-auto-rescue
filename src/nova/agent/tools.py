"""
LangChain Tool Definitions for Nova CI-Rescue Deep Agent
==========================================================

DEPRECATED: This file is being replaced by nova.agent.unified_tools.
Please use the unified tools module instead for all tool definitions.

This file is kept for backward compatibility but will be removed in a future version.

The Deep Agent uses four tools wrapped with LangChain's @tool decorator:
- plan_todo: Planning no-op tool (records the plan in agent's log)
- open_file: File read tool with safety checks
- write_file: File write tool with safety checks  
- run_tests: Docker-based test runner tool
"""

from langchain.agents import tool
import subprocess
import json
import shutil
from pathlib import Path
from typing import Optional

# Define blocked file patterns (e.g. tests or sensitive files that the agent should not modify/read)
blocked_patterns = ["tests/*", ".env", ".git/*", "secrets/*", ".github/*", "*.pyc", "__pycache__/*"]

# Docker-based test runner tool configuration
DOCKER_IMAGE = "nova-ci-rescue-sandbox:latest"
CPU_LIMIT = "1.0"   # 1 CPU core
MEM_LIMIT = "1g"    # 1 GB RAM
TEST_TIMEOUT = 600  # 10 minutes
PID_LIMIT = "256"   # Process spawn limit


@tool("plan_todo", return_direct=True)
def plan_todo(todo: str) -> str:
    """Plan next steps. The agent uses this to outline a TODO list or strategy."""
    # This tool is a no-op that just records the plan in the agent's log.
    return f"Plan noted: {todo}"


@tool("open_file", return_direct=True)
def open_file(path: str) -> str:
    """Read the contents of a file."""
    # Prevent opening files that match any forbidden pattern
    p = Path(path)
    for pattern in blocked_patterns:
        if p.match(pattern):
            return f"ERROR: Access to {path} is blocked by policy."
    try:
        with open(path, "r") as f:
            content = f.read()
            # Optionally, truncate content here if it's too large for the LLM context
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
    """Overwrite a file with the given content."""
    p = Path(path)
    for pattern in blocked_patterns:
        if p.match(pattern):
            return f"ERROR: Modification of {path} is not allowed."
    try:
        # Ensure parent directory exists
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(new_content)
        return f"File {path} updated."
    except PermissionError:
        return f"ERROR: Permission denied: {path}"
    except Exception as e:
        return f"ERROR: Could not write to file {path}: {e}"


@tool("run_tests", return_direct=True)
def run_tests() -> str:
    """Run the project's test suite inside a Docker container and return JSON results."""
    # Ensure Docker is available on the host
    if shutil.which("docker") is None:
        return json.dumps({"error": "Docker is not available on this system.", "exit_code": 127})
    
    # Assume repo_path is the current working directory of the repo
    repo_path = Path(".").resolve()
    
    # Ensure .nova directory exists for test reports
    nova_path = repo_path / ".nova"
    nova_path.mkdir(exist_ok=True)
    
    # Construct the Docker command to run tests in sandbox
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{repo_path}:/workspace:ro",               # mount repo as read-only in container
        "-v", f"{nova_path}:/workspace/.nova:rw",         # mount .nova directory for test reports
        "--memory", MEM_LIMIT, 
        "--cpus", CPU_LIMIT,
        "--network", "none",                              # disable network in container
        "--pids-limit", PID_LIMIT,                        # restrict process spawning
        DOCKER_IMAGE,
        "python", "/usr/local/bin/run_python.py", "--pytest"
    ]
    
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TEST_TIMEOUT)
    except subprocess.TimeoutExpired:
        return json.dumps({
            "exit_code": 124,
            "error": "Test execution timed out"
        })
    except Exception as e:
        return json.dumps({
            "exit_code": 1,
            "error": f"Failed to run Docker container: {e}"
        })
    
    # Capture and handle the output from the container
    stdout = proc.stdout.strip()
    
    if not stdout:
        # If no JSON output was produced, likely tests crashed; include stderr info
        return json.dumps({
            "exit_code": proc.returncode,
            "stderr": proc.stderr.strip(),
            "error": "No output from test run"
        })
    
    # Attempt to parse JSON output from tests
    try:
        result = json.loads(stdout)
        return json.dumps(result)
    except json.JSONDecodeError:
        # If output is not valid JSON (e.g., an unhandled exception), include snippet of output for debugging
        result = {
            "exit_code": proc.returncode,
            "stdout": stdout[:1000],  # include up to first 1000 chars of output
            "stderr": proc.stderr.strip(),
            "error": "Non-JSON output from tests"
        }
        return json.dumps(result)
