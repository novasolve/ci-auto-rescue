"""
Patch validation and preflight checks for Nova CI-Rescue.
Catches common bad patches before they're applied.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set, Tuple
import re

_DEF_ADD_RE = re.compile(r'^\+\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
_DEF_DEL_RE = re.compile(r'^\-\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
_CLASS_ADD_RE = re.compile(r'^\+\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)')
_CLASS_DEL_RE = re.compile(r'^\-\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)')
_FILE_HEADER_ADD_RE = re.compile(r'^\+\+\+\s+b\/(.+)$')
_FILE_HEADER_DEL_RE = re.compile(r'^\-\-\-\s+a\/(.+)$')


def preflight_patch_checks(patch_text: str, *,
                           forbid_test_edits: bool = True,
                           forbid_config_edits: bool = True) -> Tuple[bool, List[str]]:
    """
    Fast textual checks that catch common bad patches:
    - duplicate function/class definitions (added without removing the old)
    - unauthorized test edits (unless explicitly allowed)
    - config file modifications
    
    Args:
        patch_text: The unified diff text to check
        forbid_test_edits: If True, reject patches that modify test files
        forbid_config_edits: If True, reject patches that modify config files
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues: List[str] = []
    files_touched: List[str] = []
    
    # Parse patch to find all touched files
    for line in patch_text.splitlines():
        m_add = _FILE_HEADER_ADD_RE.match(line)
        if m_add:
            files_touched.append(m_add.group(1))
    
    # Check for forbidden file modifications
    if forbid_test_edits:
        test_files = [f for f in files_touched 
                     if 'test' in f.lower() or f.startswith('tests/') or '/tests/' in f]
        if test_files:
            issues.append(
                f"Patch attempts to modify test files: {', '.join(test_files[:3])}. "
                "Tests should not be modified unless explicitly approved."
            )
    
    if forbid_config_edits:
        config_patterns = [
            'pyproject.toml', 'setup.py', 'setup.cfg', 'requirements.txt',
            '.github/', '.gitlab-ci', 'Dockerfile', 'docker-compose',
            'package.json', 'poetry.lock', 'Pipfile'
        ]
        config_files = [f for f in files_touched 
                       if any(pattern in f for pattern in config_patterns)]
        if config_files:
            issues.append(
                f"Patch attempts to modify configuration files: {', '.join(config_files[:3])}. "
                "Config modifications are restricted for safety."
            )
    
    # Track added/removed definitions per file
    per_file_added_defs: Dict[str, Set[str]] = {}
    per_file_removed_defs: Dict[str, Set[str]] = {}
    per_file_added_classes: Dict[str, Set[str]] = {}
    per_file_removed_classes: Dict[str, Set[str]] = {}
    current_file = None
    
    # Parse patch line by line
    for line in patch_text.splitlines():
        # Update current file context
        m_add = _FILE_HEADER_ADD_RE.match(line)
        if m_add:
            current_file = m_add.group(1)
            continue
        
        if current_file is None:
            continue
        
        # Only check Python files
        if not current_file.endswith('.py'):
            continue
        
        # Check for function definitions
        ad = _DEF_ADD_RE.match(line)
        if ad:
            per_file_added_defs.setdefault(current_file, set()).add(ad.group(1))
            continue
        
        dl = _DEF_DEL_RE.match(line)
        if dl:
            per_file_removed_defs.setdefault(current_file, set()).add(dl.group(1))
            continue
        
        # Check for class definitions
        ac = _CLASS_ADD_RE.match(line)
        if ac:
            per_file_added_classes.setdefault(current_file, set()).add(ac.group(1))
            continue
        
        cc = _CLASS_DEL_RE.match(line)
        if cc:
            per_file_removed_classes.setdefault(current_file, set()).add(cc.group(1))
            continue
    
    # Check for duplicate function definitions
    for f, added in per_file_added_defs.items():
        removed = per_file_removed_defs.get(f, set())
        missing = sorted(added - removed)
        if missing:
            issues.append(
                f"{f}: Adding functions {missing} without removing originals. "
                "This will create duplicate definitions. Replace the existing functions instead."
            )
    
    # Check for duplicate class definitions
    for f, added in per_file_added_classes.items():
        removed = per_file_removed_classes.get(f, set())
        missing = sorted(added - removed)
        if missing:
            issues.append(
                f"{f}: Adding classes {missing} without removing originals. "
                "This will create duplicate definitions. Replace the existing classes instead."
            )
    
    # Check for suspiciously large patches
    line_count = len(patch_text.splitlines())
    if line_count > 1000:
        issues.append(
            f"Patch is very large ({line_count} lines). "
            "Consider breaking it into smaller, focused changes."
        )
    
    # Check for binary file modifications
    if b'\x00' in patch_text.encode('utf-8', errors='ignore'):
        issues.append("Patch appears to contain binary data, which is not supported.")
    
    return (len(issues) == 0, issues)


def validate_patch_structure(patch_text: str) -> Tuple[bool, List[str]]:
    """
    Validate that a patch has proper unified diff structure.
    
    Args:
        patch_text: The patch text to validate
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues: List[str] = []
    
    if not patch_text or not patch_text.strip():
        issues.append("Empty patch")
        return False, issues
    
    lines = patch_text.splitlines()
    
    # Check for file headers
    has_old_file = any(line.startswith('---') for line in lines)
    has_new_file = any(line.startswith('+++') for line in lines)
    
    if not has_old_file:
        issues.append("Missing '---' header for original file")
    if not has_new_file:
        issues.append("Missing '+++' header for modified file")
    
    # Check for hunk headers
    has_hunks = any(line.startswith('@@') for line in lines)
    if not has_hunks:
        issues.append("No hunk headers found (lines starting with @@)")
    
    # Validate hunk header format
    hunk_re = re.compile(r'^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@')
    for line in lines:
        if line.startswith('@@'):
            if not hunk_re.match(line):
                issues.append(f"Invalid hunk header format: {line}")
    
    return (len(issues) == 0, issues)
