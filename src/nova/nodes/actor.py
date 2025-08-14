"""
Actor node for Nova CI-Rescue agent workflow.
Generates patches to fix failing tests using LLM.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from rich.console import Console

from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger

console = Console()


class ActorNode:
    """Node responsible for generating patches based on the plan."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        
    def execute(
        self,
        state: AgentState,
        llm_agent: Any,
        logger: JSONLLogger,
        plan: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Generate a patch to fix failing tests based on the plan.
        
        Args:
            state: Current agent state
            llm_agent: LLM agent for patch generation
            logger: Telemetry logger
            plan: The plan created by the planner (optional, will use state.plan if not provided)
            
        Returns:
            Patch diff string or None if generation fails
        """
        iteration = state.current_iteration
        plan = plan or state.plan
        
        # Log actor start event with context
        logger.log_event("actor_start", {
            "iteration": iteration,
            "has_plan": plan is not None,
            "plan_approach": plan.get("approach") if plan else None,
            "target_tests": len(plan.get("target_tests", [])) if plan else 0,
            "failing_tests_count": len(state.failing_tests),
            "critic_feedback": state.critic_feedback[:200] if state.critic_feedback else None,
            "previous_patches_count": len(state.patches_applied),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        if self.verbose:
            console.print(f"[cyan]🎭 Generating patch based on plan...[/cyan]")
            if plan:
                console.print(f"[dim]Using plan: {plan.get('approach', 'Unknown approach')}[/dim]")
        
        start_time = datetime.utcnow()
        
        try:
            # Generate patch using LLM with plan and critic feedback
            patch_diff = llm_agent.generate_patch(
                state.failing_tests,
                iteration,
                plan=plan,
                critic_feedback=state.critic_feedback
            )
            
            if not patch_diff:
                # Log actor failure
                logger.log_event("actor_failed", {
                    "iteration": iteration,
                    "reason": "empty_patch",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                if self.verbose:
                    console.print("[red]❌ Could not generate a patch[/red]")
                return None
            
            # Calculate patch metrics
            patch_lines = patch_diff.split('\n')
            added_lines = sum(1 for line in patch_lines if line.startswith('+') and not line.startswith('+++'))
            removed_lines = sum(1 for line in patch_lines if line.startswith('-') and not line.startswith('---'))
            
            # Extract affected files from patch
            affected_files = []
            for line in patch_lines:
                if line.startswith('+++') or line.startswith('---'):
                    # Extract filename from +++ b/file.py or --- a/file.py
                    parts = line.split()
                    if len(parts) >= 2:
                        file_path = parts[1]
                        if file_path.startswith('a/') or file_path.startswith('b/'):
                            file_path = file_path[2:]
                        if file_path not in affected_files and file_path != '/dev/null':
                            affected_files.append(file_path)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Log actor completion event with patch metrics
            logger.log_event("actor_complete", {
                "iteration": iteration,
                "patch_metrics": {
                    "total_lines": len(patch_lines),
                    "added_lines": added_lines,
                    "removed_lines": removed_lines,
                    "affected_files": affected_files,
                    "affected_files_count": len(affected_files)
                },
                "execution_time_seconds": execution_time,
                "patch_preview": patch_diff[:500],  # First 500 chars for preview
                "timestamp": datetime.utcnow().isoformat()
            })
            
            if self.verbose:
                console.print(f"[green]✓ Generated patch: {len(patch_lines)} lines[/green]")
                console.print(f"  Added lines: {added_lines}")
                console.print(f"  Removed lines: {removed_lines}")
                console.print(f"  Files affected: {', '.join(affected_files[:3])}")
                if len(affected_files) > 3:
                    console.print(f"  ... and {len(affected_files) - 3} more")
            
            return patch_diff
            
        except Exception as e:
            # Log actor error
            logger.log_event("actor_error", {
                "iteration": iteration,
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            if self.verbose:
                console.print(f"[red]❌ Actor failed: {e}[/red]")
            
            return None


def generate_patch(
    state: AgentState,
    llm_agent: Any,
    logger: JSONLLogger,
    plan: Optional[Dict[str, Any]] = None,
    verbose: bool = False
) -> Optional[str]:
    """
    Convenience function to generate a patch using the ActorNode.
    
    Args:
        state: Current agent state
        llm_agent: LLM agent for patch generation
        logger: Telemetry logger
        plan: The plan created by the planner
        verbose: Enable verbose output
        
    Returns:
        Patch diff string or None if generation fails
    """
    node = ActorNode(verbose=verbose)
    return node.execute(state, llm_agent, logger, plan)