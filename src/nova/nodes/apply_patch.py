"""
Apply patch node for Nova CI-Rescue agent workflow.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console
import tempfile
import subprocess

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
            # Show first few lines of patch for debugging
            patch_lines = patch_text.split('\n')[:10]
            console.print("[dim]Patch preview:[/dim]")
            for line in patch_lines:
                if line.startswith('+++') or line.startswith('---'):
                    console.print(f"[dim]  {line}[/dim]")
                elif line.startswith('+'):
                    console.print(f"[green]  {line}[/green]")
                elif line.startswith('-'):
                    console.print(f"[red]  {line}[/red]")
                else:
                    console.print(f"[dim]  {line}[/dim]")
        
        # Apply the patch and commit it
        success, changed_files = apply_and_commit_patch(
            repo_root=state.repo_path,
            diff_text=patch_text,
            step_number=step_number,
            git_manager=git_manager,
            verbose=self.verbose
        )
        
        # If it failed, try to get more specific error information
        error_details = None
        if not success and self.verbose:
            # Try a git apply --check to get specific error
            patch_file = None
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
                    f.write(patch_text)
                    patch_file = f.name
                
                result = subprocess.run(
                    ["git", "apply", "--check", patch_file],
                    cwd=state.repo_path,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    error_details = result.stderr or result.stdout
            except Exception as e:
                error_details = str(e)
            finally:
                # Clean up temp file
                if patch_file:
                    try:
                        import os
                        os.unlink(patch_file)
                    except OSError as e:
                        if self.verbose:
                            console.print(f"[dim yellow]Warning: Failed to remove temp patch file: {e}[/dim yellow]")
        
        result = {
            "success": success,
            "step_number": step_number,
            "changed_files": [str(f) for f in changed_files],
            "patch_text": patch_text
        }
        
        if success:
            # Track the applied patch in state
            state.patches_applied.append(patch_text)
            
            # Increment modifications counter for loop prevention
            if hasattr(state, 'increment_modifications'):
                state.increment_modifications()
            
            if self.verbose:
                console.print(f"[green]✓ Applied and committed patch (step {step_number})[/green]")
                if changed_files:
                    console.print(f"[dim]Changed files: {', '.join([f.name for f in changed_files])}[/dim]")
        else:
            if self.verbose:
                console.print(f"[red]✗ Failed to apply patch (step {step_number})[/red]")
                
                if error_details:
                    console.print("[red]Git apply error details:[/red]")
                    # Parse and format git error messages
                    for line in error_details.split('\n'):
                        if line.strip():
                            if 'error:' in line:
                                console.print(f"  [red]• {line.strip()}[/red]")
                            elif 'warning:' in line:
                                console.print(f"  [yellow]• {line.strip()}[/yellow]")
                            else:
                                console.print(f"  [dim]• {line.strip()}[/dim]")
                    
                    # Provide specific hints based on error type
                    if "hunk" in error_details.lower():
                        console.print("\n[yellow]💡 Hint:[/yellow] The patch context doesn't match the current file content.")
                        console.print("   This often means the file has changed since the patch was created or the patch is out of date.")
                    elif "does not exist" in error_details.lower() or "not found" in error_details.lower():
                        console.print("\n[yellow]💡 Hint:[/yellow] A file in the patch could not be found.")
                        console.print("   Check if the file path is correct or if the file was moved or deleted.")
                    elif "already exists" in error_details.lower():
                        console.print("\n[yellow]💡 Hint:[/yellow] The patch is trying to create a file that already exists.")
                    elif "corrupt patch" in error_details.lower():
                        console.print("\n[yellow]💡 Hint:[/yellow] The patch format is corrupted or truncated.")
                        console.print("   The LLM may have generated an incomplete patch.")
                else:
                    console.print("[yellow]Possible reasons:[/yellow]")
                    console.print("  • File content doesn't match the patch context (patch is outdated)")
                    console.print("  • The failing tests might have already been fixed by a prior step")
                    console.print("  • The patch format might be invalid or corrupted")
                    console.print("  • File paths in the patch could be incorrect")
            else:
                console.print(f"[red]✗ Failed to apply patch (step {step_number})[/red]")
                console.print("[dim]Run with --verbose for detailed error information[/dim]")
        
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
