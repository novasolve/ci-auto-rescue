"""
Post-application sanity checks for Nova CI-Rescue.
Validates that patches don't introduce syntax errors.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional, Tuple
import ast
import subprocess


def ast_sanity_check(paths: Iterable[Path], verbose: bool = False) -> Tuple[bool, List[str]]:
    """
    Parse changed Python files to catch syntax errors.
    
    Args:
        paths: Iterable of file paths to check
        verbose: Enable verbose output
        
    Returns:
        Tuple of (all_valid, list_of_issues)
    """
    issues: List[str] = []
    checked_count = 0
    
    for p in paths:
        p = Path(p)
        
        # Only check Python files
        if not str(p).endswith('.py'):
            continue
        
        # Skip if file was deleted
        if not p.exists():
            continue
        
        checked_count += 1
        
        try:
            # Read and parse the file
            content = p.read_text(encoding='utf-8')
            ast.parse(content, filename=str(p))
            
            if verbose:
                print(f"✓ {p.name}: Syntax valid")
                
        except SyntaxError as e:
            # Detailed syntax error with line number
            issues.append(
                f"{p.relative_to(p.parent.parent) if p.parent.parent.exists() else p.name}: "
                f"SyntaxError at line {e.lineno}: {e.msg}"
            )
            if verbose:
                print(f"✗ {p.name}: SyntaxError at line {e.lineno}: {e.msg}")
                
        except Exception as e:
            # Other parsing errors
            issues.append(f"{p.name}: Failed to parse: {e}")
            if verbose:
                print(f"✗ {p.name}: Failed to parse: {e}")
    
    if verbose and checked_count > 0:
        print(f"Checked {checked_count} Python files")
    
    return (len(issues) == 0, issues)


def run_basic_import_check(repo_root: Path, changed_files: List[Path],
                          verbose: bool = False) -> Tuple[bool, List[str]]:
    """
    Try to import changed modules to catch import errors.
    
    Args:
        repo_root: Repository root path
        changed_files: List of changed file paths
        verbose: Enable verbose output
        
    Returns:
        Tuple of (all_valid, list_of_issues)
    """
    issues: List[str] = []
    
    for file_path in changed_files:
        if not str(file_path).endswith('.py'):
            continue
        
        # Skip test files
        if 'test' in str(file_path).lower():
            continue
        
        try:
            # Convert file path to module name
            rel_path = file_path.relative_to(repo_root)
            module_parts = []
            
            for part in rel_path.parts[:-1]:  # Exclude the .py file
                module_parts.append(part)
            
            # Add the file name without .py
            module_parts.append(rel_path.stem)
            
            # Skip if it's __init__.py
            if module_parts[-1] == '__init__':
                module_parts = module_parts[:-1]
            
            module_name = '.'.join(module_parts)
            
            # Try to compile the module
            result = subprocess.run(
                ["python", "-m", "py_compile", str(file_path)],
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                # Extract just the error message, not the full traceback
                if 'SyntaxError' in error_msg:
                    issues.append(f"{file_path.name}: Import/compilation failed: {error_msg.split('SyntaxError')[1].split('\\n')[0]}")
                else:
                    issues.append(f"{file_path.name}: Import/compilation failed")
                    
        except subprocess.TimeoutExpired:
            # Skip if compilation takes too long
            continue
        except Exception:
            # Skip other errors silently
            continue
    
    return (len(issues) == 0, issues)


def check_indentation_consistency(paths: Iterable[Path], 
                                 verbose: bool = False) -> Tuple[bool, List[str]]:
    """
    Check for mixed tabs and spaces in Python files.
    
    Args:
        paths: Iterable of file paths to check
        verbose: Enable verbose output
        
    Returns:
        Tuple of (all_valid, list_of_issues)
    """
    issues: List[str] = []
    
    for p in paths:
        p = Path(p)
        
        if not str(p).endswith('.py') or not p.exists():
            continue
        
        try:
            content = p.read_text(encoding='utf-8')
            lines = content.splitlines()
            
            has_tabs = any('\t' in line for line in lines)
            has_spaces = any(line.startswith('    ') for line in lines)
            
            if has_tabs and has_spaces:
                issues.append(
                    f"{p.name}: Mixed tabs and spaces for indentation. "
                    "This will cause IndentationError."
                )
                
        except Exception:
            continue
    
    return (len(issues) == 0, issues)


def validate_json_files(paths: Iterable[Path], 
                        verbose: bool = False) -> Tuple[bool, List[str]]:
    """
    Validate JSON syntax for any changed JSON files.
    
    Args:
        paths: Iterable of file paths to check
        verbose: Enable verbose output
        
    Returns:
        Tuple of (all_valid, list_of_issues)
    """
    import json
    issues: List[str] = []
    
    for p in paths:
        p = Path(p)
        
        if not str(p).endswith('.json') or not p.exists():
            continue
        
        try:
            content = p.read_text(encoding='utf-8')
            json.loads(content)
            
            if verbose:
                print(f"✓ {p.name}: Valid JSON")
                
        except json.JSONDecodeError as e:
            issues.append(f"{p.name}: Invalid JSON at line {e.lineno}: {e.msg}")
            if verbose:
                print(f"✗ {p.name}: Invalid JSON at line {e.lineno}: {e.msg}")
                
        except Exception as e:
            issues.append(f"{p.name}: Failed to validate: {e}")
    
    return (len(issues) == 0, issues)


def comprehensive_post_apply_check(repo_root: Path, changed_files: List[Path],
                                   verbose: bool = False) -> Tuple[bool, List[str]]:
    """
    Run all post-apply checks on changed files.
    
    Args:
        repo_root: Repository root path
        changed_files: List of changed file paths
        verbose: Enable verbose output
        
    Returns:
        Tuple of (all_valid, list_of_all_issues)
    """
    all_issues = []
    
    # Check Python syntax
    ok, issues = ast_sanity_check(changed_files, verbose)
    if not ok:
        all_issues.extend(issues)
    
    # Check indentation
    ok, issues = check_indentation_consistency(changed_files, verbose)
    if not ok:
        all_issues.extend(issues)
    
    # Check imports/compilation
    ok, issues = run_basic_import_check(repo_root, changed_files, verbose)
    if not ok:
        all_issues.extend(issues)
    
    # Check JSON files if any
    ok, issues = validate_json_files(changed_files, verbose)
    if not ok:
        all_issues.extend(issues)
    
    return (len(all_issues) == 0, all_issues)
