"""
Safety limits enforcement for Nova CI-Rescue patches.

This module provides safety checks to prevent excessive or dangerous modifications
from being applied automatically.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field

@dataclass
class SafetyConfig:
    """Configuration for safety limits."""
    max_lines_changed: int = 500  # Maximum total lines changed (added + removed) - aligned with CriticReviewTool
    max_files_modified: int = 10  # Maximum number of files that can be modified
    denied_paths: List[str] = field(default_factory=lambda: [
        # CI/CD configuration files
        ".github/workflows/*",
        ".gitlab-ci.yml",
        ".travis.yml",
        ".circleci/*",
        "Jenkinsfile",
        "azure-pipelines.yml",
        "bitbucket-pipelines.yml",
        ".buildkite/*",
        
        # Deployment and infrastructure
        "deploy/*",
        "deployment/*",
        "k8s/*",
        "kubernetes/*",
        "helm/*",
        "terraform/*",
        "ansible/*",
        "docker-compose*.yml",
        "Dockerfile*",
        
        # Security-sensitive files
        "**/secrets/*",
        "**/credentials/*",
        "**/.env*",
        "**/config/prod*",
        "**/config/production*",
        "**/*.pem",
        "**/*.key",
        "**/*.crt",
        "**/*.p12",
        "**/*.pfx",
        
        # Package management and dependencies
        "package-lock.json",
        "yarn.lock",
        "Gemfile.lock",
        "poetry.lock",
        "Pipfile.lock",
        "go.sum",
        "composer.lock",
        "Cargo.lock",
        
        # Version and release files
        "VERSION",
        "version.txt",
        "CHANGELOG.md",
        "CHANGELOG.rst",
        "RELEASES.md",
        
        # Database migrations and schemas
        "**/migrations/*",
        "**/db/migrate/*",
        "**/alembic/*",
        "**/schema.sql",
        "**/schema.rb",
        
        # Build and distribution files
        "dist/*",
        "build/*",
        "*.whl",
        "*.egg",
        "*.gem",
        "*.jar",
        "*.war",
        
        # System and IDE files
        ".git/*",
        ".gitignore",
        ".gitmodules",
        ".idea/*",
        ".vscode/*",
        "*.swp",
        "*.swo",
        ".DS_Store",
        "Thumbs.db"
    ])
    
    # Additional regex patterns for more complex path matching
    denied_path_patterns: List[str] = field(default_factory=lambda: [
        r".*\.min\.(js|css)$",  # Minified files
        r".*\.(pyc|pyo)$",       # Python bytecode
        r".*\.(so|dll|dylib)$",  # Binary libraries
    ])


@dataclass
class PatchAnalysis:
    """Results from analyzing a patch."""
    total_lines_added: int = 0
    total_lines_removed: int = 0
    total_lines_changed: int = 0
    files_modified: Set[str] = field(default_factory=set)
    files_added: Set[str] = field(default_factory=set)
    files_deleted: Set[str] = field(default_factory=set)
    denied_files: Set[str] = field(default_factory=set)
    violations: List[str] = field(default_factory=list)
    duplicate_functions: Set[str] = field(default_factory=set)  # Track potential duplicate function definitions
    is_safe: bool = True


class SafetyLimits:
    """Enforces safety limits on patches to prevent dangerous auto-modifications."""
    
    def __init__(self, config: Optional[SafetyConfig] = None, verbose: bool = False):
        """
        Initialize SafetyLimits with configuration.
        
        Args:
            config: Safety configuration. Uses defaults if not provided.
            verbose: Enable verbose output for debugging.
        """
        self.config = config or SafetyConfig()
        self.verbose = verbose
        
        # Override config from environment variables if set
        if os.environ.get("NOVA_MAX_LINES_CHANGED"):
            try:
                self.config.max_lines_changed = int(os.environ["NOVA_MAX_LINES_CHANGED"])
            except ValueError:
                pass  # Keep default if invalid value
        
        if os.environ.get("NOVA_MAX_FILES_MODIFIED"):
            try:
                self.config.max_files_modified = int(os.environ["NOVA_MAX_FILES_MODIFIED"])
            except ValueError:
                pass  # Keep default if invalid value
        
        if os.environ.get("NOVA_DENIED_PATHS"):
            # Parse comma-separated list of paths
            custom_paths = [p.strip() for p in os.environ["NOVA_DENIED_PATHS"].split(",")]
            self.config.denied_paths.extend(custom_paths)
        
        # Compile regex patterns for efficiency
        self.denied_patterns = [
            re.compile(pattern) for pattern in self.config.denied_path_patterns
        ]
    
    def analyze_patch(self, patch_text: str) -> PatchAnalysis:
        """
        Analyze a patch to extract statistics and identify affected files.
        
        Args:
            patch_text: The unified diff text to analyze.
            
        Returns:
            PatchAnalysis object with detailed information about the patch.
        """
        analysis = PatchAnalysis()
        lines = patch_text.split('\n')
        current_file = None
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # File headers
            if line.startswith('--- '):
                # Extract source file
                parts = line.split()
                if len(parts) >= 2:
                    if parts[1] == '/dev/null':
                        current_file = '/dev/null'
                    else:
                        current_file = self._extract_filename(parts[1])
                        
            elif line.startswith('+++ '):
                # Extract target file
                parts = line.split()
                if len(parts) >= 2:
                    if parts[1] == '/dev/null':
                        # File is being deleted
                        if current_file and current_file != '/dev/null':
                            analysis.files_deleted.add(current_file)
                    else:
                        filename = self._extract_filename(parts[1])
                        # File is being modified or added
                        if current_file == '/dev/null':
                            # New file (previous was /dev/null)
                            analysis.files_added.add(filename)
                        else:
                            # Modified file
                            analysis.files_modified.add(filename)
                        current_file = filename
                        
            elif line.startswith('@@'):
                # Hunk header - we can extract line counts but we'll count actual lines instead
                pass
                
            elif current_file and line.startswith('+') and not line.startswith('+++'):
                # Added line
                analysis.total_lines_added += 1
                analysis.total_lines_changed += 1
                
                # Check for potential duplicate function definitions
                # Look for Python function definitions being added
                if re.match(r'\+\s*def\s+(\w+)\s*\(', line):
                    func_match = re.match(r'\+\s*def\s+(\w+)\s*\(', line)
                    if func_match:
                        func_name = func_match.group(1)
                        # Check if this function is being added without removing the old one
                        # We'll check if there's a corresponding removal in the patch
                        has_removal = any(
                            re.match(rf'-\s*def\s+{re.escape(func_name)}\s*\(', l) 
                            for l in lines
                        )
                        if not has_removal:
                            # Function is being added without removing existing one
                            analysis.duplicate_functions.add(f"{func_name} in {current_file}")
                
            elif current_file and line.startswith('-') and not line.startswith('---'):
                # Removed line
                analysis.total_lines_removed += 1
                analysis.total_lines_changed += 1
                
            i += 1
        
        # Check for denied files
        all_files = analysis.files_modified | analysis.files_added | analysis.files_deleted
        for file_path in all_files:
            if self._is_denied_path(file_path):
                analysis.denied_files.add(file_path)
        
        return analysis
    
    def validate_patch(self, patch_text: str) -> Tuple[bool, List[str]]:
        """
        Validate a patch against safety limits.
        
        Args:
            patch_text: The unified diff text to validate.
            
        Returns:
            Tuple of (is_safe, list_of_violations)
        """
        analysis = self.analyze_patch(patch_text)
        violations = []
        
        # Check line count limit
        if analysis.total_lines_changed > self.config.max_lines_changed:
            violations.append(
                f"Exceeds maximum lines changed: {analysis.total_lines_changed} > {self.config.max_lines_changed}"
            )
        
        # Check file count limit
        total_files = len(analysis.files_modified | analysis.files_added | analysis.files_deleted)
        if total_files > self.config.max_files_modified:
            violations.append(
                f"Exceeds maximum files modified: {total_files} > {self.config.max_files_modified}"
            )
        
        # Check for denied paths
        if analysis.denied_files:
            denied_list = ', '.join(sorted(analysis.denied_files)[:5])  # Show first 5
            if len(analysis.denied_files) > 5:
                denied_list += f", ... ({len(analysis.denied_files) - 5} more)"
            violations.append(
                f"Attempts to modify restricted files: {denied_list}"
            )
        
        # Check for duplicate function definitions
        if analysis.duplicate_functions:
            dup_list = ', '.join(sorted(analysis.duplicate_functions)[:3])  # Show first 3
            if len(analysis.duplicate_functions) > 3:
                dup_list += f", ... ({len(analysis.duplicate_functions) - 3} more)"
            violations.append(
                f"Patch introduces duplicate function definitions: {dup_list}. "
                f"Functions should be modified in-place, not duplicated."
            )
        
        analysis.violations = violations
        analysis.is_safe = len(violations) == 0
        
        if self.verbose and violations:
            print(f"[SafetyLimits] Patch validation failed:")
            for violation in violations:
                print(f"  - {violation}")
        
        return analysis.is_safe, violations
    
    def get_friendly_error_message(self, violations: List[str]) -> str:
        """
        Generate a user-friendly error message explaining why the patch was rejected.
        
        Args:
            violations: List of safety violations.
            
        Returns:
            Formatted error message suitable for display to users.
        """
        if not violations:
            return "Patch passed safety checks."
        
        message_parts = [
            "🛡️ **Safety Check Failed**",
            "",
            "The proposed patch violates safety limits and cannot be automatically applied:",
            ""
        ]
        
        for i, violation in enumerate(violations, 1):
            message_parts.append(f"{i}. {violation}")
        
        message_parts.extend([
            "",
            "**Why these limits?**",
            "These safety limits help prevent:",
            "• Accidental breaking changes to critical infrastructure",
            "• Unintended modifications to security-sensitive files",
            "• Large-scale changes that should undergo manual review",
            "",
            "**What to do next?**",
            "• Review the patch manually to ensure changes are safe",
            "• If the changes are intentional, apply them manually",
            "• Consider breaking large changes into smaller, focused patches",
            "• For CI/CD or deployment changes, follow your organization's change management process"
        ])
        
        return "\n".join(message_parts)
    
    def _extract_filename(self, path_str: str) -> str:
        """
        Extract filename from patch header, removing prefixes like 'a/' or 'b/'.
        
        Args:
            path_str: Raw path string from patch header.
            
        Returns:
            Cleaned filename.
        """
        # Remove common git prefixes
        if path_str.startswith('a/') or path_str.startswith('b/'):
            return path_str[2:]
        return path_str.lstrip('/')
    
    def _is_denied_path(self, file_path: str) -> bool:
        """
        Check if a file path matches any denied patterns.
        
        Args:
            file_path: Path to check.
            
        Returns:
            True if the path is denied, False otherwise.
        """
        # Normalize the path
        path = Path(file_path).as_posix()
        
        # SPECIAL EXCEPTION: Allow our own workflow file
        if path == '.github/workflows/nova.yml':
            if self.verbose:
                print(f"[SafetyLimits] Allowing modification to nova.yml (own workflow)")
            return False
        
        # Check glob patterns
        for pattern in self.config.denied_paths:
            # Convert glob pattern to work with pathlib
            if self._matches_glob(path, pattern):
                if self.verbose:
                    print(f"[SafetyLimits] File '{path}' matches denied pattern '{pattern}'")
                return True
        
        # Check regex patterns
        for regex_pattern in self.denied_patterns:
            if regex_pattern.match(path):
                if self.verbose:
                    print(f"[SafetyLimits] File '{path}' matches denied regex pattern")
                return True
        
        return False
    
    def _matches_glob(self, path: str, pattern: str) -> bool:
        """
        Check if a path matches a glob pattern.
        
        Args:
            path: Path to check.
            pattern: Glob pattern.
            
        Returns:
            True if path matches pattern, False otherwise.
        """
        from fnmatch import fnmatch
        
        # Handle ** for recursive matching
        if '**' in pattern:
            # Convert ** to match any depth
            pattern = pattern.replace('**/', '*')
            pattern = pattern.replace('**', '*')
        
        # Check if the path or any parent directory matches
        path_obj = Path(path)
        
        # Check the file itself
        if fnmatch(path, pattern) or fnmatch(path_obj.name, pattern):
            return True
        
        # Check parent directories for patterns like 'deploy/*'
        for parent in path_obj.parents:
            parent_str = parent.as_posix()
            if fnmatch(f"{parent_str}/*", pattern):
                return True
            # Also check if any component matches
            for part in path_obj.parts:
                if fnmatch(part, pattern.strip('*/')):
                    return True
        
        return False


def check_patch_safety(
    patch_text: str,
    config: Optional[SafetyConfig] = None,
    verbose: bool = False
) -> Tuple[bool, str]:
    """
    Convenience function to check if a patch is safe to apply.
    
    Args:
        patch_text: The unified diff text to check.
        config: Optional safety configuration.
        verbose: Enable verbose output.
        
    Returns:
        Tuple of (is_safe, error_message_if_not_safe)
    """
    safety_limits = SafetyLimits(config=config, verbose=verbose)
    is_safe, violations = safety_limits.validate_patch(patch_text)
    
    if is_safe:
        return True, ""
    else:
        error_message = safety_limits.get_friendly_error_message(violations)
        return False, error_message


# Example usage for testing
if __name__ == "__main__":
    # Example patch that would be rejected
    example_patch = """
--- a/.github/workflows/test.yml
+++ b/.github/workflows/test.yml
@@ -1,3 +1,4 @@
+# Modified CI config
 name: Test
--- a/src/main.py
+++ b/src/main.py
@@ -1,5 +1,6 @@
 def main():
-    print("Hello")
+    print("Hello World")
+    return 0
"""
    
    is_safe, message = check_patch_safety(example_patch, verbose=True)
    if not is_safe:
        print("\n" + message)
