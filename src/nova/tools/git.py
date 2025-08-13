"""
Git operations for Nova CI-Rescue.
Handles branch management and repository state.
"""

import subprocess
import signal
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
from contextlib import contextmanager
from rich.console import Console

console = Console()


class GitBranchManager:
    """Manages Git branch creation and cleanup for Nova fix operations."""
    
    def __init__(self, repo_path: Path, verbose: bool = False):
        self.repo_path = repo_path
        self.verbose = verbose
        self.original_head: Optional[str] = None
        self.branch_name: Optional[str] = None
        self._original_sigint_handler = None
        
    def _run_git_command(self, *args) -> Tuple[bool, str]:
        """Run a git command and return success status and output."""
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
        except Exception as e:
            return False, str(e)
    
    def _get_current_head(self) -> Optional[str]:
        """Get the current HEAD commit hash."""
        success, output = self._run_git_command("rev-parse", "HEAD")
        return output if success else None
    
    def _get_current_branch(self) -> Optional[str]:
        """Get the current branch name."""
        success, output = self._run_git_command("rev-parse", "--abbrev-ref", "HEAD")
        return output if success else None
    
    def _check_clean_working_tree(self) -> bool:
        """Check if the working tree is clean."""
        success, output = self._run_git_command("status", "--porcelain")
        return success and not output
    
    def create_fix_branch(self) -> str:
        """Create a new nova-fix/<timestamp> branch and switch to it."""
        # Store original HEAD
        self.original_head = self._get_current_head()
        if not self.original_head:
            raise RuntimeError("Failed to get current HEAD commit")
        
        # Generate branch name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.branch_name = f"nova-fix/{timestamp}"
        
        # Create and checkout new branch
        success, output = self._run_git_command("checkout", "-b", self.branch_name)
        if not success:
            raise RuntimeError(f"Failed to create branch {self.branch_name}: {output}")
        
        if self.verbose:
            console.print(f"[dim]Created branch: {self.branch_name}[/dim]")
        
        return self.branch_name
    
    def cleanup(self, success: bool = False):
        """Clean up the repository state."""
        if not self.original_head:
            return  # Nothing to clean up
        
        if success:
            # On success, stay on the branch and print the branch name
            console.print(f"\n[green]✅ Success! Changes saved to branch: {self.branch_name}[/green]")
        else:
            # On failure or interrupt, hard reset to original HEAD
            console.print("\n[yellow]⚠️  Cleaning up... resetting to original state[/yellow]")
            
            # First, try to checkout the original branch or HEAD
            original_branch = self._get_current_branch()
            if original_branch and original_branch.startswith("nova-fix/"):
                # We're on a nova-fix branch, need to switch away
                success, _ = self._run_git_command("checkout", "-f", self.original_head)
                if not success:
                    console.print("[red]Warning: Failed to checkout original HEAD[/red]")
            
            # Hard reset to original HEAD
            success, output = self._run_git_command("reset", "--hard", self.original_head)
            if success:
                console.print("[dim]Repository reset to original state[/dim]")
                
                # Delete the created branch if it exists
                if self.branch_name:
                    success, _ = self._run_git_command("branch", "-D", self.branch_name)
                    if success and self.verbose:
                        console.print(f"[dim]Deleted branch: {self.branch_name}[/dim]")
            else:
                console.print(f"[red]Failed to reset repository: {output}[/red]")
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signal (Ctrl+C)."""
        console.print("\n[yellow]Interrupted! Cleaning up...[/yellow]")
        self.cleanup(success=False)
        sys.exit(130)  # Standard exit code for SIGINT
    
    def setup_signal_handler(self):
        """Set up signal handler for graceful cleanup on interrupt."""
        self._original_sigint_handler = signal.signal(signal.SIGINT, self._signal_handler)
    
    def restore_signal_handler(self):
        """Restore the original signal handler."""
        if self._original_sigint_handler:
            signal.signal(signal.SIGINT, self._original_sigint_handler)


@contextmanager
def managed_fix_branch(repo_path: Path, verbose: bool = False):
    """
    Context manager for Git branch operations during nova fix.
    
    Creates a nova-fix/<timestamp> branch on entry, and handles cleanup on exit.
    On success, leaves the branch. On failure or interrupt, hard resets to original HEAD.
    """
    manager = GitBranchManager(repo_path, verbose)
    
    try:
        # Check for clean working tree before starting
        if not manager._check_clean_working_tree():
            console.print("[yellow]⚠️  Warning: Working tree is not clean. Uncommitted changes may be lost.[/yellow]")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                console.print("[dim]Aborted.[/dim]")
                sys.exit(1)
        
        # Set up signal handler for Ctrl+C
        manager.setup_signal_handler()
        
        # Create the fix branch
        branch_name = manager.create_fix_branch()
        
        # Yield control back to the caller with the branch name
        yield branch_name
        
        # If we get here, it was successful
        manager.cleanup(success=True)
        
    except KeyboardInterrupt:
        # Handle Ctrl+C during execution
        manager.cleanup(success=False)
        sys.exit(130)
        
    except Exception as e:
        # Handle any other exceptions
        manager.cleanup(success=False)
        raise
        
    finally:
        # Restore original signal handler
        manager.restore_signal_handler()
