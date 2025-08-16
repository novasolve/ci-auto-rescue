"""
Planner node for Nova CI-Rescue agent workflow.
Generates plans for fixing failing tests using LLM.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from rich.console import Console

from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger

console = Console()


class PlannerNode:
    """Node responsible for creating fix plans based on failing tests."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        
    def execute(
        self,
        state: AgentState,
        llm_agent: Any,
        logger: JSONLLogger,
        critic_feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a plan for fixing failing tests.
        
        Args:
            state: Current agent state
            llm_agent: LLM agent for plan generation
            logger: Telemetry logger
            critic_feedback: Optional feedback from previous critic rejection
            
        Returns:
            Plan dictionary with approach, steps, and target tests
        """
        iteration = state.current_iteration
        
        # Log planner start event with detailed context
        logger.log_event("planner_start", {
            "iteration": iteration,
            "failing_tests_count": len(state.failing_tests),
            "failing_tests": [
                {
                    "name": test.get("name"),
                    "file": test.get("file"),
                    "line": test.get("line"),
                    "error_preview": test.get("short_traceback", "")[:200]
                }
                for test in state.failing_tests[:5]  # Log first 5 tests
            ],
            "has_critic_feedback": critic_feedback is not None,
            "critic_feedback": critic_feedback[:500] if critic_feedback else None,
            "patches_applied_count": len(state.patches_applied),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        if self.verbose:
            console.print(f"[cyan]🧠 Planning fix for {len(state.failing_tests)} failing test(s)...[/cyan]")
            if critic_feedback:
                console.print(f"[dim]Previous critic feedback: {critic_feedback[:100]}...[/dim]")
        
        try:
            # Generate plan using LLM
            plan = llm_agent.create_plan(
                state.failing_tests,
                iteration,
                critic_feedback=critic_feedback
            )
            
            # Ensure plan has required structure
            if not isinstance(plan, dict):
                plan = {
                    "approach": "Fix failing tests",
                    "target_tests": state.failing_tests[:2],
                    "steps": ["Analyze failures", "Generate fixes", "Apply patches"]
                }
            
            # Add metadata to plan
            plan["iteration"] = iteration
            plan["generated_at"] = datetime.utcnow().isoformat()
            plan["failing_count"] = len(state.failing_tests)
            
            # Store plan in state
            state.plan = plan
            
            # Log planner completion event
            logger.log_event("planner_complete", {
                "iteration": iteration,
                "plan": {
                    "approach": plan.get("approach", "Unknown"),
                    "steps": plan.get("steps", [])[:5],  # Log first 5 steps
                    "target_tests_count": len(plan.get("target_tests", [])),
                    "strategy": plan.get("strategy", "Direct fixes")
                },
                "execution_time_ms": 0,  # Would need timing logic
                "timestamp": datetime.utcnow().isoformat()
            })
            
            if self.verbose:
                console.print("[green]✓ Plan created successfully[/green]")
                console.print(f"  Approach: {plan.get('approach', 'Unknown')}")
                if plan.get('steps'):
                    console.print("  Steps:")
                    for i, step in enumerate(plan.get('steps', [])[:3], 1):
                        console.print(f"    {i}. {step}")
            
            return plan
            
        except Exception as e:
            # Log planner error
            logger.log_event("planner_error", {
                "iteration": iteration,
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            if self.verbose:
                console.print(f"[red]❌ Planner failed: {e}[/red]")
            
            # Return fallback plan
            fallback_plan = {
                "approach": "Fix failing tests incrementally",
                "target_tests": state.failing_tests[:2],
                "steps": ["Fix first failure", "Re-run tests", "Fix remaining failures"],
                "iteration": iteration,
                "generated_at": datetime.utcnow().isoformat(),
                "is_fallback": True
            }
            
            state.plan = fallback_plan
            return fallback_plan


def create_plan(
    state: AgentState,
    llm_agent: Any,
    logger: JSONLLogger,
    critic_feedback: Optional[str] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to create a plan using the PlannerNode.
    
    Args:
        state: Current agent state
        llm_agent: LLM agent for plan generation
        logger: Telemetry logger
        critic_feedback: Optional feedback from previous critic rejection
        verbose: Enable verbose output
        
    Returns:
        Plan dictionary
    """
    node = PlannerNode(verbose=verbose)
    return node.execute(state, llm_agent, logger, critic_feedback)