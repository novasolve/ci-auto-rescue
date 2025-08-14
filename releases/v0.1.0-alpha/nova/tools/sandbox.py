from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional


def _limits_preexec(cpu_seconds: Optional[int] = None, max_address_space_bytes: Optional[int] = None):
    try:
        import resource  # type: ignore
    except Exception:
        resource = None  # type: ignore

    def _apply():
        try:
            os.setsid()
        except Exception:
            pass
        if resource is None:
            return
        try:
            if cpu_seconds and cpu_seconds > 0:
                resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
        except Exception:
            pass
        try:
            if max_address_space_bytes and max_address_space_bytes > 0:
                resource.setrlimit(resource.RLIMIT_AS, (max_address_space_bytes, max_address_space_bytes))
        except Exception:
            pass

    return _apply


essential_env_keys = {
    "PATH",
    "HOME",
    "LANG",
    "LC_ALL",
    "PYTHONPATH",
}


def run_command(
    cmd: List[str],
    cwd: Path,
    timeout: int,
    env: Optional[Dict[str, str]] = None,
    capture_output: bool = True,
) -> Dict[str, object]:
    """Run a command in a sandboxed subprocess with resource limits.

    Returns a dict with keys: returncode, stdout, stderr, timed_out, duration.
    """
    start = time.time()
    stdout_pipe = subprocess.PIPE if capture_output else None
    stderr_pipe = subprocess.PIPE if capture_output else None

    cpu_limit = max(1, int(timeout)) if timeout and timeout > 0 else None
    two_gib = 2 * 1024 * 1024 * 1024

    env_vars = dict(os.environ)
    if env:
        env_vars.update(env)
    # Optionally, we could restrict environment here. Keep essentials.

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            env=env_vars,
            stdout=stdout_pipe,
            stderr=stderr_pipe,
            text=False,
            preexec_fn=_limits_preexec(cpu_seconds=cpu_limit, max_address_space_bytes=two_gib)
            if os.name == "posix"
            else None,
        )

        try:
            out, err = proc.communicate(timeout=timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                if os.name == "posix":
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                else:
                    proc.terminate()
            except Exception:
                pass
            try:
                out, err = proc.communicate(timeout=5)
            except Exception:
                try:
                    if os.name == "posix":
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    else:
                        proc.kill()
                except Exception:
                    pass
                out, err = proc.communicate()

        duration = time.time() - start
        if capture_output:
            stdout_text = (out or b"").decode("utf-8", errors="replace")
            stderr_text = (err or b"").decode("utf-8", errors="replace")
        else:
            stdout_text = ""
            stderr_text = ""
        return {
            "returncode": proc.returncode,
            "stdout": stdout_text,
            "stderr": stderr_text,
            "timed_out": timed_out,
            "duration": duration,
        }
    except FileNotFoundError as e:
        return {
            "returncode": 127,
            "stdout": "",
            "stderr": str(e),
            "timed_out": False,
            "duration": time.time() - start,
        }


__all__ = ["run_command"]
