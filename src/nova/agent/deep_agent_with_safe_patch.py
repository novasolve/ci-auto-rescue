"""
Example: NovaDeepAgent with SafePatchManager Integration
========================================================

This shows how to modify NovaDeepAgent to use SafePatchManager for
enforced patch review workflow. This is a reference implementation.
"""

from typing import Optional, Any, Dict
from pathlib import Path

from nova.agent.deep_agent import NovaDeepAgent
from nova.agent.safe_patch_manager import create_safe_patch_manager
from nova.agent.unified_tools import create_default_tools
from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger
from nova.tools.git import GitBranchManager

from langchain.tools import Tool


class NovaDeepAgentWithSafePatch(NovaDeepAgent):
    """
    Extended NovaDeepAgent that uses SafePatchManager for patch operations.
    
    This ensures all patches go through critic review before application,
    providing a hard guarantee beyond LLM prompt compliance.
    """
    
    def __init__(
        self,
        state: AgentState,
        telemetry: JSONLLogger,
        git_manager: Optional[GitBranchManager] = None,
        verbose: bool = False,
        safety_config: Optional[Any] = None,
        settings: Optional[Any] = None,
        allow_patch_override: bool = False
    ):
        """
        Initialize with SafePatchManager integration.
        
        Args:
            Same as NovaDeepAgent, plus:
            allow_patch_override: Whether to allow forcing patches despite rejection
        """
        # Initialize parent class first
        super().__init__(
            state=state,
            telemetry=telemetry,
            git_manager=git_manager,
            verbose=verbose,
            safety_config=safety_config,
            settings=settings
        )
        
        # Create SafePatchManager for enforced review workflow
        self.patch_manager = create_safe_patch_manager(
            state=state,
            telemetry=telemetry,
            llm=self.agent.agent.llm,  # Use the same LLM as the agent
            safety_config=safety_config,
            verbose=verbose,
            allow_override=allow_patch_override
        )
        
        # Replace the tools to use SafePatchManager
        self._replace_patch_tools()
    
    def _replace_patch_tools(self):
        """Replace individual patch tools with a combined safe version."""
        # Create a new combined tool
        review_and_apply_tool = Tool(
            name="review_and_apply_patch",
            description=(
                "Review a patch diff and apply it if approved. "
                "This combines critic review and patch application in one safe operation. "
                "Always use this instead of separate critic_review and apply_patch."
            ),
            func=self._review_and_apply_wrapper
        )
        
        # Get current tools
        current_tools = self.agent.tools
        
        # Remove old critic_review and apply_patch tools
        filtered_tools = [
            tool for tool in current_tools 
            if tool.name not in ["critic_review", "apply_patch"]
        ]
        
        # Add the new combined tool
        filtered_tools.append(review_and_apply_tool)
        
        # Update the agent's tools
        self.agent.tools = filtered_tools
        
        # Also update the agent's prompt to mention the new tool
        if hasattr(self.agent, 'agent') and hasattr(self.agent.agent, 'system_message'):
            self.agent.agent.system_message = self.agent.agent.system_message.replace(
                "critic_review, apply_patch",
                "review_and_apply_patch"
            )
    
    def _review_and_apply_wrapper(self, patch_diff: str) -> str:
        """
        Wrapper for SafePatchManager that formats results for the agent.
        
        Args:
            patch_diff: The unified diff to review and apply
            
        Returns:
            String message for the agent about the result
        """
        # Extract failing tests context from state
        failing_tests = ""
        if self.state.failing_tests:
            failing_tests = "\n".join([
                f"- {test['name']}: {test.get('error', 'Unknown error')}"
                for test in self.state.failing_tests[:5]  # Limit to first 5
            ])
        
        # Use SafePatchManager
        result = self.patch_manager.review_and_apply(
            patch_diff=patch_diff,
            failing_tests_context=failing_tests
        )
        
        # Format response for agent
        if result["applied"]:
            return (
                f"SUCCESS: Patch was reviewed and applied.\n"
                f"Review: {result['review_decision']} - {result['review_reason']}\n"
                f"Application: {result['apply_result']}"
            )
        else:
            if result["review_decision"] == "REJECTED":
                return (
                    f"REJECTED: Patch was rejected by critic review.\n"
                    f"Reason: {result['review_reason']}\n"
                    f"Suggestion: Revise the patch to address the concerns and try again."
                )
            else:
                # Approved but failed to apply
                return (
                    f"FAILED: Patch was approved but could not be applied.\n"
                    f"Review: {result['review_reason']}\n"
                    f"Error: {result['apply_result']}\n"
                    f"Suggestion: Check the patch format and file contexts."
                )
    
    def get_patch_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about patch reviews and applications.
        
        Returns:
            Dictionary with review/application statistics
        """
        stats = self.patch_manager.get_stats()
        stats["review_history"] = self.patch_manager.get_review_history()
        return stats


# Example usage
def create_safe_deep_agent(
    state: AgentState,
    telemetry: JSONLLogger,
    git_manager: Optional[GitBranchManager] = None,
    verbose: bool = False,
    safety_config: Optional[Any] = None,
    settings: Optional[Any] = None
) -> NovaDeepAgentWithSafePatch:
    """
    Factory function to create a NovaDeepAgent with SafePatchManager.
    
    This is the recommended way to create agents in production.
    """
    return NovaDeepAgentWithSafePatch(
        state=state,
        telemetry=telemetry,
        git_manager=git_manager,
        verbose=verbose,
        safety_config=safety_config,
        settings=settings,
        allow_patch_override=False  # Never allow override in production
    )
