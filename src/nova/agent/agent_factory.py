"""
Agent Factory for Nova CI-Rescue
=================================

Factory pattern to create different agent types based on configuration.
Supports Deep Agent (default) and legacy agent (deprecated).
"""

from typing import Optional, Any, Literal
from pathlib import Path
import warnings

from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger
from nova.tools.git import GitBranchManager


class AgentFactory:
    """
    Factory for creating Nova agents.
    
    This factory supports creating:
    - Deep Agent (default): The new LangChain-powered intelligent agent
    - Legacy Agent: The old multi-node pipeline (deprecated)
    """
    
    @staticmethod
    def create_agent(
        agent_type: Literal["deep", "legacy"] = "deep",
        state: Optional[AgentState] = None,
        telemetry: Optional[JSONLLogger] = None,
        git_manager: Optional[GitBranchManager] = None,
        verbose: bool = False,
        safety_config: Optional[Any] = None,
        **kwargs
    ):
        """
        Create an agent based on the specified type.
        
        Args:
            agent_type: Type of agent to create ("deep" or "legacy")
            state: Agent state
            telemetry: Telemetry logger
            git_manager: Git branch manager
            verbose: Enable verbose output
            safety_config: Safety configuration
            **kwargs: Additional agent-specific arguments
            
        Returns:
            The created agent instance
            
        Raises:
            ValueError: If an invalid agent type is specified
        """
        if agent_type == "deep":
            # Use the latest Deep Agent implementation from nova_deep_agent module
            try:
                # Try to import the newer nova_deep_agent module first
                from nova_deep_agent.agent.deep_agent import DeepAgent
                from nova_deep_agent.agent.agent_config import AgentConfig
                
                # Create config for the new Deep Agent
                config = AgentConfig(
                    verbose=verbose,
                    max_iterations=kwargs.get('max_iterations', 50),
                    max_execution_time=kwargs.get('max_execution_time', 3600)
                )
                
                # The newer DeepAgent has a different interface
                agent = DeepAgent(config=config)
                
                # Wrap it to match the expected interface
                class DeepAgentWrapper:
                    def __init__(self, deep_agent, state, telemetry, git_manager):
                        self.agent = deep_agent
                        self.state = state
                        self.telemetry = telemetry
                        self.git_manager = git_manager
                    
                    def run(self, failures_summary: str, error_details: str, code_snippets: str = "") -> bool:
                        """Run the Deep Agent to fix tests."""
                        # Format the task for the agent
                        task = f"""
                        Fix the following failing tests:
                        
                        {failures_summary}
                        
                        Error Details:
                        {error_details}
                        
                        {code_snippets if code_snippets else ''}
                        """
                        
                        try:
                            result = self.agent.run(task.strip())
                            # Check if tests are passing after the fix
                            from nova.runner import TestRunner
                            runner = TestRunner(self.state.repo_path)
                            failing_tests, passing_count = runner.run_tests()
                            return len(failing_tests) == 0
                        except Exception as e:
                            if self.telemetry:
                                self.telemetry.log_error(f"Deep Agent error: {str(e)}")
                            return False
                
                return DeepAgentWrapper(agent, state, telemetry, git_manager)
                
            except ImportError:
                # Fall back to the existing deep_agent module
                from nova.agent.deep_agent import NovaDeepAgent
                return NovaDeepAgent(
                    state=state,
                    telemetry=telemetry,
                    git_manager=git_manager,
                    verbose=verbose,
                    safety_config=safety_config
                )
                
        elif agent_type == "legacy":
            warnings.warn(
                "⚠️  DEPRECATION WARNING: The legacy agent is deprecated and will be removed in v2.0. "
                "Please use the default Deep Agent instead.",
                DeprecationWarning,
                stacklevel=2
            )
            
            # Create a simplified legacy agent that mimics the old behavior
            # Since LLMAgent was removed, we'll create a minimal implementation
            from nova.agent.legacy_agent import LegacyAgent
            return LegacyAgent(
                state=state,
                telemetry=telemetry,
                git_manager=git_manager,
                verbose=verbose,
                safety_config=safety_config
            )
            
        else:
            raise ValueError(
                f"Invalid agent type: {agent_type}. "
                f"Valid options are: 'deep' (default), 'legacy' (deprecated)"
            )
    
    @staticmethod
    def get_available_agents() -> list:
        """Get list of available agent types."""
        return ["deep", "legacy"]
    
    @staticmethod
    def get_default_agent() -> str:
        """Get the default agent type."""
        return "deep"
