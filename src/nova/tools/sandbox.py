from __future__ import annotations

import os
import resource
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Optional


@contextmanager
def sandbox_limits(cpu_seconds: int = 600, mem_mb: int = 2048):
    """Context manager to apply POSIX rlimits to child processes started within.

    Note: Only effective on POSIX. No effect on non-POSIX platforms.
    """
    try:
        old_cpu = resource.getrlimit(resource.RLIMIT_CPU)
        old_as = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
        resource.setrlimit(resource.RLIMIT_AS, (mem_mb * 1024 * 1024, mem_mb * 1024 * 1024))
        yield
    finally:
        try:
            resource.setrlimit(resource.RLIMIT_CPU, old_cpu)
            resource.setrlimit(resource.RLIMIT_AS, old_as)
        except Exception:
            pass


def _apply_limits():
    # Pre-exec function for subprocess to apply limits in child process
    try:
        resource.setrlimit(resource.RLIMIT_CPU, resource.getrlimit(resource.RLIMIT_CPU))
        resource.setrlimit(resource.RLIMIT_AS, resource.getrlimit(resource.RLIMIT_AS))
    except Exception:
        pass


def run_in_sandbox(cmd: Iterable[str], cwd: Path, timeout: int):
    """Run a command with rlimits applied using preexec_fn.

    Returns CompletedProcess-like object from subprocess.run.
    """
    return subprocess.run(list(cmd), cwd=str(cwd), capture_output=True, text=True, timeout=timeout, preexec_fn=_apply_limits)
