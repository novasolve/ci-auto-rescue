"""
Apply patch node for Nova CI-Rescue agent workflow.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console

from nova.agent.state import AgentState
from nova.tools.fs import apply_and_commit_patch
from nova.tools.git import GitBranchManager

console = Console()


class ApplyPatchNode:
    """Node responsible for applying approved patches and committing them."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def execute(
        self, 
        state: AgentState, 
        patch_text: str,
        git_manager: Optional[GitBranchManager] = None
    ) -> Dict[str, Any]:
        """
        Apply an approved patch to the repository and commit it.
        
        Args:
            state: Current agent state
            patch_text: The unified diff text to apply
            git_manager: Optional GitBranchManager for committing
            
        Returns:
            Dictionary with results including success status and changed files
        """
        # Increment step counter
        step_number = state.increment_step()
        
        if self.verbose:
            console.print(f"[cyan]Applying patch (step {step_number})...[/cyan]")
        
        # Apply the patch and commit it
        success, changed_files = apply_and_commit_patch(
            repo_root=state.repo_path,
            diff_text=patch_text,
            step_number=step_number,
            git_manager=git_manager,
            verbose=self.verbose
        )
        
        result = {
            "success": success,
            "step_number": step_number,
            "changed_files": [str(f) for f in changed_files],
            "patch_text": patch_text
        }
        
        if success:
            # Track the applied patch in state
            state.patches_applied.append(patch_text)
            
            if self.verbose:
                console.print(f"[green]✓ Applied and committed patch (step {step_number})[/green]")
                if changed_files:
                    console.print(f"[dim]Changed files: {', '.join([f.name for f in changed_files])}[/dim]")
        else:
            if self.verbose:
                console.print(f"[red]✗ Failed to apply patch (step {step_number})[/red]")
        
        return result


def apply_patch(
    state: AgentState,
    patch_text: str,
    git_manager: Optional[GitBranchManager] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to apply a patch using the ApplyPatchNode.
    
    Args:
        state: Current agent state
        patch_text: The unified diff text to apply
        git_manager: Optional GitBranchManager for committing
        verbose: Enable verbose output
        
    Returns:
        Dictionary with results including success status and changed files
    """
    node = ApplyPatchNode(verbose=verbose)
    return node.execute(state, patch_text, git_manager)
