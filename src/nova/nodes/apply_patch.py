"""
Apply Patch Node (Legacy)
=========================

Part of the v1.0 multi-node pipeline. Applies patches to the repository.
Deprecated in favor of the Deep Agent's integrated patch application tool.
"""

import tempfile
import subprocess
from typing import Optional, Dict, Any
from pathlib import Path

from nova.agent.state import AgentState
from nova.tools.git import GitBranchManager
from nova.tools.safety_limits import SafetyLimits


def apply_patch(
    state: AgentState,
    patch_text: str,
    git_manager: Optional[GitBranchManager] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Apply a patch to the repository with safety checks.
    
    Args:
        state: Agent state to track applied patches
        patch_text: The patch text in unified diff format
        git_manager: Optional Git branch manager for committing changes
        verbose: Enable verbose output
        
    Returns:
        Dictionary with keys:
        - success: bool indicating if patch was applied
        - safety_violation: bool indicating if safety check failed
        - safety_message: Optional message about safety violation
        - error_message: Optional error message if application failed
    """
    if verbose:
        print("[ApplyPatch] Checking patch safety...")
    
    # Safety check using SafetyLimits
    try:
        safety = SafetyLimits()
        is_safe, safety_message = safety.check_patch_safety(patch_text)
        
        if not is_safe:
            if verbose:
                print(f"[ApplyPatch] Safety violation: {safety_message}")
            return {
                "success": False,
                "safety_violation": True,
                "safety_message": safety_message
            }
    except Exception as e:
        if verbose:
            print(f"[ApplyPatch] Error during safety check: {e}")
        # Continue anyway if safety check fails
    
    # Write patch to temporary file
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
            f.write(patch_text)
            patch_file = f.name
        
        if verbose:
            print(f"[ApplyPatch] Applying patch from {patch_file}")
        
        # Apply the patch using git apply
        result = subprocess.run(
            ['git', 'apply', '--3way', patch_file],
            cwd=state.repo_path,
            capture_output=True,
            text=True
        )
        
        # Clean up temp file
        import os
        os.unlink(patch_file)
        
        if result.returncode != 0:
            if verbose:
                print(f"[ApplyPatch] Git apply failed: {result.stderr}")
            
            # Try without 3-way merge
            with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
                f.write(patch_text)
                patch_file = f.name
            
            result = subprocess.run(
                ['git', 'apply', patch_file],
                cwd=state.repo_path,
                capture_output=True,
                text=True
            )
            
            os.unlink(patch_file)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "safety_violation": False,
                    "error_message": result.stderr or "Failed to apply patch"
                }
        
        # Patch applied successfully
        if verbose:
            print("[ApplyPatch] Patch applied successfully")
        
        # Track the applied patch in state
        state.patches_applied.append(patch_text)
        state.current_iteration += 1
        
        # Commit if git_manager is available
        if git_manager:
            try:
                commit_message = f"Apply patch iteration {state.current_iteration}"
                git_manager.commit_changes(commit_message)
                if verbose:
                    print(f"[ApplyPatch] Committed changes: {commit_message}")
            except Exception as e:
                if verbose:
                    print(f"[ApplyPatch] Warning: Could not commit: {e}")
        
        return {
            "success": True,
            "safety_violation": False
        }
        
    except Exception as e:
        if verbose:
            print(f"[ApplyPatch] Error: {e}")
        return {
            "success": False,
            "safety_violation": False,
            "error_message": str(e)
        }
