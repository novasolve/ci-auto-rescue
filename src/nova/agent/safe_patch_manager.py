"""
SafePatchManager - Enforces critic review before patch application
==================================================================

This module provides programmatic enforcement of the critic review workflow,
ensuring that no patch can be applied without passing through review first.
It integrates with the existing CriticReviewTool and ApplyPatchTool.
"""

from typing import Optional, Dict, Any
from pathlib import Path

from nova.agent.unified_tools import CriticReviewTool, ApplyPatchTool
from nova.telemetry.logger import JSONLLogger
from nova.config import SafetyConfig


class SafePatchManager:
    """
    Enforces critic review before applying patches.
    
    Coordinates CriticReviewTool and ApplyPatchTool usage with comprehensive
    logging and optional override support. This provides a hard guarantee that
    patches are reviewed, beyond relying on LLM compliance with prompts.
    """
    
    def __init__(
        self, 
        repo_path: Path,
        llm: Any,
        telemetry: JSONLLogger,
        safety_config: Optional[SafetyConfig] = None,
        verbose: bool = False,
        allow_override: bool = False,
        state: Optional[Any] = None
    ):
        """
        Initialize the SafePatchManager.
        
        Args:
            repo_path: Path to the repository
            llm: Language model for critic review
            telemetry: Logger for audit trail
            safety_config: Safety configuration for patch limits
            verbose: Enable verbose output
            allow_override: Allow applying patches despite rejection (dangerous!)
            state: Agent state for tracking
        """
        # Initialize the CriticReview and ApplyPatch tools
        self.critic_tool = CriticReviewTool(
            verbose=verbose, 
            llm=llm,
            state=state
        )
        self.apply_tool = ApplyPatchTool(
            repo_path=repo_path,
            safety_config=safety_config,
            verbose=verbose,
            logger=telemetry
        )
        self.telemetry = telemetry
        self.allow_override = allow_override
        self.verbose = verbose
        
        # Track review history
        self._review_history: list[Dict[str, Any]] = []

    def review_and_apply(
        self, 
        patch_diff: str, 
        failing_tests_context: str = "",
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Run a critic review on the given patch diff and apply it if approved.
        
        This is the main entry point that enforces the review-before-apply workflow.
        
        Args:
            patch_diff: The unified diff to review and potentially apply
            failing_tests_context: Context about failing tests for the critic
            force: Force application even if rejected (requires allow_override=True)
            
        Returns:
            Dict with:
                - applied: bool - whether the patch was applied
                - review_decision: str - the critic's decision
                - review_reason: str - explanation for the decision
                - apply_result: str - result of patch application (if attempted)
        """
        result = {
            "applied": False,
            "review_decision": None,
            "review_reason": None,
            "apply_result": None
        }
        
        # Step 1: Critic review
        if self.verbose:
            print("🔍 Running critic review on patch...")
            
        decision = self.critic_tool._run(
            patch_diff=patch_diff,
            failing_tests=failing_tests_context
        )
        
        # Parse the decision
        if decision.startswith("APPROVED"):
            result["review_decision"] = "APPROVED"
            result["review_reason"] = decision.split(":", 1)[1].strip() if ":" in decision else "No reason provided"
        else:
            result["review_decision"] = "REJECTED"
            result["review_reason"] = decision.split(":", 1)[1].strip() if ":" in decision else decision
        
        # Log the critic's decision for audit
        review_event = {
            "event": "patch_review",
            "decision": result["review_decision"],
            "reason": result["review_reason"],
            "patch_size": len(patch_diff.splitlines()),
            "patch_excerpt": patch_diff[:500] + "..." if len(patch_diff) > 500 else patch_diff
        }
        self.telemetry.log_event(review_event)
        self._review_history.append(review_event)
        
        # Step 2: Apply if approved (or if override is enabled)
        should_apply = False
        override_used = False
        
        if result["review_decision"] == "APPROVED":
            should_apply = True
            if self.verbose:
                print(f"✅ Patch approved: {result['review_reason']}")
        else:
            if self.verbose:
                print(f"❌ Patch rejected: {result['review_reason']}")
                
            if force and self.allow_override:
                should_apply = True
                override_used = True
                self.telemetry.log_event({
                    "event": "safety_override",
                    "reason": "Applying rejected patch with override flag",
                    "original_rejection": result["review_reason"]
                })
                if self.verbose:
                    print("⚠️  WARNING: Applying patch despite rejection (override enabled)")
            elif force and not self.allow_override:
                self.telemetry.log_event({
                    "event": "override_denied", 
                    "reason": "Override requested but not allowed in configuration"
                })
                if self.verbose:
                    print("🚫 Override requested but not allowed")
        
        if should_apply:
            # Apply the patch
            if self.verbose:
                print("📝 Applying patch...")
                
            apply_result = self.apply_tool._run(patch_diff=patch_diff)
            result["apply_result"] = apply_result
            
            # Check if application was successful
            if apply_result.startswith("SUCCESS"):
                result["applied"] = True
                self.telemetry.log_event({
                    "event": "patch_applied",
                    "message": apply_result,
                    "override_used": override_used
                })
                if self.verbose:
                    print(f"✅ {apply_result}")
            else:
                self.telemetry.log_event({
                    "event": "patch_apply_failed",
                    "message": apply_result,
                    "override_used": override_used
                })
                if self.verbose:
                    print(f"❌ {apply_result}")
        
        return result
    
    def get_review_history(self) -> list[Dict[str, Any]]:
        """
        Get the history of all reviews performed by this manager.
        
        Returns:
            List of review event dictionaries
        """
        return self._review_history.copy()
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about reviews and applications.
        
        Returns:
            Dict with counts of approved, rejected, applied patches
        """
        stats = {
            "total_reviews": len(self._review_history),
            "approved": sum(1 for r in self._review_history if r.get("decision") == "APPROVED"),
            "rejected": sum(1 for r in self._review_history if r.get("decision") == "REJECTED"),
            "applied": sum(1 for r in self._review_history if r.get("event") == "patch_applied")
        }
        return stats


# Integration helper for existing code
def create_safe_patch_manager(
    state: Any,
    telemetry: JSONLLogger,
    llm: Any,
    safety_config: Optional[SafetyConfig] = None,
    verbose: bool = False,
    allow_override: bool = False
) -> SafePatchManager:
    """
    Factory function to create a SafePatchManager with common settings.
    
    This can be used to easily integrate with existing Nova agent code.
    """
    return SafePatchManager(
        repo_path=state.repo_path,
        llm=llm,
        telemetry=telemetry,
        safety_config=safety_config or SafetyConfig(),
        verbose=verbose,
        allow_override=allow_override,
        state=state
    )
