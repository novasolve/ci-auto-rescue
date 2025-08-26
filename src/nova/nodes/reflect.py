"""
Reflect node for Nova CI-Rescue agent workflow.
"""

from typing import Dict, Any, Optional
import time
from datetime import datetime
from nova.tools.datetime_utils import now_utc, seconds_between
from rich.console import Console

from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger

console = Console()


class ReflectNode:
    """Node responsible for deciding whether to continue or stop the loop."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def execute(
        self,
        state: AgentState,
        telemetry: Optional[JSONLLogger] = None
    ) -> Dict[str, Any]:
        """
        Analyze current state and decide next action.
        
        Args:
            state: Current agent state
            telemetry: Optional telemetry logger
            
        Returns:
            Decision dictionary with action and reason
        """
        iteration = state.current_iteration
        
        # Get test results from last run
        if state.test_results:
            last_result = state.test_results[-1]
            failures_before = last_result.get("failures_before", 0)
            failures_after = last_result.get("failures_after", 0)
        else:
            failures_before = state.total_failures
            failures_after = state.total_failures
        
        # Log reflect start
        if telemetry:
            telemetry.log_event("reflect_start", {
                "iteration": iteration,
                "failures_before": failures_before,
                "failures_after": failures_after,
                "timeout_remaining": state.timeout_seconds - (
                    (time.time() - state.start_time) if isinstance(state.start_time, float) 
                    else seconds_between(now_utc(), state.start_time) if state.start_time 
                    else 0
                )
            })
        
        if self.verbose:
            console.print(f"[cyan]🤔 Reflecting on progress...[/cyan]")
        
        # Decision logic
        decision = {"action": "continue", "reason": "unknown"}
        
        # Check if all tests are passing
        if state.total_failures == 0:
            decision = {
                "action": "success",
                "reason": "all_tests_passing",
                "message": f"All tests passing! Fixed in {iteration} iteration(s)."
            }
            state.final_status = "success"
            if self.verbose:
                console.print(f"[bold green]✅ {decision['message']}[/bold green]")
        
        # Check timeout
        elif state.check_timeout():
            decision = {
                "action": "stop",
                "reason": "timeout",
                "message": f"Timeout reached ({state.timeout_seconds}s)"
            }
            state.final_status = "timeout"
            console.print(f"[red]⏰ {decision['message']}[/red]")
        
        # Check max iterations
        elif iteration >= state.max_iterations:
            decision = {
                "action": "stop",
                "reason": "max_iterations",
                "message": f"Maximum iterations reached ({state.max_iterations})"
            }
            state.final_status = "max_iters"
            console.print(f"[red]🔄 {decision['message']}[/red]")
        
        # Check if we made progress
        elif failures_after < failures_before:
            fixed_count = failures_before - failures_after
            decision = {
                "action": "continue",
                "reason": "progress_made",
                "message": f"Fixed {fixed_count} test(s), {failures_after} remaining"
            }
            if self.verbose:
                console.print(f"[green]✓ {decision['message']}[/green]")
                console.print(f"[dim]Continuing to iteration {iteration + 1}...[/dim]")
        
        # No progress made
        else:
            decision = {
                "action": "continue",
                "reason": "no_progress",
                "message": f"No progress: {failures_after} test(s) still failing"
            }
            if self.verbose:
                console.print(f"[yellow]⚠ {decision['message']}[/yellow]")
                console.print(f"[dim]Trying different approach in iteration {iteration + 1}...[/dim]")
        
        # Log reflect completion
        if telemetry:
            telemetry.log_event("reflect_complete", {
                "iteration": iteration,
                "decision": decision["action"],
                "reason": decision["reason"],
                "failures_remaining": state.total_failures,
                "patches_applied": len(state.patches_applied)
            })
        
        return decision


def reflect_node(
    state: AgentState,
    telemetry: Optional[JSONLLogger] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to execute the reflect node.
    
    Args:
        state: Current agent state
        telemetry: Optional telemetry logger
        verbose: Enable verbose output
        
    Returns:
        Decision dictionary
    """
    node = ReflectNode(verbose=verbose)
    return node.execute(state, telemetry)
