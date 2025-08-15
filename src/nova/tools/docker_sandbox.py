from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional


def is_docker_available() -> bool:
    """Return True if the docker CLI is available on PATH."""
    return shutil.which("docker") is not None


def run_pytest_in_docker(
    repo_path: Path,
    image: str,
    timeout_seconds: int = 600,
    no_network: bool = True,
    memory: str = "1g",
    cpus: float = 1.0,
) -> Dict[str, object]:
    """Run pytest inside a sandbox container and return structured JSON results.

    Expects the image to contain /usr/local/bin/run_python.py and pytest.
    Mounts the repo read-only at /workspace and a writable .nova at /workspace/.nova.
    """
    repo_path = Path(repo_path).resolve()
    nova_dir = repo_path / ".nova"
    nova_dir.mkdir(exist_ok=True)

    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{str(repo_path)}:/workspace:ro",
        "-v",
        f"{str(nova_dir)}:/workspace/.nova:rw",
        "--memory",
        memory,
        "--cpus",
        str(cpus),
    ]
    if no_network:
        cmd.extend(["--network", "none"])

    # Drop capabilities and make container pid/user namespaces more restrictive when possible
    cmd.extend(["--pids-limit", "256"])
    # Use the provided image and execute the pytest runner
    cmd.extend([
        image,
        "python",
        "/usr/local/bin/run_python.py",
        "--pytest",
    ])

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
        stdout = proc.stdout.strip()
        # The sandbox prints a single JSON object to stdout
        try:
            data = json.loads(stdout) if stdout else {}
        except json.JSONDecodeError:
            data = {
                "exit_code": proc.returncode,
                "stdout": stdout,
                "stderr": proc.stderr,
                "error": "Non-JSON output from sandbox",
            }
        return data
    except subprocess.TimeoutExpired:
        return {
            "exit_code": 124,
            "stdout": "",
            "stderr": "Docker sandbox timed out",
            "timed_out": True,
        }


def run_code_in_docker(
    repo_path: Path,
    image: str,
    code: str,
    timeout_seconds: int = 60,
    no_network: bool = True,
    memory: str = "1g",
    cpus: float = 1.0,
) -> Dict[str, object]:
    """Execute an arbitrary Python snippet inside the sandbox container."""
    repo_path = Path(repo_path).resolve()
    nova_dir = repo_path / ".nova"
    nova_dir.mkdir(exist_ok=True)

    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{str(repo_path)}:/workspace:ro",
        "-v",
        f"{str(nova_dir)}:/workspace/.nova:rw",
        "--memory",
        memory,
        "--cpus",
        str(cpus),
    ]
    if no_network:
        cmd.extend(["--network", "none"])

    cmd.extend([
        image,
        "python",
        "/usr/local/bin/run_python.py",
        "--code",
        code,
    ])

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
        stdout = proc.stdout.strip()
        try:
            return json.loads(stdout) if stdout else {"exit_code": proc.returncode}
        except json.JSONDecodeError:
            return {
                "exit_code": proc.returncode,
                "stdout": stdout,
                "stderr": proc.stderr,
                "error": "Non-JSON output from sandbox",
            }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": 124,
            "stdout": "",
            "stderr": "Docker sandbox timed out",
            "timed_out": True,
        }


__all__ = [
    "is_docker_available",
    "run_pytest_in_docker",
    "run_code_in_docker",
]


