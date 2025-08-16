"""
Nova Deep Agent Implementation
===============================

Orchestrator agent that uses LangChain's AgentExecutor to fix failing tests with minimal changes.
Utilizes a ReAct loop with tools: run_tests, apply_patch, critic_review.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path

from langchain.agents import AgentExecutor, Tool, initialize_agent, AgentType
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

# Use newer imports to avoid deprecation warnings
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    from langchain.chat_models import ChatOpenAI  # Fallback to old import

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    try:
        from langchain.chat_models import ChatAnthropic  # Fallback to old import
    except ImportError:
        ChatAnthropic = None  # Anthropic support may require separate package

from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger
from nova.agent.llm_agent import LLMAgent  # for fallback critic review LLM logic
from nova.tools.git import GitBranchManager

# Import unified tools
from nova.agent.unified_tools import create_default_tools


class NovaDeepAgent:
    """
    Orchestrator agent that uses LangChain's AgentExecutor to fix failing tests with minimal changes.
    Integrates with existing Nova state management and telemetry.
    """
    
    def __init__(
        self, 
        state: AgentState, 
        telemetry: JSONLLogger, 
        git_manager: Optional[GitBranchManager] = None,
        verbose: bool = False, 
        safety_config: Optional[Any] = None
    ):
        """
        Initialize the Deep Agent with the given state, telemetry logger, and optional Git branch manager.
        
        Args:
            state: AgentState tracking failures, iterations, etc.
            telemetry: JSONLLogger for telemetry events.
            git_manager: GitBranchManager for applying commits (if any).
            verbose: whether to print verbose output during operations.
            safety_config: optional SafetyConfig to enforce patch safety limits.
        """
        self.state = state
        self.telemetry = telemetry
        self.git_manager = git_manager
        self.verbose = verbose
        self.safety_config = safety_config
        
        # Initialize a legacy LLMAgent for critic review and (optionally) fallback patch generation
        self.legacy_agent = LLMAgent(state.repo_path)
        
        # Set up the LangChain agent
        self.agent = self._build_agent()
    
    def _build_agent(self) -> AgentExecutor:
        """Set up the LangChain Agent with the LLM, tools, and prompt."""
        # Choose an LLM based on configuration (support OpenAI GPT or Anthropic Claude)
        model_name = getattr(self.legacy_agent.settings, 'default_llm_model', 'gpt-4') if hasattr(self.legacy_agent, 'settings') else 'gpt-4'
        
        if model_name.lower().startswith("gpt") or ChatAnthropic is None:
            llm = ChatOpenAI(model_name=model_name, temperature=0)
        else:
            # Use Anthropic model if available and specified (e.g., "claude")
            llm = ChatAnthropic(model=model_name, temperature=0) if ChatAnthropic else ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        
        # System message prompt defining the agent's role and rules
        system_message = (
            "You are an AI software developer tasked with fixing failing unit tests in a codebase. "
            "You have access to the repository files and a test runner. Plan your approach, make code edits, and run tests until all tests pass. "
            "Do not modify tests themselves. Keep changes minimal and safe. Use the available tools when necessary, and stop when the tests are all green or you can't fix the issue."
        )
        
        # Create tools using unified module
        tools = create_default_tools(
            repo_path=self.state.repo_path,
            verbose=self.verbose,
            safety_config=self.safety_config,
            llm=None  # Will use default GPT-4 in CriticReviewTool
        )
        
        # Initialize the agent with tools and LLM (using OpenAI function-calling agent type for tool integration)
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=self.verbose,
            agent_kwargs={"system_message": system_message}
        )
        
        return agent
    
    def run(self, failures_summary: str = "", error_details: str = "", code_snippets: str = "") -> bool:
        """
        Execute the agent loop using the AgentExecutor.
        
        Args:
            failures_summary: Summary of failing tests
            error_details: Detailed error messages and stack traces
            code_snippets: Relevant code snippets
            
        Returns:
            True if all tests were fixed (success), False otherwise
        """
        # Prepare the user prompt with failing test details
        user_prompt = f"""The following tests are failing:
{failures_summary}

Stack traces and error snippets:
{error_details}

Relevant code snippets:
{code_snippets}

Begin fixing the tests. Use the available tools to:
1. Plan your approach using 'plan_todo'
2. Read relevant files using 'open_file'
3. Modify source code using 'write_file'
4. Run tests using 'run_tests' to verify your fixes

Remember: Do not modify test files. Keep changes minimal and focused on fixing the failures.
Stop when all tests pass or when no further progress can be made."""
        
        success = False
        
        try:
            # Log start of agent execution
            self.telemetry.log_event("deep_agent_start", {
                "failing_tests": self.state.total_failures,
                "iteration": self.state.current_iteration
            })
            
            # Run the agent until completion (or max iterations reached)
            result = self.agent.run(user_prompt)
            
            # Check if tests are passing after agent execution
            # Run final test check
            import json
            test_result_str = run_tests()
            test_result = json.loads(test_result_str)
            
            if test_result.get("exit_code") == 0:
                success = True
                self.state.final_status = "success"
                self.state.total_failures = 0
                self.telemetry.log_event("deep_agent_success", {
                    "iterations": self.state.current_iteration,
                    "message": "All tests passing"
                })
            else:
                # Tests still failing
                self.state.final_status = "incomplete"
                self.telemetry.log_event("deep_agent_incomplete", {
                    "iterations": self.state.current_iteration,
                    "remaining_failures": test_result.get("failures", "unknown")
                })
                
        except Exception as e:
            # Catch exceptions (could be max iteration or other errors)
            err_msg = str(e)
            self.telemetry.log_event("deep_agent_error", {
                "error": err_msg,
                "iteration": self.state.current_iteration
            })
            
            if "max iterations" in err_msg.lower():
                self.state.final_status = "max_iters"
            else:
                self.state.final_status = "error"
            
            success = False
        
        return success
