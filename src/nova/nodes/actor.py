"""
Actor node for Nova CI-Rescue agent workflow.
"""

from typing import Dict, Any, Optional
from rich.console import Console

from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger

console = Console()


class ActorNode:
    """Node responsible for generating patches to fix failing tests."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def execute(
        self,
        state: AgentState,
        llm_agent: Any,
        telemetry: Optional[JSONLLogger] = None,
        critic_feedback: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a patch to fix failing tests.
        
        Args:
            state: Current agent state
            llm_agent: LLM agent instance for generating patches
            telemetry: Optional telemetry logger
            critic_feedback: Optional feedback from previous critic rejection
            
        Returns:
            Unified diff string or None if no patch can be generated
        """
        iteration = state.current_iteration
        
        # Log actor start
        if telemetry:
            telemetry.log_event("actor_start", {
                "iteration": iteration,
                "plan_available": state.plan is not None,
                "has_critic_feedback": critic_feedback is not None
            })
        
        if self.verbose:
            console.print(f"[cyan]🎭 Generating patch based on plan...[/cyan]")
        
        # Generate patch with plan context and critic feedback if available
        patch_diff = llm_agent.generate_patch(
            state.failing_tests, 
            iteration, 
            plan=state.plan, 
            critic_feedback=critic_feedback,
            state=state
        )
        
        if not patch_diff:
            console.print("[red]❌ Could not generate a patch[/red]")
            if telemetry:
                telemetry.log_event("actor_failed", {
                    "iteration": iteration,
                    "reason": "no_patch_generated"
                })
            return None
        
        # Display patch info
        patch_lines = patch_diff.split('\n')
        if self.verbose:
            console.print(f"[dim]Generated patch: {len(patch_lines)} lines[/dim]")
            console.print("[bold cyan]Full patch content:[/bold cyan]")
            # Show the full patch content (no line limit in verbose mode)
            for line in patch_lines:  
                if line.startswith('+++') or line.startswith('---'):
                    console.print(f"[bold]  {line}[/bold]")
                elif line.startswith('+'):
                    console.print(f"[green]  {line}[/green]")
                elif line.startswith('-'):
                    console.print(f"[red]  {line}[/red]")
                else:
                    console.print(f"[dim]  {line}[/dim]")
        
        # Log actor completion and save patch artifact
        if telemetry:
            telemetry.log_event("actor_complete", {
                "iteration": iteration,
                "patch_size": len(patch_lines),
                "patch_bytes": len(patch_diff)
            })
            # Save patch artifact (before apply, so we have it even if apply fails)
            telemetry.save_patch(iteration, patch_diff)
        
        return patch_diff


def actor_node(
    state: AgentState,
    llm_agent: Any,
    telemetry: Optional[JSONLLogger] = None,
    critic_feedback: Optional[str] = None,
    verbose: bool = False
) -> Optional[str]:
    """
    Convenience function to execute the actor node.
    
    Args:
        state: Current agent state
        llm_agent: LLM agent instance
        telemetry: Optional telemetry logger
        critic_feedback: Optional critic feedback
        verbose: Enable verbose output
        
    Returns:
        Patch diff string or None
    """
    node = ActorNode(verbose=verbose)
    return node.execute(state, llm_agent, telemetry, critic_feedback)
