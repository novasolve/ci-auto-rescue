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
            # Try src/ directory if file doesn't exist
            if not path.exists() and not src_rel.startswith("src/"):
                alt_path = (repo_root / "src" / src_rel).resolve()
                if alt_path.exists():
                    path = alt_path
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
                    # Try src/ directory if file doesn't exist
                    if not path.exists() and not src_rel.startswith("src/"):
                        alt_path = (repo_root / "src" / src_rel).resolve()
                        if alt_path.exists():
                            path = alt_path
                else:
                    raise ValueError("Patch file missing path information")
            else:
                path = (repo_root / tgt_rel).resolve()
                # Try src/ directory if file doesn't exist and not adding new file
                if not path.exists() and not getattr(pf, "is_added_file", False):
                    if not tgt_rel.startswith("src/"):
                        alt_path = (repo_root / "src" / tgt_rel).resolve()
                        if alt_path.exists():
                            path = alt_path
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
        
        # Fix patch format issues (trailing artifacts, hunk count mismatches) before applying
        try:
            from nova.tools.patch_fixer import fix_patch_format, validate_patch, attempt_patch_reconstruction
            
            # Always apply formatting fixes to the patch text first
            diff_text_fixed = fix_patch_format(diff_text, verbose=verbose)
            is_valid, error_msg = validate_patch(diff_text_fixed)
            if not is_valid:
                if verbose:
                    print(f"Patch validation failed: {error_msg}")
                    print("Attempting patch reconstruction...")
                # Try to reconstruct the patch if format fixing wasn't enough
                reconstructed = attempt_patch_reconstruction(diff_text_fixed, str(repo_root), verbose=verbose)
                is_valid2, error_msg2 = validate_patch(reconstructed)
                if is_valid2:
                    diff_text = reconstructed
                    if verbose:
                        print("Patch reconstruction successful")
                else:
                    if verbose:
                        print(f"Could not fix or reconstruct patch: {error_msg2}")
                    return False, []
            else:
                diff_text = diff_text_fixed
                if verbose:
                    if diff_text_fixed != diff_text:
                        print("Patch format issues fixed")
                    else:
                        print("Patch format OK")
        except ImportError as e:
            # patch_fixer not available, proceed without fixing
            if verbose:
                print(f"Warning: patch_fixer module not available: {e}")
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
    
    # Create .nova directory for temporary files if it doesn't exist
    nova_dir = Path(repo_root) / ".nova"
    nova_dir.mkdir(exist_ok=True, parents=True)
    
    # Check if we need to strip subdirectory prefix from patch paths
    # This handles cases where Nova is run in a subdirectory of a larger repo
    git_toplevel = None
    if git_manager and isinstance(git_manager, GitBranchManager):
        success_top, top_path = git_manager._run_git_command("rev-parse", "--show-toplevel")
        if success_top:
            git_toplevel = Path(top_path.strip()).resolve()
    if not git_toplevel:
        # Fallback: try running git rev-parse directly
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], cwd=repo_root, 
            capture_output=True, text=True
        )
        if result.returncode == 0:
            git_toplevel = Path(result.stdout.strip()).resolve()
    
    # If repo_root is a subdirectory, strip that prefix from patch paths
    if git_toplevel and git_toplevel != repo_root.resolve():
        try:
            prefix_path = repo_root.resolve().relative_to(git_toplevel)
            prefix_str = str(prefix_path).replace('\\', '/') + "/"
            
            # Strip the prefix from the patch file paths
            lines = diff_text.splitlines(keepends=True)
            fixed_lines = []
            for line in lines:
                if line.startswith("--- a/") and prefix_str in line:
                    # Remove the subdirectory prefix from the source file path
                    line = line.replace(f"--- a/{prefix_str}", "--- a/")
                elif line.startswith("+++ b/") and prefix_str in line:
                    # Remove the subdirectory prefix from the target file path  
                    line = line.replace(f"+++ b/{prefix_str}", "+++ b/")
                fixed_lines.append(line)
            diff_text = ''.join(fixed_lines)
            
            if verbose:
                print(f"Stripped prefix '{prefix_str}' from patch paths")
        except ValueError:
            # repo_root is not under git_toplevel, no prefix to strip
            pass
    
    # Write patch to a temporary file in .nova directory
    with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False, dir=nova_dir) as f:
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
            
            # If file doesn't exist, try with -p1 to strip directory level
            if "does not exist" in output.lower() or "no such file" in output.lower():
                if verbose:
                    print("File not found, attempting with -p1 to strip directory level...")
                
                # Try applying with -p1 to strip one directory level
                if git_manager and isinstance(git_manager, GitBranchManager):
                    success_p1, output_p1 = git_manager._run_git_command("apply", "--check", "-p1", "--whitespace=nowarn", str(patch_file))
                else:
                    result_p1 = subprocess.run(
                        ["git", "apply", "--check", "-p1", "--whitespace=nowarn", str(patch_file)],
                        cwd=repo_root,
                        capture_output=True,
                        text=True
                    )
                    success_p1 = result_p1.returncode == 0
                    output_p1 = result_p1.stderr or result_p1.stdout
                
                if success_p1:
                    # -p1 check succeeded, apply it for real
                    if verbose:
                        print("✓ Patch can be applied with -p1 (stripping directory level)")
                    
                    if git_manager and isinstance(git_manager, GitBranchManager):
                        success_apply, output_apply = git_manager._run_git_command("apply", "-p1", "--whitespace=nowarn", str(patch_file))
                    else:
                        result_apply = subprocess.run(
                            ["git", "apply", "-p1", "--whitespace=nowarn", str(patch_file)],
                            cwd=repo_root,
                            capture_output=True,
                            text=True
                        )
                        success_apply = result_apply.returncode == 0
                        output_apply = result_apply.stderr or result_apply.stdout
                    
                    if success_apply:
                        # Successfully applied with -p1, now get the changed files
                        if git_manager and isinstance(git_manager, GitBranchManager):
                            # Get unstaged changes
                            success1, unstaged = git_manager._run_git_command("diff", "--name-only")
                            # Get staged changes
                            success2, staged = git_manager._run_git_command("diff", "--name-only", "--cached")
                            # Get untracked files
                            success3, untracked = git_manager._run_git_command("ls-files", "--others", "--exclude-standard")
                            output = "\n".join([unstaged, staged, untracked]).strip()
                        else:
                            # Get all changes
                            result1 = subprocess.run(["git", "diff", "--name-only"], cwd=repo_root, capture_output=True, text=True)
                            result2 = subprocess.run(["git", "diff", "--name-only", "--cached"], cwd=repo_root, capture_output=True, text=True)
                            result3 = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=repo_root, capture_output=True, text=True)
                            output = "\n".join([result1.stdout, result2.stdout, result3.stdout]).strip()
                        
                        changed_files = [Path(repo_root) / f.strip() for f in output.split('\n') if f.strip()]
                        return changed_files
            
            # Try dynamic path adjustment for missing files before giving up
            if "does not exist" in output.lower() or "no such file" in output.lower():
                if verbose:
                    print("Attempting to dynamically locate missing files...")
                
                # Detect if project uses src/ layout
                base_source_dir = None
                pyproject = Path(repo_root) / "pyproject.toml"
                if pyproject.exists():
                    try:
                        text = pyproject.read_text()
                        # Look for common indications of src layout
                        if 'from = "src"' in text or 'package-dir' in text and 'src' in text:
                            base_source_dir = Path(repo_root) / "src"
                    except:
                        pass
                
                # Fallback: check if src/ directory exists
                if base_source_dir is None and (Path(repo_root) / "src").is_dir():
                    base_source_dir = Path(repo_root) / "src"
                
                # Try to adjust patch paths
                if base_source_dir and base_source_dir.exists():
                    import re
                    missing_map = {}
                    patch_lines = diff_text.splitlines()
                    
                    # Extract file paths from patch
                    for line in patch_lines:
                        if line.startswith("--- a/") or line.startswith("+++ b/"):
                            # Extract the file path
                            match = re.match(r'^(?:--- a/|+++ b/)(.*)', line)
                            if match:
                                rel_path = match.group(1)
                                if rel_path and rel_path != "/dev/null":
                                    file_path = Path(repo_root) / rel_path
                                    if not file_path.exists():
                                        # Try with src/ prefix
                                        src_path = base_source_dir / rel_path
                                        if src_path.exists():
                                            missing_map[rel_path] = f"src/{rel_path}"
                                        else:
                                            # Try to find file by name
                                            import os
                                            filename = os.path.basename(rel_path)
                                            matches = list(Path(repo_root).rglob(filename))
                                            if len(matches) == 1:
                                                try:
                                                    found_rel = matches[0].relative_to(Path(repo_root))
                                                    missing_map[rel_path] = str(found_rel).replace('\\', '/')
                                                except:
                                                    pass
                    
                    # If we found missing files, adjust the patch
                    if missing_map:
                        if verbose:
                            print(f"Adjusting patch paths: {missing_map}")
                        
                        new_diff_lines = []
                        for line in diff_text.splitlines(keepends=True):
                            modified = False
                            for old_path, new_path in missing_map.items():
                                if line.startswith(f"--- a/{old_path}"):
                                    line = f"--- a/{new_path}\n"
                                    modified = True
                                    break
                                elif line.startswith(f"+++ b/{old_path}"):
                                    line = f"+++ b/{new_path}\n"
                                    modified = True
                                    break
                            new_diff_lines.append(line)
                        
                        # Write adjusted patch
                        adjusted_diff = "".join(new_diff_lines)
                        patch_file.write_text(adjusted_diff)
                        
                        # Retry with adjusted paths
                        if git_manager and isinstance(git_manager, GitBranchManager):
                            success_adj, output_adj = git_manager._run_git_command("apply", "--check", "--whitespace=nowarn", str(patch_file))
                        else:
                            result_adj = subprocess.run(
                                ["git", "apply", "--check", "--whitespace=nowarn", str(patch_file)],
                                cwd=repo_root,
                                capture_output=True,
                                text=True
                            )
                            success_adj = result_adj.returncode == 0
                            output_adj = result_adj.stderr or result_adj.stdout
                        
                        if success_adj:
                            # Apply the adjusted patch
                            if verbose:
                                print("✓ Adjusted patch can be applied")
                            
                            if git_manager and isinstance(git_manager, GitBranchManager):
                                success_apply, output_apply = git_manager._run_git_command("apply", "--whitespace=nowarn", str(patch_file))
                            else:
                                result_apply = subprocess.run(
                                    ["git", "apply", "--whitespace=nowarn", str(patch_file)],
                                    cwd=repo_root,
                                    capture_output=True,
                                    text=True
                                )
                                success_apply = result_apply.returncode == 0
                            
                            if success_apply:
                                # Get changed files
                                if git_manager and isinstance(git_manager, GitBranchManager):
                                    success1, unstaged = git_manager._run_git_command("diff", "--name-only")
                                    success2, staged = git_manager._run_git_command("diff", "--name-only", "--cached")
                                    success3, untracked = git_manager._run_git_command("ls-files", "--others", "--exclude-standard")
                                    output = "\n".join([unstaged, staged, untracked]).strip()
                                else:
                                    result1 = subprocess.run(["git", "diff", "--name-only"], cwd=repo_root, capture_output=True, text=True)
                                    result2 = subprocess.run(["git", "diff", "--name-only", "--cached"], cwd=repo_root, capture_output=True, text=True)
                                    result3 = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=repo_root, capture_output=True, text=True)
                                    output = "\n".join([result1.stdout, result2.stdout, result3.stdout]).strip()
                                
                                changed_files = [Path(repo_root) / f.strip() for f in output.split('\n') if f.strip()]
                                return changed_files
            
            # Original error handling continues if dynamic adjustment didn't work
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
            
            # Save the failed patch for debugging
            if telemetry and hasattr(telemetry, 'save_artifact'):
                import hashlib
                patch_hash = hashlib.md5(diff_text.encode()).hexdigest()[:8]
                telemetry.save_artifact(f"failed_patches/patch_{patch_hash}.diff", diff_text)
            
            # Do NOT attempt Python fallback here – return empty result on failure
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
            # Determine changed files (excluding the temporary patch file)
            changed_lines = [line.strip() for line in output.splitlines() 
                           if line.strip() and not line.endswith('.patch')]
            
            # If repo_path is a subdirectory of a git repo, strip that prefix from paths
            # Use the same git_toplevel detection as above
            if git_toplevel and git_toplevel != repo_root.resolve():
                try:
                    prefix_parts = repo_root.resolve().relative_to(git_toplevel).parts
                except ValueError:
                    # repo_root is not under git_toplevel, no prefix to strip
                    prefix_parts = ()
            else:
                prefix_parts = ()
            
            changed_files: List[Path] = []
            for line in changed_lines:
                p = Path(line)
                if prefix_parts and len(p.parts) > len(prefix_parts) and p.parts[:len(prefix_parts)] == prefix_parts:
                    # Strip the repo_path prefix (e.g., 'examples/demos/demo_math_ops')
                    p = Path(*p.parts[len(prefix_parts)])
                # Join with repo_root to get the correct absolute path
                changed_files.append((repo_root / p).resolve())
            
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
        except Exception as e:
            if verbose:
                print(f"Warning: Could not delete temporary patch file: {e}")
        
        # Clean up old patch files in .nova directory (older than 1 hour)
        try:
            import time
            current_time = time.time()
            for old_patch in nova_dir.glob("*.patch"):
                if (current_time - old_patch.stat().st_mtime) > 3600:  # 1 hour
                    old_patch.unlink()
        except Exception:
            pass  # Ignore cleanup errors


__all__ = [
    "read_text",
    "write_text_safe",
    "apply_unified_diff",
    "apply_patch_with_git",
    "rollback_on_failure",
    "apply_and_commit_patch",
]
