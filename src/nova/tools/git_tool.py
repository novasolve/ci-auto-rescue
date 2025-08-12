from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional


class GitError(Exception):
    pass


def _run(repo: Path, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
    cmd = ["git", "-C", str(repo)] + args
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError as e:
        raise GitError("git not available") from e
    if check and cp.returncode != 0:
        raise GitError(cp.stderr.strip() or cp.stdout.strip())
    return cp


def ensure_branch(repo: Path, branch_name: Optional[str] = None) -> str:
    repo = repo.resolve()
    if branch_name is None:
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        branch_name = f"nova-fix/{ts}"
    # Ensure repository exists
    _run(repo, ["rev-parse", "--is-inside-work-tree"])
    # Create and switch branch
    _run(repo, ["checkout", "-B", branch_name])
    return branch_name


def commit_all(repo: Path, message: str) -> None:
    repo = repo.resolve()
    _run(repo, ["add", "-A"])
    cp = _run(repo, ["commit", "-m", message], check=False)
    if cp.returncode != 0:
        # Attempt to set fallback identity locally and retry once
        if "user.name" in cp.stderr or "user.email" in cp.stderr:
            _run(repo, ["config", "user.email", "nova@example.com"])  # best-effort
            _run(repo, ["config", "user.name", "Nova CI-Rescue"])  # best-effort
            _run(repo, ["commit", "-m", message])
        else:
            raise GitError(cp.stderr.strip() or cp.stdout.strip())


def reset_hard(repo: Path, ref: str = "HEAD") -> None:
    _run(repo, ["reset", "--hard", ref])


def get_head(repo: Path) -> str:
    cp = _run(repo, ["rev-parse", "HEAD"])
    return cp.stdout.strip()


def get_changed_files(repo: Path) -> List[str]:
    cp = _run(repo, ["status", "--porcelain"])
    files: List[str] = []
    for line in cp.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.strip().split(maxsplit=1)
        if len(parts) == 2:
            files.append(parts[1])
    return files
