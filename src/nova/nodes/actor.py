"""
Actor Node (Legacy)
===================

Part of the v1.0 multi-node pipeline. Generates patches to fix failing tests.
Deprecated in favor of the Deep Agent's integrated patch generation.
"""

from typing import Optional
from nova.agent.state import AgentState
from nova.agent.llm_agent import LLMAgent
from nova.telemetry.logger import JSONLLogger


def actor_node(
    state: AgentState,
    llm_agent: LLMAgent,
    telemetry: Optional[JSONLLogger] = None,
    critic_feedback: Optional[str] = None,
    verbose: bool = False
) -> Optional[str]:
    """
    Generate a patch to fix failing tests based on the plan.
    
    Args:
        state: Agent state containing the plan and test failures
        llm_agent: Legacy LLM agent for generating patches
        telemetry: Optional telemetry logger
        critic_feedback: Optional feedback from previous critic rejection
        verbose: Enable verbose output
        
    Returns:
        Generated patch as a string, or None if generation fails
    """
    if verbose:
        print("[Actor] Generating patch...")
    
    if telemetry:
        telemetry.log_event("actor_start", {
            "iteration": state.current_iteration,
            "has_feedback": critic_feedback is not None
        })
    
    # Get plan from state
    plan = state.plan
    if not plan:
        if verbose:
            print("[Actor] No plan available, cannot generate patch")
        return None
    
    # Format failing tests
    failing_tests_summary = []
    for test_name in state.failing_tests[:5]:
        failing_tests_summary.append(f"- {test_name}")
    failures_text = "\n".join(failing_tests_summary)
    
    # Generate the patch
    try:
        patch = llm_agent.generate_patch(
            plan=plan,
            failing_tests=failures_text,
            critic_feedback=critic_feedback or state.critic_feedback
        )
        
        if verbose:
            print(f"[Actor] Generated patch ({len(patch)} chars)")
        
        if telemetry:
            telemetry.log_event("actor_complete", {
                "iteration": state.current_iteration,
                "patch_length": len(patch)
            })
        
        return patch
        
    except Exception as e:
        if verbose:
            print(f"[Actor] Error generating patch: {e}")
        
        if telemetry:
            telemetry.log_event("actor_error", {
                "iteration": state.current_iteration,
                "error": str(e)
            })
        
        return None
