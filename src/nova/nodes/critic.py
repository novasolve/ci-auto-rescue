"""
Critic Node (Legacy)
====================

Part of the v1.0 multi-node pipeline. Reviews patches for safety and correctness.
Deprecated in favor of the Deep Agent's integrated critic review tool.
"""

from typing import Optional, Tuple
from nova.agent.state import AgentState
from nova.agent.llm_agent import LLMAgent
from nova.telemetry.logger import JSONLLogger


def critic_node(
    state: AgentState,
    patch_diff: str,
    llm_agent: LLMAgent,
    telemetry: Optional[JSONLLogger] = None,
    verbose: bool = False
) -> Tuple[bool, str]:
    """
    Review a patch using the critic LLM to determine if it should be applied.
    
    Args:
        state: Agent state containing the plan
        patch_diff: The patch to review
        llm_agent: Legacy LLM agent for reviewing patches
        telemetry: Optional telemetry logger
        verbose: Enable verbose output
        
    Returns:
        Tuple of (approved, reason)
    """
    if verbose:
        print("[Critic] Reviewing patch...")
    
    if telemetry:
        telemetry.log_event("critic_start", {
            "iteration": state.current_iteration,
            "patch_size": len(patch_diff)
        })
    
    # Perform basic safety checks first
    if len(patch_diff) > 10000:
        reason = "Patch too large (>10000 characters)"
        if verbose:
            print(f"[Critic] Rejected: {reason}")
        if telemetry:
            telemetry.log_event("critic_rejected", {
                "iteration": state.current_iteration,
                "reason": reason
            })
        return False, reason
    
    # Check for test file modifications
    patch_lines = patch_diff.split('\n')
    for line in patch_lines:
        if line.startswith('+++') or line.startswith('---'):
            if 'test' in line.lower() or 'spec' in line.lower():
                reason = "Patch modifies test files"
                if verbose:
                    print(f"[Critic] Rejected: {reason}")
                if telemetry:
                    telemetry.log_event("critic_rejected", {
                        "iteration": state.current_iteration,
                        "reason": reason
                    })
                state.critic_feedback = reason
                return False, reason
    
    # Use LLM to review the patch
    plan = state.plan or "Fix failing tests"
    approved, reason = llm_agent.review_patch(patch_diff, plan)
    
    if approved:
        if verbose:
            print("[Critic] Patch approved")
        if telemetry:
            telemetry.log_event("critic_approved", {
                "iteration": state.current_iteration
            })
        # Clear any previous critic feedback on approval
        state.critic_feedback = None
    else:
        if verbose:
            print(f"[Critic] Patch rejected: {reason}")
        if telemetry:
            telemetry.log_event("critic_rejected", {
                "iteration": state.current_iteration,
                "reason": reason
            })
        # Store feedback for next iteration
        state.critic_feedback = reason
    
    return approved, reason
