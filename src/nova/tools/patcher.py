from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable, List, Tuple

from unidiff import PatchSet  # type: ignore


SAFE_DENY_PATTERNS = (
    ".env",
    ".env.local",
    "secrets",
)


class PatchError(Exception):
    pass


def parse_unified_diff(diff_text: str) -> PatchSet:
    try:
        return PatchSet(diff_text)
    except Exception as e:
        raise PatchError(f"Invalid unified diff: {e}")


def changed_line_count(patch: PatchSet) -> int:
    total = 0
    for f in patch:
        for h in f:
            total += sum(1 for l in h if l.is_added or l.is_removed)
    return total


def _deny_path(path: Path, allow_tests_mods: bool) -> bool:
    p = str(path).replace("\\", "/")
    if not allow_tests_mods and (p.startswith("tests/") or "/tests/" in p):
        return True
    for pat in SAFE_DENY_PATTERNS:
        if pat in p:
            return True
    return False


def apply_unified_diff(
    repo_root: Path,
    diff_text: str,
    allow_tests_mods: bool = False,
    max_changed_lines: int = 50,
) -> List[str]:
    """Apply a unified diff conservatively.

    - Reject if any target is forbidden (tests/* unless allowed, .env, secrets).
    - Enforce max_changed_lines across all files.
    - Create .bak backups and rollback on any failure.

    Returns list of modified file paths (relative to repo_root).
    """
    repo_root = repo_root.resolve()
    patch = parse_unified_diff(diff_text)
    if len(patch) == 0:
        raise PatchError("Empty diff")

    if changed_line_count(patch) > max_changed_lines:
        raise PatchError(
            f"Diff too large: {changed_line_count(patch)} lines > {max_changed_lines}"
        )

    targets: List[Tuple[Path, str]] = []
    for f in patch:
        # Prefer target path (new_file_path), fallback to source
        rel = (f.path or f.target_file or f.source_file).lstrip("ab/")
        path = (repo_root / rel).resolve()
        if not str(path).startswith(str(repo_root)):
            raise PatchError(f"Refusing to write outside repo: {rel}")
        if _deny_path(path.relative_to(repo_root), allow_tests_mods):
            raise PatchError(f"Refusing to modify forbidden path: {path.relative_to(repo_root)}")
        targets.append((path, rel))

    backups: List[Path] = []
    modified: List[str] = []

    try:
        for f in patch:
            rel = (f.path or f.target_file or f.source_file).lstrip("ab/")
            path = (repo_root / rel).resolve()
            # Read original content (empty if new file)
            original = []
            if path.exists():
                original = path.read_text(encoding="utf-8").splitlines(keepends=False)
            new_lines = _apply_file_hunks(original, f)
            # Backup existing file
            if path.exists():
                bak = path.with_suffix(path.suffix + ".bak")
                shutil.copy2(path, bak)
                backups.append(bak)
            else:
                # Ensure parent exists
                path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("\n".join(new_lines) + ("\n" if new_lines and not new_lines[-1].endswith("\n") else ""))
            modified.append(str(path.relative_to(repo_root)))
    except Exception as e:
        # Rollback
        for bak in backups:
            orig = Path(str(bak)[: -len(".bak")])
            shutil.move(str(bak), str(orig))
        # Remove newly created files that didn't exist before and have no backup
        for fpath, _ in targets:
            bak = fpath.with_suffix(fpath.suffix + ".bak")
            if not bak.exists() and fpath.exists():
                try:
                    fpath.unlink()
                except Exception:
                    pass
        raise PatchError(f"Failed to apply diff: {e}")

    # Cleanup backups after successful apply
    for bak in backups:
        try:
            bak.unlink()
        except Exception:
            pass

    return modified


def _apply_file_hunks(original: List[str], fpatch) -> List[str]:
    """Apply hunks for a single file; require exact context matches.

    Raises PatchError if any hunk does not apply cleanly.
    """
    # We'll build new content by walking through original lines with hunk positions.
    # unidiff hunks contain target_start, source lines etc. We'll use a simple approach:
    result: List[str] = []
    idx = 0
    for h in fpatch:
        # Copy unchanged lines before hunk target start (1-based index)
        target_start = h.target_start - 1  # to 0-based
        # Compute actual position by scanning original with context matching
        # We'll match the context preceding the first changed line when possible.
        # For conservative behavior, require exact position alignment.
        if target_start < idx:
            raise PatchError("Overlapping or out-of-order hunks are not supported")
        # Append untouched lines up to target_start adjusted by how many lines already removed/added
        while idx < target_start and idx < len(original):
            result.append(original[idx])
            idx += 1
        # Now apply hunk lines
        o_cursor = idx
        for line in h:
            if line.is_context:
                # Context line must match original
                if o_cursor >= len(original) or original[o_cursor] != line.value.rstrip("\n"):
                    raise PatchError("Context mismatch when applying hunk")
                result.append(original[o_cursor])
                o_cursor += 1
            elif line.is_removed:
                # Removed line must match original; do not append to result
                if o_cursor >= len(original) or original[o_cursor] != line.value.rstrip("\n"):
                    raise PatchError("Removal mismatch when applying hunk")
                o_cursor += 1
            elif line.is_added:
                # Added line goes to result
                result.append(line.value.rstrip("\n"))
        # Set new idx to o_cursor after applying hunk
        idx = o_cursor
    # Append remaining original lines
    while idx < len(original):
        result.append(original[idx])
        idx += 1
    return result
