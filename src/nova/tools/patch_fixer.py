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
    
    lines = patch_text.split('\n')
    fixed_lines = []
    current_file = None
    i = 0
    
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
                while j < len(lines) and not lines[j].startswith(('@@', '---', '+++')):
                    if lines[j] or lines[j].startswith(('+', '-', ' ', '\\')):
                        hunk_lines.append(lines[j])
                    j += 1
                
                # Count actual lines
                actual_old = 0
                actual_new = 0
                for hunk_line in hunk_lines:
                    if hunk_line.startswith('-'):
                        actual_old += 1
                    elif hunk_line.startswith('+'):
                        actual_new += 1
                    elif hunk_line.startswith(' ') or (hunk_line and not hunk_line.startswith('\\')):
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
                fixed_lines.append(line)
                i += 1
        else:
            # Other lines (comments, etc.)
            fixed_lines.append(line)
            i += 1
    
    return '\n'.join(fixed_lines)


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
