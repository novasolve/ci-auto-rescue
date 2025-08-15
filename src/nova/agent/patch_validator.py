"""
Patch validation and formatting utilities for Nova CI-Rescue.
Handles patch format fixes and duplicate definition detection.
"""

import re
from pathlib import Path
from typing import Optional

class PatchValidator:
    """Utility to fix patch formatting and validate patches (duplicate definitions, etc.)."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        # Determine if project uses src/ layout for source code
        self.uses_src_layout = False
        pyproject_path = self.repo_path / "pyproject.toml"
        if pyproject_path.exists():
            try:
                text = pyproject_path.read_text()
                if re.search(r'package_dir\s*=\s*.*src', text) or \
                   re.search(r'where\s*=\s*\[\s*["\']src["\']\\s*\]', text) or \
                   re.search(r'from\s*=\s*["\']src["\']', text):
                    self.uses_src_layout = True
            except Exception:
                pass

    def fix_patch_format(self, patch_diff: str) -> str:
        """Ensure the patch diff is in proper unified diff format with correct file paths."""
        patch_diff = patch_diff.rstrip()
        # Remove trailing partial characters that aren't part of the diff
        if patch_diff and patch_diff[-1] not in '\n+-@ \\':
            while patch_diff and patch_diff[-1] not in '\n+-@ \\' + 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789)"}\'':
                patch_diff = patch_diff[:-1]
        lines = patch_diff.split('\n')
        fixed_lines = []
        in_hunk = False
        
        for line in lines:
            if line.startswith('--- '):
                parts = line.split()
                if len(parts) >= 2:
                    target = parts[1]
                    if 'dev/null' in target:
                        line = '--- /dev/null'
                    else:
                        if target.startswith('a/'):
                            target = target[2:]
                        target = target.lstrip('/')
                        fixed_path = self._resolve_path(target)
                        line = f"--- a/{fixed_path}"
                in_hunk = False
            elif line.startswith('+++ '):
                parts = line.split()
                if len(parts) >= 2:
                    target = parts[1]
                    if 'dev/null' in target:
                        line = '+++ /dev/null'
                    else:
                        if target.startswith('b/'):
                            target = target[2:]
                        target = target.lstrip('/')
                        fixed_path = self._resolve_path(target)
                        line = f"+++ b/{fixed_path}"
                in_hunk = False
            elif line.startswith('@@'):
                in_hunk = True
                if not re.match(r'@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@', line):
                    line = '@@ -1,1 +1,1 @@'
            elif in_hunk and line and not line.startswith(('+', '-', ' ', '\\')):
                line = ' ' + line
            fixed_lines.append(line)
        return '\n'.join(fixed_lines)

    def _resolve_path(self, target: str) -> str:
        """Resolve file path to correct location in repository."""
        fixed_path = target
        
        # Check if file exists at given path
        if (self.repo_path / fixed_path).exists():
            return fixed_path
        
        # Try with src/ prefix
        if (self.repo_path / 'src' / fixed_path).exists():
            return f"src/{fixed_path}"
        
        # If using src/ layout, check if module is in src/
        if self.uses_src_layout and (self.repo_path / 'src').exists():
            top_packages = [d.name for d in (self.repo_path / 'src').iterdir() if d.is_dir()]
            first_part = fixed_path.split('/')[0] if '/' in fixed_path else fixed_path.split('.')[0]
            if first_part in top_packages:
                return f"src/{fixed_path}"
        
        # Strip redundant src/ if already in path
        if 'src/' in fixed_path and not fixed_path.startswith('src/'):
            idx = fixed_path.find('src/')
            candidate = fixed_path[idx:] if idx != -1 else fixed_path
            if candidate and (self.repo_path / candidate).exists():
                return candidate
        
        # Strip repository name from path
        if self.repo_path.name in fixed_path:
            idx = fixed_path.rfind(self.repo_path.name)
            candidate = fixed_path[idx+len(self.repo_path.name)+1:] if idx != -1 else fixed_path
            if candidate and (self.repo_path / candidate).exists():
                return candidate
        
        return fixed_path

    def detect_duplicate_defs(self, patch: str) -> Optional[str]:
        """Detects if a patch adds a duplicate function definition without removing the original."""
        try:
            patch_lines = patch.split('\n')
            current_file: Optional[str] = None
            
            for line in patch_lines:
                if line.startswith('+++ '):
                    parts = line.split()
                    if len(parts) > 1:
                        file_path = parts[1]
                        if file_path.startswith('b/'):
                            file_path = file_path[2:]
                        # Resolve the actual file path
                        if not (self.repo_path / file_path).exists():
                            alt_path = self.repo_path / 'src' / file_path
                            if alt_path.exists():
                                file_path = str(Path('src') / file_path)
                        current_file = file_path
                    else:
                        current_file = None
                    continue
                
                if not current_file:
                    continue
                
                # Only check Python files
                if not current_file.endswith('.py'):
                    continue
                
                if line.startswith('+'):
                    stripped = line[1:].lstrip()
                    if stripped.startswith('def '):
                        func_name = stripped[len('def '):].split('(')[0].strip()
                        orig_path = self.repo_path / current_file
                        original_content = ""
                        try:
                            original_content = orig_path.read_text()
                        except Exception:
                            original_content = ""
                        
                        if f"def {func_name}(" in original_content:
                            # Ensure the original def is being removed somewhere in patch
                            original_def_removed = any(
                                ol.startswith('-') and ol[1:].lstrip().startswith(f"def {func_name}(")
                                for ol in patch_lines
                            )
                            if not original_def_removed:
                                return (
                                    f"Patch introduces a duplicate definition of function '{func_name}' "
                                    f"in {current_file}. Modify the existing function instead of adding a new one."
                                )
            return None
        except Exception:
            return None
