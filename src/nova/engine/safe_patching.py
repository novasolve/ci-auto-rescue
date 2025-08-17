"""
Comprehensive Safe Patching System for Nova CI-Rescue
=====================================================

This module provides a multi-layer safety system for patch application:
- PatchSafetyGuard: Enforces safety policies on patches before application
- ApplyPatchTool: Applies unified diff patches with Git integration
- CriticReviewTool: Two-stage review (safety checks + LLM semantic review)
- RollbackManager: Manages rollback of applied patches

Following Nova CI-Rescue design requirements for minimal, safe changes.
"""

import subprocess
import logging
import tempfile
import re
from pathlib import Path
from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import List, Set, Tuple, Optional, Dict
from contextlib import contextmanager

logger = logging.getLogger("safe_patching")


@dataclass
class PatchSafetyConfig:
    """
    Configuration for PatchSafetyGuard limits and rules.
    """
    max_lines_changed: int = 500       # Max total added + removed lines allowed
    max_files_modified: int = 10       # Max number of files that can be modified
    # List of path patterns (globs or substrings) that are forbidden to edit
    denied_paths: List[str] = field(default_factory=lambda: [
        # Test files and directories
        "test/", "tests/", 
        # CI/CD and config files
        ".github/", ".gitlab-ci", ".travis.yml", ".circleci/", "Jenkinsfile", 
        "azure-pipelines.yml", "bitbucket-pipelines.yml", ".buildkite/",
        # Build and package config files
        "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt",
        "Dockerfile", "docker-compose", "package.json", "poetry.lock", "Pipfile",
    ])
    # Regex patterns for dangerous code usage in added lines
    dangerous_code_patterns: List[str] = field(default_factory=lambda: [
        r"exec\(", r"eval\(", r"__import__", r"os\.system", r"subprocess\.call\(", r"rm\s+-rf"
    ])


class ApplyPatchTool:
    """
    Tool to apply a unified diff patch to a git repository.
    It validates the patch with 'git apply --check', applies it, and commits the changes.
    """
    def __init__(self, repo_path: str = "."):
        """
        Initialize the patch applier. Optionally specify the repository path (default is current directory).
        """
        self.repo_path = repo_path
    
    def apply_patch(self, patch_diff: str) -> tuple[bool, str]:
        """
        Apply the given unified diff patch to the repository.
        
        Returns:
            (success, message) where success is True if applied and committed, False otherwise.
            The message provides information on success or error details.
        """
        try:
            # Write the patch diff to a temporary file
            with tempfile.NamedTemporaryFile("w+", suffix=".diff", delete=False) as tmp:
                tmp.write(patch_diff)
                tmp.flush()
                patch_file_path = tmp.name

            # Validate patch using git apply --check (dry-run)
            cmd_check = ["git", "apply", "--check", patch_file_path]
            result = subprocess.run(cmd_check, cwd=self.repo_path, capture_output=True, text=True)
            if result.returncode != 0:
                # Validation failed – return error message from Git
                logger.error("ApplyPatchTool: Patch validation failed: %s", result.stderr.strip())
                return False, f"Patch validation failed: {result.stderr.strip()}"

            # Apply the patch (actual changes to working directory)
            cmd_apply = ["git", "apply", patch_file_path]
            result = subprocess.run(cmd_apply, cwd=self.repo_path, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("ApplyPatchTool: git apply failed: %s", result.stderr.strip())
                return False, f"Failed to apply patch: {result.stderr.strip()}"

            # Stage all changes and commit them
            subprocess.run(["git", "add", "-A"], cwd=self.repo_path, check=False)
            commit_message = "Apply patch via SafePatchTool"
            commit_proc = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.repo_path, capture_output=True, text=True
            )
            if commit_proc.returncode != 0:
                # Commit might fail if there's nothing to commit (e.g., patch was empty or already applied)
                logger.error("ApplyPatchTool: git commit failed: %s", commit_proc.stderr.strip())
                return False, f"Patch applied but commit failed: {commit_proc.stderr.strip()}"

            # Patch successfully applied and committed
            # Get the new commit hash (short form) for reference
            rev_parse = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=self.repo_path, capture_output=True, text=True
            )
            commit_hash = rev_parse.stdout.strip() if rev_parse.returncode == 0 else ""
            logger.info("ApplyPatchTool: Patch applied and committed (hash %s).", commit_hash)
            return True, f"Patch applied and committed (commit {commit_hash})"
        except Exception as e:
            logger.exception("ApplyPatchTool: Exception while applying patch")
            return False, f"Error applying patch: {e}"


class PatchSafetyGuard:
    """
    Enforces safety rules on patches before they are applied.
    Checks for patch size limits, forbidden file paths, and dangerous code patterns.
    """
    def __init__(self, config: Optional[PatchSafetyConfig] = None, verbose: bool = False):
        self.config = config or PatchSafetyConfig()
        self.verbose = verbose

    def validate_patch(self, patch_text: str) -> Tuple[bool, List[str]]:
        """
        Validate a unified diff patch against safety rules.
        Returns:
            (is_safe, violations) where violations is a list of descriptions for any rule violations.
        """
        violations: List[str] = []
        if not patch_text or patch_text.strip() == "":
            violations.append("Patch is empty.")
            return False, violations

        lines = patch_text.splitlines()
        files_modified: Set[str] = set()
        files_added: Set[str] = set()
        files_deleted: Set[str] = set()
        total_added = 0
        total_removed = 0
        current_old_file: Optional[str] = None

        # Parse patch headers and hunks
        for line in lines:
            if line.startswith('--- '):
                # Original file path
                path = line.split(maxsplit=1)[1].strip()
                current_old_file = '/dev/null' if path == '/dev/null' else (path[2:] if path.startswith("a/") else path)
            elif line.startswith('+++ '):
                # New file path
                path = line.split(maxsplit=1)[1].strip()
                if path == '/dev/null':
                    # File was deleted
                    if current_old_file and current_old_file != '/dev/null':
                        files_deleted.add(current_old_file)
                else:
                    new_file = path[2:] if path.startswith("b/") else path
                    if current_old_file == '/dev/null':
                        files_added.add(new_file)
                    else:
                        files_modified.add(new_file)
                    current_old_file = new_file
            elif line.startswith('+') and not line.startswith('+++'):
                # Added line
                total_added += 1
                # Check for dangerous code in added lines
                for pattern in self.config.dangerous_code_patterns:
                    if re.search(pattern, line, flags=re.IGNORECASE):
                        # Map regex pattern to a friendly description for the message
                        if "exec" in pattern:
                            desc = "exec("
                        elif "eval" in pattern:
                            desc = "eval("
                        elif "os\\.system" in pattern:
                            desc = "os.system"
                        elif "subprocess\\.call" in pattern:
                            desc = "subprocess.call("
                        elif "rm\\s+-rf" in pattern:
                            desc = "rm -rf"
                        else:
                            desc = pattern
                        violations.append(f"Contains dangerous code pattern: {desc}")
            elif line.startswith('-') and not line.startswith('---'):
                # Removed line
                total_removed += 1

        total_lines_changed = total_added + total_removed
        all_files = files_modified | files_added | files_deleted

        # Enforce limits on lines and files changed
        if total_lines_changed > self.config.max_lines_changed:
            violations.append(f"Exceeds maximum lines changed: {total_lines_changed} > {self.config.max_lines_changed}")
        if len(all_files) > self.config.max_files_modified:
            violations.append(f"Exceeds maximum files modified: {len(all_files)} > {self.config.max_files_modified}")

        # Check for forbidden file path modifications
        denied_hits: List[str] = []
        for file_path in all_files:
            path_str = Path(file_path).as_posix()
            for pattern in self.config.denied_paths:
                if ('*' in pattern or '?' in pattern) and fnmatch(path_str, pattern):
                    denied_hits.append(file_path); break
                if pattern in path_str:
                    denied_hits.append(file_path); break
        if denied_hits:
            sample = ', '.join(sorted(denied_hits)[:5])
            if len(denied_hits) > 5:
                sample += f", ... (+{len(denied_hits) - 5} more)"
            violations.append(f"Attempts to modify restricted files: {sample}")

        is_safe = (len(violations) == 0)
        if self.verbose:
            if is_safe:
                logger.info("PatchSafetyGuard: Patch passed all safety checks.")
            else:
                logger.warning("PatchSafetyGuard: Violations found - %s", "; ".join(violations))
        return is_safe, violations


class CriticReviewTool:
    """
    Simulated critic review tool that performs a two-step review on a patch:
    - Safety guard validation
    - LLM-based semantic review (mocked in this implementation).
    """
    def __init__(self, safety_guard: Optional[PatchSafetyGuard] = None, verbose: bool = False):
        self.safety_guard = safety_guard or PatchSafetyGuard()
        self.verbose = verbose

    def review_patch(self, patch_diff: str, context: Optional[str] = None) -> Tuple[bool, str]:
        """
        Review the patch diff (with optional context) and decide whether to approve or reject it.
        
        Returns:
            (approved, rationale): approved is True if the patch is accepted, False if rejected.
            rationale is a string explaining the decision.
        """
        # Stage 1: Apply safety checks
        is_safe, violations = self.safety_guard.validate_patch(patch_diff)
        if not is_safe:
            # If safety checks failed, reject with the combined reasons
            rationale = "Safety violations: " + "; ".join(violations)
            if self.verbose:
                logger.info("CriticReview: Patch rejected by safety guard: %s", rationale)
            return False, rationale

        if self.verbose:
            logger.info("CriticReview: Patch passed safety guard, proceeding to LLM review.")
        # Stage 2: Simulate LLM semantic review
        # (In a real scenario, this is where we'd call an LLM API like OpenAI to get an approval decision.)
        approved = True
        reason = "Patch looks good and addresses the issues (simulated review)."
        if context:
            reason += " Context was taken into account."
        if self.verbose:
            logger.info("CriticReview: LLM simulated decision -> %s: %s",
                        "APPROVED" if approved else "REJECTED", reason)
        return approved, reason


class RollbackManager:
    """
    Manages rollback of applied patches. Can undo the last patch commit, either by a git revert or a hard reset.
    """
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self._patch_history: List[str] = []  # history of patch commit hashes

    def record_patch_commit(self, commit_hash: str):
        """
        Record the hash of a patch commit (to enable future rollback).
        """
        self._patch_history.append(commit_hash)
        if commit_hash:
            logger.info("RollbackManager: Recorded patch commit %s for history.", commit_hash)

    def rollback_last_patch(self, preserve_history: bool = False) -> Tuple[bool, str]:
        """
        Revert the last applied patch.
        
        If preserve_history=True, perform 'git revert' on the last patch commit (creates a new commit that undoes it).
        If preserve_history=False, perform 'git reset --hard HEAD~1' to remove the commit entirely.
        
        Returns:
            (success, message) indicating whether the rollback succeeded and an explanatory message.
        """
        if not self._patch_history:
            logger.warning("RollbackManager: No patch history to rollback.")
            return False, "No patch to rollback."

        last_commit = self._patch_history.pop()  # get the last patch commit hash
        try:
            if preserve_history:
                # Use git revert to create a new commit that undoes last_commit
                result = subprocess.run(
                    ["git", "revert", "--no-edit", last_commit],
                    cwd=self.repo_path, capture_output=True, text=True
                )
                if result.returncode != 0:
                    logger.error("RollbackManager: git revert failed: %s", result.stderr.strip())
                    return False, f"Failed to revert commit {last_commit}: {result.stderr.strip()}"
                else:
                    logger.info("RollbackManager: Reverted patch commit %s with new commit.", last_commit)
                    return True, f"Patch commit {last_commit} reverted successfully."
            else:
                # Use git reset to hard-remove the last commit (HEAD~1)
                result = subprocess.run(
                    ["git", "reset", "--hard", "HEAD~1"],
                    cwd=self.repo_path, capture_output=True, text=True
                )
                if result.returncode != 0:
                    logger.error("RollbackManager: git reset failed: %s", result.stderr.strip())
                    return False, f"Failed to undo commit {last_commit}: {result.stderr.strip()}"
                else:
                    logger.info("RollbackManager: Hard reset HEAD to remove commit %s.", last_commit)
                    return True, f"Patch commit {last_commit} has been undone (hard reset)."
        except Exception as e:
            logger.exception("RollbackManager: Exception during rollback")
            return False, f"Error rolling back patch: {e}"


def main_cli(patch_text: str, failing_tests_context: Optional[str] = None):
    """
    Example CLI integration for the Safe Patching system.
    """
    # Initialize tools
    safety_guard = PatchSafetyGuard()
    critic = CriticReviewTool(safety_guard=safety_guard, verbose=True)
    applier = ApplyPatchTool()
    rollback = RollbackManager()

    # Step 1-3: Safety + Critic review
    approved, rationale = critic.review_patch(patch_text, context=failing_tests_context)
    if not approved:
        print(f"Patch REJECTED: {rationale}")
        return

    print("Patch approved by critic. Applying patch...")
    # Step 4: Apply patch
    success, message = applier.apply_patch(patch_text)
    if not success:
        print(f"ERROR: Failed to apply patch - {message}")
        # (Optional) If patch partially applied, one could call rollback here.
        return

    print(message)  # Success message from ApplyPatchTool
    # Step 5: Record the commit for potential rollback
    # Extract commit hash from success message, if present
    commit_id = ""
    if "commit" in message:
        # message format: "Patch applied and committed (commit <hash>)"
        commit_id = message.split()[-1].strip(")")
    rollback.record_patch_commit(commit_id)

    # (Step 6: Optionally demonstrate rollback)
    # e.g., to undo the patch if needed:
    # rollback.rollback_last_patch(preserve_history=True)
