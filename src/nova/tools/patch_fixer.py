"""
Patch format fixer to handle malformed patches from LLMs.
"""

import re
from typing import List, Tuple


def fix_patch_format(patch_text: str, verbose: bool = False) -> str:
    """
    Fix common issues in LLM-generated patches.
    
    Args:
        patch_text: The potentially malformed patch
        verbose: Enable verbose output
        
    Returns:
        Fixed patch text
    """
    if not patch_text:
        return patch_text
    
    # Clean up trailing garbage characters that LLMs sometimes add
    patch_text = patch_text.rstrip()
    # Remove common trailing artifacts like %, ```, etc
    while patch_text and patch_text[-1] in '%`':
        patch_text = patch_text[:-1]
        if verbose:
            print(f"Removed trailing '{patch_text[-1] if patch_text else ''}' character")
    
    lines = patch_text.split('\n')
    fixed_lines = []
    current_file = None
    i = 0
    
    # Check if patch appears truncated
    patch_appears_truncated = False
    if lines:
        last_line = lines[-1].strip()
        # Common signs of truncation
        if (last_line and 
            not last_line.startswith(('\\', ' ', '+', '-', '@@')) and
            not last_line == '' and
            '...' in last_line or 
            'truncated' in last_line.lower() or
            last_line.endswith(('...', '…'))):
            patch_appears_truncated = True
            if verbose:
                print(f"Warning: Patch appears truncated. Last line: '{last_line}'")
    
    while i < len(lines):
        line = lines[i]
        
        # File headers
        if line.startswith('--- '):
            # Ensure proper format
            if not line.startswith('--- a/'):
                parts = line.split()
                if len(parts) >= 2:
                    filename = parts[1].lstrip('/')
                    line = f"--- a/{filename}"
            fixed_lines.append(line)
            i += 1
            
        elif line.startswith('+++ '):
            # Ensure proper format
            if not line.startswith('+++ b/'):
                parts = line.split()
                if len(parts) >= 2:
                    filename = parts[1].lstrip('/')
                    line = f"+++ b/{filename}"
                    current_file = filename
            fixed_lines.append(line)
            i += 1
            
        elif line.startswith('@@'):
            # Parse hunk header
            hunk_header = parse_hunk_header(line)
            if hunk_header:
                old_start, old_count, new_start, new_count = hunk_header
                
                # Collect hunk lines
                hunk_lines = []
                j = i + 1
                # Be more lenient with hunk boundaries for truncated patches
                while j < len(lines):
                    next_line = lines[j]
                    # Stop if we hit another hunk or file header
                    if next_line.startswith(('@@', '---', '+++')):
                        break
                    # Include lines that look like diff content
                    if next_line.startswith(('+', '-', ' ', '\\')) or next_line.strip() == '':
                        hunk_lines.append(next_line)
                    elif j == i + 1:
                        # If the very next line after @@ doesn't look like diff content,
                        # the patch might be corrupted - stop here
                        if verbose:
                            print(f"Warning: Unexpected line after hunk header: '{next_line}'")
                        break
                    j += 1
                
                # Count actual lines
                actual_old = 0
                actual_new = 0
                for hunk_line in hunk_lines:
                    if hunk_line.startswith('-') and not hunk_line.startswith('---'):
                        actual_old += 1
                    elif hunk_line.startswith('+') and not hunk_line.startswith('+++'):
                        actual_new += 1
                    elif hunk_line.startswith(' ') or hunk_line.strip() == '':
                        actual_old += 1
                        actual_new += 1
                    elif not hunk_line.startswith('\\'):
                        # Context line without proper prefix
                        actual_old += 1
                        actual_new += 1
                
                # Fix the hunk header with correct counts
                if old_count != actual_old or new_count != actual_new:
                    if verbose:
                        print(f"Fixing hunk header: was @@ -{old_start},{old_count} +{new_start},{new_count} @@")
                        print(f"                     now @@ -{old_start},{actual_old} +{new_start},{actual_new} @@")
                    line = f"@@ -{old_start},{actual_old} +{new_start},{actual_new} @@"
                
                fixed_lines.append(line)
                
                # Add the hunk lines with proper formatting
                for hunk_line in hunk_lines:
                    if hunk_line.startswith(('+', '-', ' ', '\\')):
                        fixed_lines.append(hunk_line)
                    elif hunk_line.strip() == '':
                        # Empty line should have space prefix
                        fixed_lines.append(' ')
                    else:
                        # Context line without prefix - add space
                        fixed_lines.append(' ' + hunk_line)
                
                i = j
            else:
                # Invalid hunk header, keep as is
                if verbose:
                    print(f"Warning: Invalid hunk header: '{line}'")
                fixed_lines.append(line)
                i += 1
        else:
            # Other lines
            # Skip lines that look like they might be part of a truncated explanation
            if i == len(lines) - 1 and line.strip() and not line.startswith(('+', '-', ' ', '\\')):
                if verbose:
                    print(f"Skipping potential truncation artifact: '{line}'")
                i += 1
                continue
            fixed_lines.append(line)
            i += 1
    
    # Remove any trailing junk characters in diff content lines (e.g., '%' from truncated output)
    for idx, line in enumerate(fixed_lines):
        if line.startswith(('+', '-', ' ')) and line.rstrip().endswith(('%', '`')):
            if verbose:
                print(f"Removing trailing artifact character from line: '{line}'")
            # Strip trailing `%` or `` ` `` (and any trailing spaces) from the line
            fixed_lines[idx] = line.rstrip('%` ')
    
    fixed_patch_text = '\n'.join(fixed_lines)
    
    # Ensure the patch ends with a newline (to avoid EOF issues in git apply)
    if not fixed_patch_text.endswith('\n'):
        fixed_patch_text += '\n'
    
    return fixed_patch_text


def parse_hunk_header(line: str) -> Tuple[int, int, int, int]:
    """
    Parse a hunk header line.
    
    Args:
        line: Hunk header like "@@ -1,3 +1,4 @@"
        
    Returns:
        Tuple of (old_start, old_count, new_start, new_count) or None
    """
    match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
    if match:
        old_start = int(match.group(1))
        old_count = int(match.group(2)) if match.group(2) else 1
        new_start = int(match.group(3))
        new_count = int(match.group(4)) if match.group(4) else 1
        return old_start, old_count, new_start, new_count
    return None


def count_hunk_lines(lines: List[str]) -> Tuple[int, int]:
    """
    Count the actual old and new lines in a hunk.
    
    Args:
        lines: Lines following a hunk header
        
    Returns:
        Tuple of (old_line_count, new_line_count)
    """
    old_count = 0
    new_count = 0
    
    for line in lines:
        if line.startswith('@@'):
            # Next hunk started
            break
        elif line.startswith('---') or line.startswith('+++'):
            # File header for next file
            break
        elif line.startswith('-'):
            old_count += 1
        elif line.startswith('+'):
            new_count += 1
        elif line.startswith(' ') or line == '':
            # Context line
            old_count += 1
            new_count += 1
        elif line.startswith('\\'):
            # No newline indicator - don't count
            continue
        else:
            # Assume it's a context line without prefix
            old_count += 1
            new_count += 1
    
    return old_count, new_count


def validate_patch(patch_text: str) -> Tuple[bool, str]:
    """
    Validate if a patch is well-formed.
    
    Args:
        patch_text: The patch to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not patch_text or not patch_text.strip():
        return False, "Empty patch"
    
    lines = patch_text.split('\n')
    
    # Check for obvious truncation
    if lines:
        last_line = lines[-1].strip()
        if (last_line and 
            ('...' in last_line or 'truncated' in last_line.lower() or
             last_line.endswith(('...', '…')))):
            return False, "Patch appears to be truncated"
    
    # Check for file headers
    has_old_file = any(line.startswith('---') for line in lines)
    has_new_file = any(line.startswith('+++') for line in lines)
    
    if not has_old_file:
        return False, "Missing --- header"
    if not has_new_file:
        return False, "Missing +++ header"
    
    # Check for hunk headers
    has_hunks = any(line.startswith('@@') for line in lines)
    if not has_hunks:
        return False, "No hunk headers found"
    
    # Check hunk format
    for line in lines:
        if line.startswith('@@'):
            if not parse_hunk_header(line):
                return False, f"Invalid hunk header: {line}"
    
    return True, "Valid"


def extract_simple_changes(patch_text: str) -> List[Tuple[str, str, str]]:
    """
    Extract simple change tuples from a patch for fallback application.
    
    Args:
        patch_text: The patch text
        
    Returns:
        List of (filename, old_line, new_line) tuples
    """
    changes = []
    current_file = None
    lines = patch_text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if line.startswith('+++'):
            # Extract filename
            parts = line.split()
            if len(parts) >= 2:
                filename = parts[1].lstrip('b/').lstrip('/')
                current_file = filename
        
        elif line.startswith('-') and not line.startswith('---'):
            # Found a removal, look for corresponding addition
            old_line = line[1:]
            
            # Look ahead for the addition
            for j in range(i+1, min(i+10, len(lines))):
                if lines[j].startswith('+') and not lines[j].startswith('+++'):
                    new_line = lines[j][1:]
                    if current_file:
                        changes.append((current_file, old_line, new_line))
                    break
        
        i += 1
    
    return changes


def attempt_patch_reconstruction(patch_text: str, repo_root: str, verbose: bool = False) -> str:
    """
    Attempt to reconstruct a truncated patch by analyzing what was changed.
    
    Args:
        patch_text: The truncated patch text
        repo_root: Repository root path
        verbose: Enable verbose output
        
    Returns:
        Reconstructed patch text (may still be incomplete)
    """
    import os
    from pathlib import Path
    
    # Extract what we can from the truncated patch
    changes = extract_simple_changes(patch_text)
    
    if not changes and verbose:
        print("Could not extract any changes from truncated patch")
        return patch_text
    
    # Group changes by file
    file_changes = {}
    for filename, old_line, new_line in changes:
        if filename not in file_changes:
            file_changes[filename] = []
        file_changes[filename].append((old_line, new_line))
    
    # Try to reconstruct a complete patch
    reconstructed_lines = []
    
    for filename, changes_list in file_changes.items():
        file_path = Path(repo_root) / filename
        
        if not file_path.exists():
            if verbose:
                print(f"Warning: File {filename} not found, skipping reconstruction")
            continue
        
        # Read the file content
        try:
            with open(file_path, 'r') as f:
                file_lines = f.readlines()
        except Exception as e:
            if verbose:
                print(f"Error reading {filename}: {e}")
            continue
        
        # Create a simple patch for this file
        reconstructed_lines.append(f"--- a/{filename}")
        reconstructed_lines.append(f"+++ b/{filename}")
        
        # Find and replace each change
        for old_line, new_line in changes_list:
            # Find the line number
            for i, file_line in enumerate(file_lines):
                if file_line.rstrip() == old_line.rstrip():
                    # Found the line to change
                    line_num = i + 1
                    
                    # Create a simple hunk
                    reconstructed_lines.append(f"@@ -{line_num},1 +{line_num},1 @@")
                    reconstructed_lines.append(f"-{old_line}")
                    reconstructed_lines.append(f"+{new_line}")
                    break
        else:
            if verbose:
                print(f"Warning: Could not find line '{old_line}' in {filename}")
    
    if reconstructed_lines:
        if verbose:
            print(f"Reconstructed patch with {len(file_changes)} file(s)")
        return '\n'.join(reconstructed_lines)
    
    return patch_text
