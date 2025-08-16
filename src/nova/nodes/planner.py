"""
Planner Node (Legacy)
=====================

Part of the v1.0 multi-node pipeline. Generates plans to fix failing tests.
Deprecated in favor of the Deep Agent's integrated planning.
"""

from typing import Optional
from nova.agent.state import AgentState
from nova.agent.llm_agent import LLMAgent
from nova.telemetry.logger import JSONLLogger


def planner_node(
    state: AgentState,
    llm_agent: LLMAgent,
    telemetry: Optional[JSONLLogger] = None,
    verbose: bool = False
) -> None:
    """
    Generate a plan to fix failing tests and store it in the agent state.
    
    Args:
        state: Agent state containing test failures
        llm_agent: Legacy LLM agent for generating plans
        telemetry: Optional telemetry logger
        verbose: Enable verbose output
    """
    if verbose:
        print("[Planner] Generating fix plan...")
    
    if telemetry:
        telemetry.log_event("planner_start", {
            "iteration": state.current_iteration,
            "failures": state.total_failures
        })
    
    # Format failing tests for the planner
    failing_tests_summary = []
    for test_name in state.failing_tests[:5]:  # Limit to first 5
        failing_tests_summary.append(f"- {test_name}")
    
    failures_text = "\n".join(failing_tests_summary)
    
    # Get error details from state (simplified)
    error_details = "Test failures with assertion errors and type mismatches"
    
    # Generate the plan
    plan = llm_agent.generate_plan(failures_text, error_details)
    
    # Store plan in state
    state.plan = plan
    
    if verbose:
        print(f"[Planner] Generated plan: {plan[:200]}...")
    
    if telemetry:
        telemetry.log_event("planner_complete", {
            "iteration": state.current_iteration,
            "plan_length": len(plan)
        })
