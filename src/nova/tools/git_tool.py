from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid
from pathlib import Path
from typing import List, Optional

from .sandbox import run_command


class GitError(RuntimeError):
    pass


def ensure_repo(repo_root: Path) -> None:
    root = Path(repo_root)
    if not (root / ".git").exists():
        raise GitError(f"No .git directory found under {root}")


def _git(repo_root: Path, args: List[str], timeout: int = 30) -> str:
    res = run_command(["git", *args], cwd=repo_root, timeout=timeout, capture_output=True)
    if res.get("returncode") != 0:
        stderr = str(res.get("stderr", ""))
        stdout = str(res.get("stdout", ""))
        timed_out = res.get("timed_out", False)
        msg = f"git {' '.join(args)} failed (rc={res.get('returncode')}, timeout={timed_out}).\nSTDERR:\n{stderr}\nSTDOUT:\n{stdout}"
        raise GitError(msg)
    return str(res.get("stdout", ""))


def current_branch(repo_root: Path) -> str:
    out = _git(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"]).strip()
    return out or "HEAD"


def create_fix_branch(repo_root: Path, prefix: str = "nova-fix") -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    branch = f"{prefix}/{ts}-{uuid.uuid4().hex[:6]}"
    try:
        _git(repo_root, ["switch", "-c", branch])
    except GitError:
        _git(repo_root, ["checkout", "-b", branch])
    return branch


def _has_changes(repo_root: Path) -> bool:
    out = _git(repo_root, ["status", "--porcelain"]).strip()
    return bool(out)


def commit_all(repo_root: Path, message: str) -> None:
    _git(repo_root, ["add", "-A"])
    if not _has_changes(repo_root):
        return
    # Use inline config to avoid relying on global git identity
    _git(
        repo_root,
        [
            "-c",
            "user.name=Nova CI-Rescue",
            "-c",
            "user.email=nova@example.com",
            "commit",
            "-m",
            message,
            "--no-verify",
        ],
    )


def reset_hard(repo_root: Path, ref: str = "HEAD") -> None:
    _git(repo_root, ["reset", "--hard", ref])


__all__ = [
    "GitError",
    "ensure_repo",
    "create_fix_branch",
    "commit_all",
    "reset_hard",
    "current_branch",
]
