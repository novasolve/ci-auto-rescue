from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional


_IGNORED_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "dist", "build", "node_modules", "__pycache__"}


def _iter_files(root: Path) -> Iterator[Path]:
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune ignored directories in-place
        dirnames[:] = [d for d in dirnames if d not in _IGNORED_DIRS]
        for fname in filenames:
            yield Path(dirpath) / fname


def _matches_any(path: Path, patterns: List[str]) -> bool:
    rel = str(path)
    for pat in patterns:
        if path.match(pat) or rel.endswith(pat):
            return True
    return False


def grep(
    repo_root: Path,
    pattern: str,
    globs: Optional[List[str]] = None,
    max_matches: int = 200,
) -> List[Dict[str, object]]:
    """Search text files under repo_root for lines matching a regex pattern.

    - Skips common ignored directories (.git, .venv, dist, build, etc.).
    - If globs is provided, restricts search to files matching any of the patterns.
    - Returns up to max_matches results as dicts: {path, line_no, line} with
      path relative to repo_root.
    """
    repo_root = Path(repo_root).resolve()
    try:
        regex = re.compile(pattern)
    except re.error:
        # Fallback: escape if invalid regex
        regex = re.compile(re.escape(pattern))

    results: List[Dict[str, object]] = []

    for f in _iter_files(repo_root):
        # Filter by globs if provided
        if globs and not _matches_any(f.relative_to(repo_root), globs):
            continue

        # Quick binary check: read a small chunk
        try:
            with open(f, "rb") as fb:
                chunk = fb.read(1024)
                if b"\x00" in chunk:
                    continue
        except (OSError, PermissionError):
            continue

        # Scan line by line as text (utf-8, tolerant)
        try:
            with open(f, "r", encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh, start=1):
                    if regex.search(line):
                        results.append({
                            "path": str(f.relative_to(repo_root)),
                            "line_no": i,
                            "line": line.rstrip("\n"),
                        })
                        if len(results) >= max_matches:
                            return results
        except (OSError, UnicodeError):
            continue

    return results


__all__ = ["grep"]
