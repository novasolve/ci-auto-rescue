"""
Nova Deep Agent Implementation
===============================
Orchestrator agent that uses LangChain's AgentExecutor to fix failing tests with minimal changes.
Utilizes a ReAct loop with tools: run_tests, apply_patch, critic_review.
"""

from typing import Optional, Any
from pathlib import Path

from langchain.agents import AgentExecutor, Tool, initialize_agent, AgentType
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
# Use newer imports to avoid deprecation warnings
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    from langchain.chat_models import ChatOpenAI  # fallback
try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    try:
        from langchain.chat_models import ChatAnthropic  # fallback
    except ImportError:
        ChatAnthropic = None  # Anthropic support optional

from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger
from nova.tools.git import GitBranchManager
from nova.config import get_settings

# Import unified tools factory
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
        # Load runtime settings for LLM configuration
        self.settings = get_settings()
        # Build the LangChain agent executor
        self.agent = self._build_agent()

    def _build_agent(self) -> AgentExecutor:
        """Set up the LangChain Agent with the LLM, tools, and prompt."""
        # Choose LLM based on configuration (supports OpenAI GPT or Anthropic Claude)
        model_name = getattr(self.settings, 'default_llm_model', 'gpt-4')
        if model_name.lower().startswith("gpt") or ChatAnthropic is None:
            llm = ChatOpenAI(model_name=model_name, temperature=0)
        else:
            # Use Anthropic model if available and specified (e.g., "claude")
            llm = ChatAnthropic(model=model_name, temperature=0) if ChatAnthropic else ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        # Define the system message prompt for the agent
        system_message = (
            "You are an AI software developer tasked with fixing failing unit tests in a codebase. "
            "You have access to the repository files and a test runner. Plan your approach, make code edits, "
            "and run tests until all tests pass. Do not modify tests themselves. Keep changes minimal and safe. "
            "Use the available tools when necessary, and stop when the tests are all green or you can't fix the issue."
        )
        # Create the tool set (unified tools with safety and testing integrated)
        tools = create_default_tools(
            repo_path=self.state.repo_path,
            verbose=self.verbose,
            safety_config=self.safety_config,
            llm=None  # tools like CriticReviewTool will use default LLM if needed
        )
        # Initialize the LangChain agent with tools and LLM (using OpenAI function-calling agent type for tool integration)
        agent_executor = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=self.verbose,
            agent_kwargs={"system_message": system_message}
        )
        return agent_executor

    def run(self, failures_summary: str = "", error_details: str = "", code_snippets: str = "") -> bool:
        """
        Execute the agent loop using the LangChain AgentExecutor.

        Args:
            failures_summary: Summary of failing tests (e.g., table of test names and failures).
            error_details: Detailed error messages and stack traces from failing tests.
            code_snippets: Relevant code snippets that might be useful (optional).

        Returns:
            True if all tests were fixed (success), False otherwise.
        """
        success = False
        # Prepare a single user prompt with failing test details and instructions
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
        try:
            # Log the start of Deep Agent execution
            self.telemetry.log_event("deep_agent_start", {
                "failing_tests": self.state.total_failures,
                "iteration": self.state.current_iteration
            })
            if self.verbose:
                print(f"\n[DEBUG] Invoking agent with prompt length: {len(user_prompt)} chars")
            # Run the LangChain agent until completion (or until it decides to stop)
            result = self.agent({"input": user_prompt})
            if self.verbose:
                print(f"[DEBUG] Agent result type: {type(result)}")
                print(f"[DEBUG] Agent result (truncated): {str(result)[:500]}...")
            # After agent execution, run one final test suite to verify all tests
            import json
            # Use the RunTestsTool directly to get final test results
            final_test_output = None
            try:
                from nova.agent.unified_tools import RunTestsTool
                test_tool = RunTestsTool(repo_path=self.state.repo_path, verbose=self.verbose)
                output_str = test_tool.run(max_failures=5)
                final_test_output = json.loads(output_str)
            except Exception:
                # Fallback: direct runner if tool usage fails
                from nova.runner import TestRunner
                fallback_runner = TestRunner(self.state.repo_path, verbose=self.verbose)
                output_xml = fallback_runner.run_tests()  # returns JUnit XML or similar
                final_test_output = {"exit_code": 0 if output_xml and self.state.total_failures == 0 else 1}
            if final_test_output and final_test_output.get("exit_code") == 0:
                # All tests passing
                success = True
                self.state.final_status = "success"
                self.state.total_failures = 0
                self.telemetry.log_event("deep_agent_success", {
                    "iterations": self.state.current_iteration,
                    "message": "All tests passing"
                })
            else:
                # Tests still failing or result unknown
                self.state.final_status = "max_iters" if self.state.current_iteration >= self.state.max_iterations else "incomplete"
                self.telemetry.log_event("deep_agent_incomplete", {
                    "iterations": self.state.current_iteration,
                    "remaining_failures": final_test_output.get("failures", "unknown") if final_test_output else "unknown"
                })
        except Exception as e:
            import traceback
            err_msg = str(e)
            err_trace = traceback.format_exc()
            if self.verbose:
                print(f"\n[DEBUG] Deep Agent Error: {err_msg}")
                print(f"[DEBUG] Traceback:\n{err_trace}")
            self.telemetry.log_event("deep_agent_error", {
                "error": err_msg,
                "traceback": err_trace[:500],
                "iteration": self.state.current_iteration
            })
            # Mark appropriate final status on error
            if "max iterations" in err_msg.lower():
                self.state.final_status = "max_iters"
            else:
                self.state.final_status = "error"
            success = False
        return success