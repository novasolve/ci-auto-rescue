"""
Rollback Management for Nova CI-Rescue
======================================

This module provides rollback capabilities at multiple levels:
- Git commit rollback (revert/reset)
- File-level rollback (restore original content)
- Integration with the Safe Patching system
"""

from pathlib import Path
from typing import List, Tuple, Optional, Dict
import subprocess
import logging
from contextlib import contextmanager

from nova.engine.safe_patching import RollbackManager as SafeRollbackManager
from nova.tools.fs import rollback_on_failure

logger = logging.getLogger("nova.rollback")


class ComprehensiveRollbackManager:
    """
    Manages comprehensive rollback functionality combining:
    - Git-level rollback for committed patches
    - File-level rollback for uncommitted changes
    - Integration with the Safe Patching system
    """
    
    def __init__(self, repo_path: str = "."):
        """Initialize the rollback manager."""
        self.repo_path = Path(repo_path).resolve()
        self.git_rollback = SafeRollbackManager(repo_path=str(self.repo_path))
        self._uncommitted_files: List[Path] = []
    
    def record_patch_commit(self, commit_hash: str):
        """
        Record a patch commit for potential future rollback.
        
        Args:
            commit_hash: The Git commit hash to track
        """
        self.git_rollback.record_patch_commit(commit_hash)
    
    def rollback_last_commit(self, preserve_history: bool = True) -> Tuple[bool, str]:
        """
        Rollback the last committed patch.
        
        Args:
            preserve_history: If True, use git revert; if False, use git reset --hard
            
        Returns:
            Tuple of (success, message)
        """
        return self.git_rollback.rollback_last_patch(preserve_history=preserve_history)
    
    def track_file_changes(self, files: List[Path]):
        """
        Track files that are being modified for potential rollback.
        
        Args:
            files: List of file paths being modified
        """
        self._uncommitted_files.extend(files)
    
    @contextmanager
    def file_rollback_context(self, files: List[Path]):
        """
        Context manager that provides file-level rollback on failure.
        
        Args:
            files: List of file paths to protect
            
        Example:
            with rollback_manager.file_rollback_context([Path("src/main.py")]):
                # Modify files here
                # If exception occurs, files are restored
        """
        # Track files for this operation
        self.track_file_changes(files)
        
        # Use the existing rollback_on_failure context manager
        with rollback_on_failure(files):
            yield
    
    def get_patch_history(self) -> List[str]:
        """
        Get the history of applied patch commits.
        
        Returns:
            List of commit hashes in order of application
        """
        return self.git_rollback._patch_history.copy()
    
    def rollback_multiple_commits(self, count: int, preserve_history: bool = True) -> List[Tuple[bool, str]]:
        """
        Rollback multiple commits in sequence.
        
        Args:
            count: Number of commits to rollback
            preserve_history: If True, use git revert; if False, use git reset
            
        Returns:
            List of (success, message) tuples for each rollback attempt
        """
        results = []
        for _ in range(min(count, len(self.git_rollback._patch_history))):
            result = self.rollback_last_commit(preserve_history=preserve_history)
            results.append(result)
            if not result[0]:  # Stop on first failure
                break
        return results
    
    def get_current_branch(self) -> str:
        """
        Get the current Git branch name.
        
        Returns:
            Branch name or "HEAD" if detached
        """
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            branch = result.stdout.strip()
            return branch if branch else "HEAD"
        except Exception as e:
            logger.error(f"Failed to get current branch: {e}")
            return "unknown"
    
    def create_backup_branch(self, branch_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Create a backup branch at the current HEAD before rollback operations.
        
        Args:
            branch_name: Optional branch name; auto-generates if not provided
            
        Returns:
            Tuple of (success, branch_name_or_error)
        """
        if not branch_name:
            import time
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            branch_name = f"nova_backup_{timestamp}"
        
        try:
            result = subprocess.run(
                ["git", "branch", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info(f"Created backup branch: {branch_name}")
                return True, branch_name
            else:
                error = result.stderr.strip() or "Unknown error"
                logger.error(f"Failed to create backup branch: {error}")
                return False, error
        except Exception as e:
            logger.exception("Exception creating backup branch")
            return False, str(e)
    
    def get_rollback_preview(self) -> List[Dict[str, str]]:
        """
        Get a preview of what would be rolled back.
        
        Returns:
            List of dicts with commit info (hash, message, files)
        """
        preview = []
        for commit_hash in reversed(self.git_rollback._patch_history):
            try:
                # Get commit message
                msg_result = subprocess.run(
                    ["git", "log", "-1", "--pretty=%s", commit_hash],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )
                message = msg_result.stdout.strip() if msg_result.returncode == 0 else "Unknown"
                
                # Get changed files
                files_result = subprocess.run(
                    ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )
                files = files_result.stdout.strip().split('\n') if files_result.returncode == 0 else []
                
                preview.append({
                    "hash": commit_hash,
                    "message": message,
                    "files": files
                })
            except Exception as e:
                logger.error(f"Error getting preview for {commit_hash}: {e}")
                preview.append({
                    "hash": commit_hash,
                    "message": "Error retrieving info",
                    "files": []
                })
        
        return preview


# Global instance for convenience
_rollback_manager: Optional[ComprehensiveRollbackManager] = None


def get_rollback_manager(repo_path: str = ".") -> ComprehensiveRollbackManager:
    """
    Get or create a global rollback manager instance.
    
    Args:
        repo_path: Repository path
        
    Returns:
        ComprehensiveRollbackManager instance
    """
    global _rollback_manager
    if _rollback_manager is None or str(_rollback_manager.repo_path) != str(Path(repo_path).resolve()):
        _rollback_manager = ComprehensiveRollbackManager(repo_path)
    return _rollback_manager
