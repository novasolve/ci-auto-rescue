"""
Intelligent patch application with fallback strategies for Nova CI-Rescue.
Handles path mismatches and applies patches robustly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional, Tuple
import subprocess
import re
import tempfile

_FILE_HEADER_ADD_RE = re.compile(r'^\+\+\+\s+b\/(.+)$')
_FILE_HEADER_DEL_RE = re.compile(r'^\-\-\-\s+a\/(.+)$')


class PatchApplyError(RuntimeError):
    """Raised when patch application fails."""
    pass


def apply_patch_with_fallback(patch_text: str, repo_root: Path, 
                             verbose: bool = False) -> List[Path]:
    """
    Apply a unified diff patch with intelligent fallback strategies.
    
    If initial application fails due to path mismatches, tries:
    1. Stripping common prefix directories (e.g., 'demo-failing-tests/')
    2. Inserting 'src/' prefix for files that exist there
    3. Smart reconstruction with fuzzy matching
    
    Args:
        patch_text: The unified diff text to apply
        repo_root: Repository root path
        verbose: Enable verbose output
        
    Returns:
        List of changed file paths
        
    Raises:
        PatchApplyError: If patch cannot be applied after all fallback attempts
    """
    repo_root = Path(repo_root).resolve()
    
    if verbose:
        print(f"Attempting to apply patch to {repo_root}")
    
    # 1) Try raw apply
    try:
        changed_files = _git_apply(patch_text, repo_root, verbose)
        if verbose:
            print(f"✓ Patch applied successfully: {len(changed_files)} files changed")
        return changed_files
    except PatchApplyError as e:
        err = str(e)
        if verbose:
            print(f"Initial apply failed: {err}")
    
    # 2) Try stripping common problematic prefixes
    stripped = _strip_common_prefix_from_paths(patch_text, repo_root)
    if stripped != patch_text:
        if verbose:
            print("Trying with stripped path prefixes...")
        try:
            changed_files = _git_apply(stripped, repo_root, verbose)
            if verbose:
                print(f"✓ Patch applied after stripping prefixes: {len(changed_files)} files changed")
            return changed_files
        except PatchApplyError:
            if verbose:
                print("Stripped prefix attempt failed")
    
    # 3) Try inserting 'src/' prefix for missing files
    inserted = _insert_src_prefix_if_missing(patch_text, repo_root)
    if inserted != patch_text:
        if verbose:
            print("Trying with src/ prefix insertion...")
        try:
            changed_files = _git_apply(inserted, repo_root, verbose)
            if verbose:
                print(f"✓ Patch applied after src/ insertion: {len(changed_files)} files changed")
            return changed_files
        except PatchApplyError:
            if verbose:
                print("src/ prefix attempt failed")
    
    # 4) Try fuzzy reconstruction (this will be called from fs.py integration)
    # For now, raise the error
    raise PatchApplyError(
        f"Failed to apply patch after all fallback attempts. "
        f"Original error: {err}"
    )


# --- Helper functions ---

def _git_apply(patch_text: str, cwd: Path, verbose: bool = False) -> List[Path]:
    """
    Apply a patch using git apply and return changed files.
    
    Args:
        patch_text: The patch to apply
        cwd: Working directory
        verbose: Enable verbose output
        
    Returns:
        List of changed file paths
        
    Raises:
        PatchApplyError: If git apply fails
    """
    # Write patch to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
        f.write(patch_text)
        patch_file = Path(f.name)
    
    try:
        # Try to apply the patch
        result = subprocess.run(
            ["git", "apply", "--whitespace=fix", patch_file.as_posix()],
            cwd=str(cwd),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise PatchApplyError(result.stderr or result.stdout or "Unknown error")
        
        # Get list of changed files
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=True
        )
        
        changed_files = []
        for line in result.stdout.strip().splitlines():
            if line.strip():
                changed_files.append((cwd / line.strip()).resolve())
        
        return changed_files
        
    finally:
        # Clean up temp file
        patch_file.unlink(missing_ok=True)


def _collect_patch_targets(patch_text: str) -> List[str]:
    """
    Extract target file paths from a patch.
    
    Args:
        patch_text: The patch text
        
    Returns:
        List of target file paths
    """
    targets = []
    for line in patch_text.splitlines():
        m = _FILE_HEADER_ADD_RE.match(line)
        if m:
            targets.append(m.group(1))
    return targets


def _strip_common_prefix_from_paths(patch_text: str, repo_root: Path) -> str:
    """
    Strip common problematic prefixes from patch paths.
    
    Handles cases like:
    - 'demo-failing-tests/src/calculator.py' -> 'src/calculator.py'
    - 'repo-name/file.py' -> 'file.py'
    
    Args:
        patch_text: Original patch text
        repo_root: Repository root path
        
    Returns:
        Modified patch text with stripped prefixes
    """
    # Common prefixes to try stripping
    repo_name = repo_root.name
    candidates = {
        repo_name,
        'demo-failing-tests',
        'demo-repo',
        'demo_failing_tests',
        'demo_repo'
    }
    
    # Check if any files in the patch have these prefixes
    targets = _collect_patch_targets(patch_text)
    prefix_to_strip = None
    
    for target in targets:
        for prefix in candidates:
            if target.startswith(prefix + '/'):
                prefix_to_strip = prefix
                break
        if prefix_to_strip:
            break
    
    if not prefix_to_strip:
        return patch_text
    
    # Strip the prefix from all paths
    out_lines = []
    for line in patch_text.splitlines():
        m_add = _FILE_HEADER_ADD_RE.match(line)
        m_del = _FILE_HEADER_DEL_RE.match(line)
        
        if m_add:
            path = m_add.group(1)
            if path.startswith(prefix_to_strip + '/'):
                new_path = path[len(prefix_to_strip) + 1:]
            else:
                new_path = path
            out_lines.append(f"+++ b/{new_path}")
        elif m_del:
            path = m_del.group(1)
            if path.startswith(prefix_to_strip + '/'):
                new_path = path[len(prefix_to_strip) + 1:]
            else:
                new_path = path
            out_lines.append(f"--- a/{new_path}")
        else:
            out_lines.append(line)
    
    return '\n'.join(out_lines)


def _insert_src_prefix_if_missing(patch_text: str, repo_root: Path) -> str:
    """
    Insert 'src/' prefix for files that exist in src/ but patch doesn't specify.
    
    Args:
        patch_text: Original patch text
        repo_root: Repository root path
        
    Returns:
        Modified patch text with src/ prefixes where needed
    """
    out_lines = []
    modified = False
    
    for line in patch_text.splitlines():
        m_add = _FILE_HEADER_ADD_RE.match(line)
        m_del = _FILE_HEADER_DEL_RE.match(line)
        
        if m_add or m_del:
            tag = "+++" if m_add else "---"
            letter = "b" if m_add else "a"
            path = (m_add or m_del).group(1)
            
            # Check if file exists at path
            p = repo_root / path
            if not p.exists() and not path.startswith('src/'):
                # Try with src/ prefix
                p_src = repo_root / 'src' / path
                if p_src.exists():
                    path = f"src/{path}"
                    modified = True
            
            out_lines.append(f"{tag} {letter}/{path}")
        else:
            out_lines.append(line)
    
    return '\n'.join(out_lines) if modified else patch_text


def _intersects(changed: List[str], targets: set) -> bool:
    """
    Check if any changed files intersect with target files.
    
    Args:
        changed: List of changed file paths
        targets: Set of target file paths
        
    Returns:
        True if there's at least one intersection
    """
    return any(c in targets for c in changed)
