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
from nova.tools.safety_limits import check_patch_safety, SafetyConfig
from nova.telemetry.logger import JSONLLogger

console = Console()


class ApplyPatchNode:
    """Node responsible for applying approved patches and committing them."""
    
    def __init__(self, verbose: bool = False, safety_config: Optional[SafetyConfig] = None):
        self.verbose = verbose
        self.safety_config = safety_config or SafetyConfig()
    
    def execute(
        self, 
        state: AgentState, 
        patch_text: str,
        git_manager: Optional[GitBranchManager] = None,
        skip_safety_check: bool = False,
        logger: Optional[JSONLLogger] = None,
        iteration: int = 0
    ) -> Dict[str, Any]:
        """
        Apply an approved patch to the repository and commit it.
        
        Args:
            state: Current agent state
            patch_text: The unified diff text to apply
            git_manager: Optional GitBranchManager for committing
            skip_safety_check: Skip safety validation (use with caution)
            logger: Optional telemetry logger
            iteration: Current iteration number
            
        Returns:
            Dictionary with results including success status and changed files
        """
        # Increment step counter
        step_number = state.increment_step()
        
        # Log apply start event
        if logger:
            patch_lines = patch_text.split('\n')
            patch_size = len(patch_lines)
            
            # Count changed files from patch
            files_in_patch = set()
            for line in patch_lines:
                if line.startswith('+++') or line.startswith('---'):
                    # Extract file path
                    parts = line.split()
                    if len(parts) >= 2 and not parts[1].startswith('/dev/null'):
                        # Remove b/ or a/ prefix
                        file_path = parts[1]
                        if file_path.startswith('b/') or file_path.startswith('a/'):
                            file_path = file_path[2:]
                        files_in_patch.add(file_path)
            
            logger.log_event("apply_start", {
                "iteration": iteration,
                "step_number": step_number,
                "patch_size": patch_size,
                "files_count": len(files_in_patch),
                "skip_safety_check": skip_safety_check
            })
        
        if self.verbose:
            console.print(f"[cyan]Applying patch (step {step_number})...[/cyan]")
        
        # Perform safety check unless explicitly skipped
        if not skip_safety_check:
            if self.verbose:
                console.print("[dim]Running safety checks...[/dim]")
            
            is_safe, safety_message = check_patch_safety(
                patch_text, 
                config=self.safety_config,
                verbose=self.verbose
            )
            
            if not is_safe:
                console.print("[red]✗ Patch rejected by safety limits[/red]")
                console.print(safety_message)
                
                # Log safety rejection
                if logger:
                    logger.log_event("patch_rejected", {
                        "iteration": iteration,
                        "step_number": step_number,
                        "reason": "safety_violation",
                        "safety_message": safety_message
                    })
                
                result = {
                    "success": False,
                    "step_number": step_number,
                    "changed_files": [],
                    "patch_text": patch_text,
                    "safety_violation": True,
                    "safety_message": safety_message
                }
                return result
            
            if self.verbose:
                console.print("[green]✓ Patch passed safety checks[/green]")
        
        if self.verbose:
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
        
        # Preflight validation: ensure the patch cleanly applies before modifying files
        preflight_error = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
                f.write(patch_text)
                preflight_file = f.name

            preflight = subprocess.run(
                ["git", "apply", "--check", "--whitespace=nowarn", preflight_file],
                cwd=state.repo_path,
                capture_output=True,
                text=True
            )

            if preflight.returncode != 0:
                preflight_error = (preflight.stderr or preflight.stdout or "Unknown error")
        finally:
            try:
                import os
                if 'preflight_file' in locals():
                    os.unlink(preflight_file)
            except Exception:
                pass

        if preflight_error is not None:
            if self.verbose:
                console.print("[red]✗ Patch preflight check failed — will not apply[/red]")
                console.print("[yellow]Git apply --check output:[/yellow]")
                for line in preflight_error.split('\n'):
                    if line.strip():
                        console.print(f"  [dim]• {line.strip()}[/dim]")

            if logger:
                logger.log_event("preflight_failed", {
                    "iteration": iteration,
                    "step_number": step_number,
                    "error_details": preflight_error
                })

            return {
                "success": False,
                "step_number": step_number,
                "changed_files": [],
                "patch_text": patch_text,
                "preflight_failed": True,
                "error": "context_mismatch"
            }

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
                    
                # Clean up temp file
                try:
                    import os
                    os.unlink(patch_file)
                except:
                    pass
            except Exception as e:
                error_details = str(e)
        
        result = {
            "success": success,
            "step_number": step_number,
            "changed_files": [str(f) for f in changed_files],
            "patch_text": patch_text
        }
        
        if success:
            # Track the applied patch in state
            state.patches_applied.append(patch_text)
            
            # Log successful patch application
            if logger:
                logger.log_event("patch_applied", {
                    "iteration": iteration,
                    "step_number": step_number,
                    "changed_files": [str(f) for f in changed_files],
                    "files_count": len(changed_files)
                })
            
            if self.verbose:
                console.print(f"[green]✓ Applied and committed patch (step {step_number})[/green]")
                if changed_files:
                    console.print(f"[dim]Changed files: {', '.join([f.name for f in changed_files])}[/dim]")
        else:
            # Log failed patch application
            if logger:
                logger.log_event("patch_error", {
                    "iteration": iteration,
                    "step_number": step_number,
                    "error_details": error_details if error_details else "Unknown error"
                })
            
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
    verbose: bool = False,
    safety_config: Optional[SafetyConfig] = None,
    skip_safety_check: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to apply a patch using the ApplyPatchNode.
    
    Args:
        state: Current agent state
        patch_text: The unified diff text to apply
        git_manager: Optional GitBranchManager for committing
        verbose: Enable verbose output
        safety_config: Optional safety configuration
        skip_safety_check: Skip safety validation (use with caution)
        
    Returns:
        Dictionary with results including success status and changed files
    """
    node = ApplyPatchNode(verbose=verbose, safety_config=safety_config)
    return node.execute(state, patch_text, git_manager, skip_safety_check=skip_safety_check)
