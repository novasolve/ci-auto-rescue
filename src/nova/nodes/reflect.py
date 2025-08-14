"""
Reflect node for Nova CI-Rescue agent workflow.
Analyzes test results and decides whether to continue or stop the agent loop.
"""

from typing import Dict, Any, Tuple
from datetime import datetime
from rich.console import Console

from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger

console = Console()


class ReflectNode:
    """Node responsible for deciding whether to continue or stop the agent loop."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        
    def execute(
        self,
        state: AgentState,
        test_results: Dict[str, Any],
        logger: JSONLLogger
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Analyze test results and decide next action.
        
        Args:
            state: Current agent state
            test_results: Results from the last test run
            logger: Telemetry logger
            
        Returns:
            Tuple of (should_continue: bool, decision: str, metadata: dict)
        """
        iteration = state.current_iteration
        
        # Extract metrics from test results
        current_failures = test_results.get("failure_count", 0)
        previous_failures = test_results.get("previous_failure_count", 0)
        tests_fixed = test_results.get("tests_fixed", [])
        new_failures = test_results.get("new_failures", [])
        
        # Calculate progress metrics
        progress_made = current_failures < previous_failures
        all_fixed = current_failures == 0
        regression = len(new_failures) > 0
        
        # Check termination conditions
        timeout_reached = state.check_timeout()
        max_iterations_reached = iteration >= state.max_iterations
        
        # Calculate time elapsed
        elapsed_seconds = (datetime.now() - state.start_time).total_seconds()
        
        # Log reflect start
        logger.log_event("reflect_start", {
            "iteration": iteration,
            "current_failures": current_failures,
            "previous_failures": previous_failures,
            "tests_fixed_count": len(tests_fixed),
            "new_failures_count": len(new_failures),
            "progress_made": progress_made,
            "all_fixed": all_fixed,
            "regression": regression,
            "timeout_reached": timeout_reached,
            "max_iterations_reached": max_iterations_reached,
            "elapsed_seconds": elapsed_seconds,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        if self.verbose:
            console.print(f"\n[cyan]🤔 Reflecting on results...[/cyan]")
        
        # Decision logic
        should_continue = False
        decision = ""
        reason = ""
        
        if all_fixed:
            # Success - all tests passing
            should_continue = False
            decision = "success"
            reason = "all_tests_passing"
            state.final_status = "success"
            
            if self.verbose:
                console.print(f"[bold green]✅ Success! All tests are now passing.[/bold green]")
                
        elif timeout_reached:
            # Timeout reached
            should_continue = False
            decision = "stop"
            reason = "timeout"
            state.final_status = "timeout"
            
            if self.verbose:
                console.print(f"[red]⏰ Timeout reached ({state.timeout_seconds}s)[/red]")
                
        elif max_iterations_reached:
            # Max iterations reached
            should_continue = False
            decision = "stop"
            reason = "max_iterations"
            state.final_status = "max_iters"
            
            if self.verbose:
                console.print(f"[red]🔄 Maximum iterations reached ({state.max_iterations})[/red]")
                
        elif not progress_made and iteration >= 3:
            # No progress after 3 iterations
            should_continue = False
            decision = "stop"
            reason = "no_progress"
            state.final_status = "no_progress"
            
            if self.verbose:
                console.print(f"[yellow]⚠ No progress after {iteration} iterations, stopping[/yellow]")
                
        else:
            # Continue trying
            should_continue = True
            decision = "continue"
            
            if progress_made:
                reason = "progress_made"
                if self.verbose:
                    console.print(f"[green]✓ Progress made: fixed {len(tests_fixed)} test(s)[/green]")
            else:
                reason = "retry"
                if self.verbose:
                    console.print(f"[yellow]Retrying with different approach...[/yellow]")
        
        # Build metadata
        metadata = {
            "iteration": iteration,
            "decision": decision,
            "reason": reason,
            "should_continue": should_continue,
            "metrics": {
                "current_failures": current_failures,
                "previous_failures": previous_failures,
                "tests_fixed": len(tests_fixed),
                "new_failures": len(new_failures),
                "total_patches_applied": len(state.patches_applied),
                "elapsed_seconds": elapsed_seconds,
                "iterations_remaining": state.max_iterations - iteration,
                "timeout_remaining": max(0, state.timeout_seconds - elapsed_seconds)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log reflect completion
        logger.log_event("reflect_complete", metadata)
        
        # Display summary if stopping
        if not should_continue and self.verbose:
            console.print(f"\n[bold]Summary:[/bold]")
            console.print(f"  • Iterations: {iteration}/{state.max_iterations}")
            console.print(f"  • Patches applied: {len(state.patches_applied)}")
            console.print(f"  • Tests fixed: {sum(len(r.get('tests_fixed', [])) for r in [test_results])}")
            console.print(f"  • Remaining failures: {current_failures}")
            
            minutes, seconds = divmod(int(elapsed_seconds), 60)
            console.print(f"  • Time elapsed: {minutes}m {seconds}s")
        
        return should_continue, decision, metadata


def reflect(
    state: AgentState,
    test_results: Dict[str, Any],
    logger: JSONLLogger,
    verbose: bool = False
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Convenience function to reflect on results using the ReflectNode.
    
    Args:
        state: Current agent state
        test_results: Results from the last test run
        logger: Telemetry logger
        verbose: Enable verbose output
        
    Returns:
        Tuple of (should_continue: bool, decision: str, metadata: dict)
    """
    node = ReflectNode(verbose=verbose)
    return node.execute(state, test_results, logger)