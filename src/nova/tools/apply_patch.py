"""
Apply Patch Tool for Nova Deep Agent
=====================================

Class-based tool for applying unified diff patches with safety checks.
"""

from typing import Optional, Type, Any
from pathlib import Path
import subprocess

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from nova.agent.state import AgentState
from nova.tools.git import GitBranchManager
from nova.nodes.apply_patch import apply_patch as apply_patch_func


class ApplyPatchInput(BaseModel):
    """Input schema for ApplyPatchTool."""
    patch_diff: str = Field(
        description="The unified diff patch to apply"
    )


class ApplyPatchTool(BaseTool):
    """
    Tool to apply a unified diff patch to the repository.
    
    Includes safety checks and git integration.
    """
    name: str = "apply_patch"
    description: str = (
        "Apply a unified diff patch to the codebase. "
        "Use this after the patch has been reviewed and approved. "
        "Input should be the patch diff as a string."
    )
    args_schema: Type[BaseModel] = ApplyPatchInput
    
    git_manager: Optional[GitBranchManager] = None
    safety_config: Optional[Any] = None
    verbose: bool = False
    state: Optional[AgentState] = None
    
    def __init__(
        self,
        git_manager: Optional[GitBranchManager] = None,
        safety_config: Optional[Any] = None,
        verbose: bool = False,
        state: Optional[AgentState] = None,
        **kwargs
    ):
        """Initialize with git manager and safety configuration."""
        super().__init__(**kwargs)
        self.git_manager = git_manager
        self.safety_config = safety_config
        self.verbose = verbose
        self.state = state
    
    def _run(self, patch_diff: str) -> str:
        """
        Apply the patch and return status.
        
        Returns:
            Status message indicating success or failure.
        """
        # Clean up patch if it has markdown formatting
        if patch_diff.strip().startswith("```"):
            lines = patch_diff.strip().split("\n")
            # Remove first line (```diff or similar)
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove last line if it's closing ```
            if lines and lines[-1] == "```":
                lines = lines[:-1]
            patch_diff = "\n".join(lines)
        
        # Use Nova's apply_patch function if available
        if self.state:
            try:
                result = apply_patch_func(
                    state=self.state,
                    patch_text=patch_diff,
                    git_manager=self.git_manager,
                    verbose=self.verbose,
                    safety_config=self.safety_config
                )
                
                if result["success"]:
                    # Track applied patch
                    if self.state:
                        self.state.patches_applied.append(patch_diff)
                        self.state.current_step += 1
                    return "SUCCESS: Patch applied successfully."
                else:
                    # Handle various failure reasons
                    if result.get("safety_violation"):
                        return f"FAILED: Safety violation - {result.get('safety_message', 'unknown')}"
                    elif result.get("preflight_failed"):
                        return "FAILED: Patch could not be applied (context mismatch)."
                    else:
                        return f"FAILED: {result.get('error', 'Unknown error')}"
                        
            except Exception as e:
                return f"ERROR: Failed to apply patch: {e}"
        
        # Fallback: Direct git apply
        try:
            # Save patch to temporary file
            patch_file = Path("/tmp/nova_patch.diff")
            patch_file.write_text(patch_diff)
            
            # Try to apply the patch
            result = subprocess.run(
                ["git", "apply", "--check", str(patch_file)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return f"FAILED: Patch validation failed: {result.stderr}"
            
            # Actually apply the patch
            result = subprocess.run(
                ["git", "apply", str(patch_file)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Commit the changes
                subprocess.run(["git", "add", "-A"], check=False)
                subprocess.run(
                    ["git", "commit", "-m", "Apply patch from Nova Deep Agent"],
                    check=False
                )
                return "SUCCESS: Patch applied successfully."
            else:
                return f"FAILED: Could not apply patch: {result.stderr}"
                
        except Exception as e:
            return f"ERROR: {e}"
    
    async def _arun(self, patch_diff: str) -> str:
        """Async version not implemented."""
        raise NotImplementedError("ApplyPatchTool does not support async execution")
