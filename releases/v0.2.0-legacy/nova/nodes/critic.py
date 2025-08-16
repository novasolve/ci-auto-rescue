"""
Critic node for Nova CI-Rescue agent workflow.
"""

from typing import Tuple, Optional, Any
from rich.console import Console

from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger

console = Console()


class CriticNode:
    """Node responsible for reviewing and approving/rejecting patches."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def execute(
        self,
        state: AgentState,
        patch_diff: str,
        llm_agent: Any,
        telemetry: Optional[JSONLLogger] = None
    ) -> Tuple[bool, str]:
        """
        Review a patch and decide whether to approve or reject it.
        
        Args:
            state: Current agent state
            patch_diff: The patch diff to review
            llm_agent: LLM agent instance for reviewing
            telemetry: Optional telemetry logger
            
        Returns:
            Tuple of (approved: bool, reason: str)
        """
        iteration = state.current_iteration
        
        # Log critic start
        if telemetry:
            telemetry.log_event("critic_start", {
                "iteration": iteration,
                "patch_size": len(patch_diff.split('\n'))
            })
        
        if self.verbose:
            console.print(f"[cyan]🔍 Reviewing patch with critic...[/cyan]")
        
        # Use LLM to review patch
        patch_approved, review_reason = llm_agent.review_patch(patch_diff, state.failing_tests)
        
        if self.verbose:
            console.print(f"[dim]Review result: {review_reason}[/dim]")
        
        if not patch_approved:
            console.print(f"[red]❌ Patch rejected: {review_reason}[/red]")
            # Store critic feedback for next iteration
            state.critic_feedback = review_reason
            if telemetry:
                telemetry.log_event("critic_rejected", {
                    "iteration": iteration,
                    "reason": review_reason,
                    "patch_lines": len(patch_diff.split('\n'))
                })
        else:
            console.print("[green]✓ Patch approved by critic[/green]")
            # Clear critic feedback since patch was approved
            state.critic_feedback = None
            if telemetry:
                telemetry.log_event("critic_approved", {
                    "iteration": iteration,
                    "reason": review_reason,
                    "patch_lines": len(patch_diff.split('\n'))
                })
        
        return patch_approved, review_reason


def critic_node(
    state: AgentState,
    patch_diff: str,
    llm_agent: Any,
    telemetry: Optional[JSONLLogger] = None,
    verbose: bool = False
) -> Tuple[bool, str]:
    """
    Convenience function to execute the critic node.
    
    Args:
        state: Current agent state
        patch_diff: Patch to review
        llm_agent: LLM agent instance
        telemetry: Optional telemetry logger
        verbose: Enable verbose output
        
    Returns:
        Tuple of (approved, reason)
    """
    node = CriticNode(verbose=verbose)
    return node.execute(state, patch_diff, llm_agent, telemetry)
