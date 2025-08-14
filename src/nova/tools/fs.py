from __future__ import annotations

import io
import os
import tempfile
import subprocess
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
        
        # Track if we successfully matched context
        context_matched = True
        hunk_lines = list(hunk)  # Convert to list for easier processing
        
        # First pass: check if context lines match
        temp_idx = idx
        for line in hunk_lines:
            if getattr(line, "is_context", False) or getattr(line, "is_removed", False):
                val = getattr(line, "value", str(line)[1:] if str(line) else "")
                if temp_idx < len(lines_prev):
                    # Check if the context/removed line matches what we expect
                    if lines_prev[temp_idx].rstrip() != val.rstrip():
                        context_matched = False
                        break
                    temp_idx += 1
                    
        # If context doesn't match, try to find where the hunk should apply
        if not context_matched and lines_prev:
            # Try to find matching context in the file
            for search_idx in range(max(0, idx - 10), min(len(lines_prev), idx + 10)):
                temp_idx = search_idx
                match = True
                for line in hunk_lines:
                    if getattr(line, "is_context", False) or getattr(line, "is_removed", False):
                        val = getattr(line, "value", str(line)[1:] if str(line) else "")
                        if temp_idx >= len(lines_prev) or lines_prev[temp_idx].rstrip() != val.rstrip():
                            match = False
                            break
                        temp_idx += 1
                if match:
                    # Found matching context, adjust index
                    if search_idx > idx:
                        out.extend(lines_prev[idx:search_idx])
                    idx = search_idx
                    context_matched = True
                    break
        
        # Apply hunk lines
        for line in hunk_lines:
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
                    if context_matched:
                        out.append(lines_prev[idx])
                    else:
                        # Context doesn't match, use the line from patch
                        out.append(val)
                else:
                    # If context beyond current, trust patch line
                    out.append(val)
                idx += 1
            elif getattr(line, "is_removed", False):
                # Only consume if we have matching context
                if context_matched and idx < len(lines_prev):
                    idx += 1
                elif not context_matched:
                    # If context doesn't match, skip this removal
                    pass
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
        # Validate the diff is not empty
        if not diff_text or not diff_text.strip():
            if verbose:
                print("Error: Empty patch provided")
            return False, []
        
        # Try to fix common patch format issues
        try:
            from nova.tools.patch_fixer import fix_patch_format, validate_patch
            
            # Validate the patch
            is_valid, error_msg = validate_patch(diff_text)
            if not is_valid:
                if verbose:
                    print(f"Patch validation failed: {error_msg}")
                    print("Attempting to fix patch format...")
                
                # Try to fix the patch
                diff_text = fix_patch_format(diff_text, verbose=verbose)
                
                # Validate again
                is_valid, error_msg = validate_patch(diff_text)
                if not is_valid:
                    if verbose:
                        print(f"Could not fix patch: {error_msg}")
                    return False, []
                elif verbose:
                    print("Patch format fixed successfully")
        except ImportError:
            # patch_fixer not available, proceed without fixing
            pass
        
        # Use git apply instead of custom patch application
        changed_files = apply_patch_with_git(repo_root, diff_text, git_manager, verbose, telemetry=None)
        
        # If no files were changed, it might mean the patch was already applied
        if not changed_files:
            if verbose:
                print("Warning: No files were changed by the patch (may already be applied)")
            return False, []
        
        # If a git manager is provided, commit the changes
        if git_manager and changed_files:
            # Import here to avoid circular dependency
            from nova.tools.git import GitBranchManager
            if isinstance(git_manager, GitBranchManager):
                commit_success = git_manager.commit_patch(step_number)
                if not commit_success and verbose:
                    print(f"Warning: Failed to commit step {step_number}")
        
        return True, changed_files
    except ValueError as e:
        if verbose:
            print(f"Error: Invalid patch format - {e}")
        return False, []
    except PermissionError as e:
        if verbose:
            print(f"Error: Permission denied - {e}")
        return False, []
    except RuntimeError as e:
        if verbose:
            print(f"Error: Runtime error - {e}")
        return False, []
    except Exception as e:
        if verbose:
            import traceback
            print(f"Error applying patch: {e}")
            print(f"Patch content (first 500 chars):\n{diff_text[:500]}")
            if verbose:
                traceback.print_exc()
        return False, []


def apply_patch_with_git(
    repo_root: Path,
    diff_text: str,
    git_manager: Optional[object] = None,
    verbose: bool = False,
    telemetry: Optional[object] = None
) -> List[Path]:
    """Apply a patch using git apply.
    
    Args:
        repo_root: Repository root path
        diff_text: The unified diff text to apply
        git_manager: Optional GitBranchManager instance for git operations
        verbose: Enable verbose output
        telemetry: Optional telemetry logger instance
        
    Returns:
        List of changed files
    """
    from nova.tools.git import GitBranchManager
    
    # Write patch to a temporary file (use system temp dir, not repo dir)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
        patch_file = Path(f.name)
        f.write(diff_text)
    
    try:
        # First, do a dry run with --check to validate the patch
        if git_manager and isinstance(git_manager, GitBranchManager):
            success, output = git_manager._run_git_command("apply", "--check", "--whitespace=nowarn", str(patch_file))
        else:
            # Fallback to direct subprocess call
            result = subprocess.run(
                ["git", "apply", "--check", "--whitespace=nowarn", str(patch_file)],
                cwd=repo_root,
                capture_output=True,
                text=True
            )
            success = result.returncode == 0
            output = result.stderr or result.stdout
        
        if not success:
            # Patch cannot be applied
            error_msg = f"Patch validation failed: {output}"
            if verbose:
                from rich.console import Console
                console = Console()
                console.print(f"[red]✗ {error_msg}[/red]")
                
                # Try to provide more specific error information
                if "hunk" in output.lower():
                    console.print("[yellow]Hint: The patch context doesn't match the current file content.[/yellow]")
                elif "does not exist" in output.lower() or "not found" in output.lower():
                    console.print("[yellow]Hint: The file specified in the patch doesn't exist.[/yellow]")
                elif "already exists" in output.lower():
                    console.print("[yellow]Hint: Trying to create a file that already exists.[/yellow]")
            
            # Log to telemetry if available
            if telemetry and hasattr(telemetry, 'log_event'):
                telemetry.log_event("patch_error", {
                    "error": output,
                    "type": "validation_failed"
                })
            
            # Also try to fall back to the old method as a last resort
            if verbose:
                print("Attempting fallback to Python-based patch application...")
            try:
                changed_files = apply_unified_diff(repo_root, diff_text)
                if changed_files:
                    if verbose:
                        print("Fallback successful!")
                    return changed_files
            except Exception as fallback_error:
                if verbose:
                    print(f"Fallback also failed: {fallback_error}")
            
            return []
        
        # Apply the patch for real
        if git_manager and isinstance(git_manager, GitBranchManager):
            success, output = git_manager._run_git_command("apply", "--whitespace=nowarn", str(patch_file))
        else:
            result = subprocess.run(
                ["git", "apply", "--whitespace=nowarn", str(patch_file)],
                cwd=repo_root,
                capture_output=True,
                text=True
            )
            success = result.returncode == 0
            output = result.stderr or result.stdout
        
        if not success:
            # This shouldn't happen if --check passed, but handle it anyway
            error_msg = f"Patch application failed: {output}"
            if verbose:
                from rich.console import Console
                console = Console()
                console.print(f"[red]✗ {error_msg}[/red]")
            
            if telemetry and hasattr(telemetry, 'log_event'):
                telemetry.log_event("patch_error", {
                    "error": output,
                    "type": "application_failed"
                })
            return []
        
        # Get list of changed files (both staged and unstaged)
        if git_manager and isinstance(git_manager, GitBranchManager):
            # Get unstaged changes
            success1, unstaged = git_manager._run_git_command("diff", "--name-only")
            # Get staged changes
            success2, staged = git_manager._run_git_command("diff", "--name-only", "--cached")
            # Get untracked files
            success3, untracked = git_manager._run_git_command("ls-files", "--others", "--exclude-standard")
            success = success1 and success2 and success3
            output = "\n".join([unstaged, staged, untracked]).strip()
        else:
            # Get all changes (unstaged, staged, and untracked)
            result1 = subprocess.run(
                ["git", "diff", "--name-only"],
                cwd=repo_root,
                capture_output=True,
                text=True
            )
            result2 = subprocess.run(
                ["git", "diff", "--name-only", "--cached"],
                cwd=repo_root,
                capture_output=True,
                text=True
            )
            result3 = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=repo_root,
                capture_output=True,
                text=True
            )
            success = result1.returncode == 0 and result2.returncode == 0 and result3.returncode == 0
            output = "\n".join([result1.stdout, result2.stdout, result3.stdout]).strip()
        
        if success and output:
            # Filter out the temporary patch file and only include actual source files
            changed_files = [
                repo_root / line.strip() 
                for line in output.strip().split('\n') 
                if line.strip() and not line.endswith('.patch')
            ]
            
            if verbose:
                from rich.console import Console
                console = Console()
                console.print(f"[green]✓ Patch applied successfully[/green]")
                if changed_files:
                    console.print(f"[dim]Changed files: {', '.join([f.name for f in changed_files])}[/dim]")
            
            # Save the patch as an artifact for debugging
            if telemetry and hasattr(telemetry, 'save_artifact'):
                telemetry.save_artifact(f"patches/step-{len(changed_files)}.diff", diff_text)
            
            return changed_files
        else:
            # No changes detected after applying patch
            if verbose:
                print("Warning: Patch applied but no changes detected")
            return []
    
    finally:
        # Clean up temporary patch file
        try:
            patch_file.unlink()
        except:
            pass


__all__ = [
    "read_text",
    "write_text_safe",
    "apply_unified_diff",
    "apply_patch_with_git",
    "rollback_on_failure",
    "apply_and_commit_patch",
]
