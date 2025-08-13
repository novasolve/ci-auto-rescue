from __future__ import annotations

import io
import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple


# -------- Basic FS helpers --------

def read_text(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_text_safe(path: Path, content: str, backup: bool = True) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    if backup and p.exists():
        backup_path = p.with_suffix(p.suffix + ".bak")
        try:
            backup_path.write_bytes(p.read_bytes())
        except Exception:
            pass
    tmp.replace(p)


# -------- Diff application --------

@dataclass
class _Backup:
    existed: bool
    data: Optional[bytes]  # previous bytes if existed


def _is_within(root: Path, target: Path) -> bool:
    try:
        return target.resolve().is_relative_to(root.resolve())  # type: ignore[attr-defined]
    except AttributeError:
        root_r = str(root.resolve())
        targ_r = str(target.resolve())
        return targ_r == root_r or targ_r.startswith(root_r + os.sep)


@contextmanager
def rollback_on_failure(paths: Iterable[Path]) -> Iterator[None]:
    backups: Dict[Path, _Backup] = {}
    for p in paths:
        p = Path(p)
        if p.exists():
            try:
                backups[p] = _Backup(True, p.read_bytes())
            except Exception:
                backups[p] = _Backup(True, None)
        else:
            backups[p] = _Backup(False, None)
    try:
        yield
    except Exception:
        for p, b in backups.items():
            try:
                if b.existed:
                    if b.data is not None:
                        p.parent.mkdir(parents=True, exist_ok=True)
                        p.write_bytes(b.data)
                else:
                    if p.exists():
                        p.unlink()
            except Exception:
                pass
        raise


def _strip_prefix(path_str: str) -> str:
    # Git-style a/ and b/ prefixes
    if path_str.startswith("a/") or path_str.startswith("b/"):
        return path_str[2:]
    return path_str


def apply_unified_diff(repo_root: Path, diff_text: str) -> List[Path]:
    """Apply a unified diff to files under repo_root.

    Returns a list of changed file Paths. Ensures all paths stay within repo_root
    and rolls back if any patch application fails.
    """
    try:
        from unidiff import PatchSet  # type: ignore
    except Exception as e:
        raise RuntimeError("unidiff package is required to apply patches") from e

    repo_root = Path(repo_root).resolve()

    patch = PatchSet(io.StringIO(diff_text))

    targets: List[Tuple[Path, object]] = []
    # Determine all paths that will be modified/created/deleted for backup
    paths_to_touch: List[Path] = []

    for pf in patch:
        # Prefer target file path; fall back to source for deletions/renames
        tgt = getattr(pf, "target_file", None) or getattr(pf, "path", None)
        src = getattr(pf, "source_file", None)
        tgt_rel = _strip_prefix(tgt) if isinstance(tgt, str) else None
        src_rel = _strip_prefix(src) if isinstance(src, str) else None

        if getattr(pf, "is_removed_file", False) and src_rel:
            path = (repo_root / src_rel).resolve()
            if not _is_within(repo_root, path):
                raise PermissionError(f"Refusing to modify path outside repo: {path}")
            targets.append((path, pf))
            paths_to_touch.append(path)
        else:
            # Added/modified/renamed target
            if not tgt_rel:
                # Some diffs might specify only source on rename/delete with no target
                if src_rel:
                    path = (repo_root / src_rel).resolve()
                else:
                    raise ValueError("Patch file missing path information")
            else:
                path = (repo_root / tgt_rel).resolve()
            if not _is_within(repo_root, path):
                raise PermissionError(f"Refusing to modify path outside repo: {path}")
            targets.append((path, pf))
            paths_to_touch.append(path)

    changed: List[Path] = []

    with rollback_on_failure(paths_to_touch):
        for path, pf in targets:
            is_added = bool(getattr(pf, "is_added_file", False))
            is_removed = bool(getattr(pf, "is_removed_file", False))
            is_rename = bool(getattr(pf, "is_rename", False))

            if is_rename:
                # Attempt to move source to target first if names differ
                src = getattr(pf, "source_file", None)
                tgt = getattr(pf, "target_file", None)
                if isinstance(src, str) and isinstance(tgt, str):
                    src_path = (repo_root / _strip_prefix(src)).resolve()
                    tgt_path = (repo_root / _strip_prefix(tgt)).resolve()
                    if src_path != tgt_path and src_path.exists():
                        tgt_path.parent.mkdir(parents=True, exist_ok=True)
                        os.replace(src_path, tgt_path)
                        changed.append(tgt_path)
                        path = tgt_path  # continue to apply any hunks to new path

            if is_removed:
                if path.exists():
                    path.unlink()
                changed.append(path)
                continue

            if is_added and not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                # Build content from hunks (added lines)
                new_bytes = _build_content_from_hunks(None, pf)
                path.write_bytes(new_bytes)
                changed.append(path)
                continue

            # Modified (or added over existing path)
            path.parent.mkdir(parents=True, exist_ok=True)
            prev_bytes = path.read_bytes() if path.exists() else b""
            new_bytes = _build_content_from_hunks(prev_bytes, pf)
            if new_bytes != prev_bytes:
                path.write_bytes(new_bytes)
                changed.append(path)

    return changed


def _build_content_from_hunks(prev: Optional[bytes], pf: object) -> bytes:
    """Construct new file content by applying hunks to previous bytes.

    pf is a PatchedFile from unidiff.
    """
    # Access hunks via iteration over pf
    lines_prev = (prev or b"").decode("utf-8", errors="replace").splitlines(keepends=True)
    out: List[str] = []
    idx = 0

    # If previous content is empty and file is marked added, we can just emit all
    # added and context lines as they appear in hunks
    for hunk in pf:  # type: ignore[operator]
        # Append unchanged lines before hunk start (1-based to 0-based)
        # hunk.source_start may be 0 for added files
        start = max(1, getattr(hunk, "source_start", 1))
        start_idx = max(0, start - 1)
        if idx < start_idx and lines_prev:
            out.extend(lines_prev[idx:start_idx])
            idx = start_idx
        # Apply hunk lines
        for line in hunk:  # Lines in hunk
            # Skip special no-newline indicator
            if getattr(line, "is_no_newline", False):
                continue
            # Determine content value
            val = getattr(line, "value", None)
            if val is None:
                s = str(line)
                # Strip leading prefix if present
                if s and s[0] in "+- \t":
                    val = s[1:]
                else:
                    val = s
            if getattr(line, "is_context", False):
                if idx < len(lines_prev):
                    out.append(lines_prev[idx])
                else:
                    # If context beyond current, trust patch line
                    out.append(val)
                idx += 1
            elif getattr(line, "is_removed", False):
                # Consume a line from previous without adding
                idx += 1
            elif getattr(line, "is_added", False):
                out.append(val)
            else:
                # Fallback treat as context
                if idx < len(lines_prev):
                    out.append(lines_prev[idx])
                    idx += 1
                else:
                    out.append(val)

    # Append remaining previous content if any
    if idx < len(lines_prev):
        out.extend(lines_prev[idx:])

    return "".join(out).encode("utf-8")


def apply_and_commit_patch(
    repo_root: Path, 
    diff_text: str, 
    step_number: int,
    git_manager: Optional[object] = None,
    verbose: bool = False
) -> Tuple[bool, List[Path]]:
    """Apply a patch and commit it with a step message.
    
    Args:
        repo_root: Repository root path
        diff_text: The unified diff text to apply
        step_number: The step number for the commit message
        git_manager: Optional GitBranchManager instance for committing
        verbose: Enable verbose output
        
    Returns:
        Tuple of (success, list of changed files)
    """
    try:
        # Apply the patch
        changed_files = apply_unified_diff(repo_root, diff_text)
        
        # If a git manager is provided, commit the changes
        if git_manager and changed_files:
            # Import here to avoid circular dependency
            from nova.tools.git import GitBranchManager
            if isinstance(git_manager, GitBranchManager):
                commit_success = git_manager.commit_patch(step_number)
                if not commit_success and verbose:
                    print(f"Warning: Failed to commit step {step_number}")
        
        return True, changed_files
    except Exception as e:
        if verbose:
            print(f"Error applying patch: {e}")
        return False, []


__all__ = [
    "read_text",
    "write_text_safe",
    "apply_unified_diff",
    "rollback_on_failure",
    "apply_and_commit_patch",
]
