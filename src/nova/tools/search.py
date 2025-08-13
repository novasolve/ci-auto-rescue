from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Dict, Iterable, List


def list_py_files(repo: Path) -> List[str]:
    repo = repo.resolve()
    return [str(p.relative_to(repo)) for p in repo.rglob("*.py")]


def grep(repo: Path, pattern: str, file_globs: Iterable[str] | None = None) -> List[Dict]:
    repo = repo.resolve()
    file_globs = list(file_globs) if file_globs is not None else ["**/*.py", "**/*.md", "**/*.txt"]
    regex = re.compile(pattern)
    results: List[Dict] = []
    for glob in file_globs:
        for path in repo.rglob(glob.replace("**/", "")) if glob.startswith("**/") else repo.rglob(glob):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for i, line in enumerate(text.splitlines(), start=1):
                if regex.search(line):
                    results.append({"path": str(path.relative_to(repo)), "line_no": i, "text": line})
    return results
