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

# Model capability registry for cleaner model handling
MODEL_CAPABILITIES = {
    "gpt-4": {"function_calling": True, "max_tokens": 8192, "fallback": None},
    "gpt-4-turbo": {"function_calling": True, "max_tokens": 128000, "fallback": "gpt-4"},
    "gpt-3.5-turbo": {"function_calling": True, "max_tokens": 4096, "fallback": None},
    "gpt-5": {"function_calling": True, "max_tokens": 16384, "fallback": "gpt-4"},  # GPT-5 supports function calling
    "gpt-5-turbo": {"function_calling": True, "max_tokens": 32768, "fallback": "gpt-4"},  # GPT-5 variants also support it
    "gpt-5-preview": {"function_calling": True, "max_tokens": 16384, "fallback": "gpt-4"},
    "claude-3-opus": {"function_calling": False, "max_tokens": 200000, "fallback": "gpt-4"},
    "claude-3-sonnet": {"function_calling": False, "max_tokens": 200000, "fallback": "gpt-4"},
}


def get_model_capabilities(model_name: str) -> dict:
    """Get capabilities for a model, with fallback to defaults."""
    # Check exact match first
    if model_name in MODEL_CAPABILITIES:
        return MODEL_CAPABILITIES[model_name]
    
    # Check for GPT-5 variants (now with function calling support)
    if model_name.lower().startswith("gpt-5"):
        return {"function_calling": True, "max_tokens": 16384, "fallback": "gpt-4"}
    
    # Check for GPT-4 variants
    if model_name.lower().startswith("gpt-4"):
        return {"function_calling": True, "max_tokens": 8192, "fallback": None}
    
    # Check for Claude variants
    if "claude" in model_name.lower():
        return {"function_calling": False, "max_tokens": 200000, "fallback": "gpt-4"}
    
    # Default to GPT-4-like capabilities
    return {"function_calling": True, "max_tokens": 8192, "fallback": None}


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
        safety_config: Optional[Any] = None,
        settings: Optional[Any] = None
    ):
        """
        Initialize the Deep Agent with the given state, telemetry logger, and optional Git branch manager.

        Args:
            state: AgentState tracking failures, iterations, etc.
            telemetry: JSONLLogger for telemetry events.
            git_manager: GitBranchManager for applying commits (if any).
            verbose: whether to print verbose output during operations.
            safety_config: optional SafetyConfig to enforce patch safety limits.
            settings: optional NovaSettings to use (defaults to get_settings() if not provided).
        """
        self.state = state
        self.telemetry = telemetry
        self.git_manager = git_manager
        self.verbose = verbose
        self.safety_config = safety_config
        # Use provided settings or load runtime settings for LLM configuration
        self.settings = settings or get_settings()
        # Build the LangChain agent executor
        self.agent = self._build_agent()

    def _build_agent(self) -> AgentExecutor:
        """Set up the LangChain Agent with the LLM, tools, and prompt."""
        # Get model name and capabilities
        model_name = getattr(self.settings, 'default_llm_model', 'gpt-4')
        
        # Show what model was requested for transparency
        if self.verbose:
            print(f"📋 Requested model: {model_name}")
        
        capabilities = get_model_capabilities(model_name)
        use_react = not capabilities["function_calling"]
        
        # Try to initialize the model with fallback support
        try:
            if model_name.lower().startswith("claude") and ChatAnthropic:
                llm = ChatAnthropic(model=model_name, temperature=0)
            else:
                # Try to use the model as requested, let OpenAI API handle availability
                llm = ChatOpenAI(model_name=model_name, temperature=0)
            
            if self.verbose:
                if use_react:
                    print(f"🚀 Using {model_name} model with ReAct pattern")
                else:
                    print(f"🚀 Using {model_name} model with function calling")
                    
        except Exception as e:
            # Fallback to configured fallback model
            fallback_model = capabilities.get("fallback")
            
            # If no fallback or fallback is None, use gpt-4 as ultimate fallback
            if not fallback_model:
                fallback_model = "gpt-4"
            
            # Always print the fallback reason for transparency
            print(f"⚠️  Model '{model_name}' not available: {str(e)[:100]}")
            print(f"    Falling back to '{fallback_model}'...")
            
            try:
                llm = ChatOpenAI(model_name=fallback_model, temperature=0)
                model_name = fallback_model  # Update for display
                self.settings.default_llm_model = fallback_model
                # Update capabilities for fallback model
                capabilities = get_model_capabilities(fallback_model)
                use_react = not capabilities["function_calling"]
                
                if self.verbose:
                    if use_react:
                        print(f"🚀 Using {model_name} model with ReAct pattern (fallback)")
                    else:
                        print(f"🚀 Using {model_name} model with function calling (fallback)")
            except Exception as fallback_error:
                # If even the fallback fails, raise a more informative error
                raise RuntimeError(
                    f"Failed to initialize both '{model_name}' and fallback '{fallback_model}'. "
                    f"Original error: {e}. Fallback error: {fallback_error}. "
                    f"Please ensure OPENAI_API_KEY is set and valid."
                )
        # Define the comprehensive system message prompt with all safety rules
        system_message = (
            "You are Nova, an advanced AI software engineer specialized in automatically fixing failing tests.\n\n"
            "## CRITICAL RULES - NEVER VIOLATE THESE:\n"
            "1. **NEVER MODIFY TEST FILES**: You must NEVER edit any file in tests/, test_*.py, or *_test.py\n"
            "   - If a test is wrong, document it but DO NOT change it\n"
            "   - Only fix source code to make tests pass\n\n"
            "2. **MINIMIZE DIFF SIZE**: Keep changes as small as possible\n"
            "   - Fix only what's necessary for tests to pass\n"
            "   - Don't refactor or improve unrelated code\n"
            "   - Each change should have a clear purpose\n\n"
            "3. **NO HALLUCINATING TOOLS**: Only use tools that actually exist\n"
            "   - Available tools: plan_todo, open_file, write_file, run_tests, apply_patch, critic_review\n"
            "   - Never invent or reference non-existent tools\n\n"
            "4. **SAFETY GUARDRAILS**: Respect all safety limits\n"
            "   - Max patch size: 500 lines\n"
            "   - Max files per patch: 10\n"
            "   - Never modify: .env, .git/, secrets/, .github/, CI/CD configs\n\n"
            "5. **VALID PATCHES ONLY**: Ensure all patches are syntactically valid\n"
            "   - Preserve indentation (spaces vs tabs)\n"
            "   - Maintain code style consistency\n"
            "   - Ensure no syntax errors introduced\n\n"
            "## YOUR WORKFLOW:\n"
            "1. ANALYZE: Understand the failing tests and their error messages\n"
            "2. INVESTIGATE: Read relevant source files to understand the code\n"
            "3. PLAN: Create a minimal fix strategy\n"
            "4. IMPLEMENT: Make targeted changes to fix the issues\n"
            "5. VERIFY: Run tests to confirm fixes work\n"
            "6. ITERATE: If tests still fail, analyze and adjust\n\n"
            "Remember: Your goal is to make ALL tests pass with MINIMAL, SAFE changes."
        )
        # Create the tool set (unified tools with safety and testing integrated)
        tools = create_default_tools(
            repo_path=self.state.repo_path,
            verbose=self.verbose,
            safety_config=self.safety_config,
            llm=llm  # Pass LLM for critic review
        )
        
        # Choose agent type based on model capabilities
        from langchain.agents import AgentType
        
        if use_react:
            # For GPT-5 and other models that don't support function calling
            # Use ReAct pattern with description-based tool selection
            agent_executor = initialize_agent(
                tools=tools,
                llm=llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=self.verbose,
                handle_parsing_errors=True,
                max_iterations=15,
                early_stopping_method="generate",
                agent_kwargs={
                    "prefix": system_message + "\n\nYou have access to the following tools:",
                    "format_instructions": "Use the following format:\n\nThought: I need to [describe what you need to do]\nAction: [the action/tool to take, should be one of the available tools]\nAction Input: [the input to the action]\nObservation: [the result of the action]\n... (this Thought/Action/Action Input/Observation can repeat N times)\nThought: I now know the final answer\nFinal Answer: [your final response]\n\nBegin!"
                }
            )
        else:
            # For GPT-4 and other models that support function calling
            agent_executor = initialize_agent(
                tools=tools,
                llm=llm,
                agent=AgentType.OPENAI_FUNCTIONS,
                verbose=self.verbose,
                agent_kwargs={"system_message": system_message},
                handle_parsing_errors=True,
                max_iterations=15
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
        # Prepare a comprehensive user prompt with failing test details and structured instructions
        user_prompt = f"""Fix the following failing tests:

## FAILURES SUMMARY:
{failures_summary}

## ERROR DETAILS (Stack traces and messages):
{error_details}

{f"## RELEVANT CODE SNIPPETS:\n{code_snippets}" if code_snippets else ""}

## YOUR TASK:
Use the available tools to fix the failing tests. Follow this workflow:

1. **Plan your approach** using 'plan_todo' - Outline what needs to be fixed
2. **Read relevant files** using 'open_file' - Understand the code structure
3. **Modify source code** using 'write_file' - Apply minimal fixes
4. **Run tests** using 'run_tests' - Verify your fixes work
5. **(Optional) Review patches** using 'critic_review' - Validate changes before applying
6. **(Optional) Apply patches** using 'apply_patch' - Commit validated changes

## REMEMBER:
- Do NOT modify test files (tests/, test_*.py, *_test.py)
- Keep changes minimal and focused on fixing the failures
- Only use the provided tools (no invented commands)
- Follow all safety guidelines
- Stop when tests are all green or you cannot fix the issue

Begin fixing the tests now."""
        try:
            # Log the start of Deep Agent execution
            self.telemetry.log_event("deep_agent_start", {
                "failing_tests": self.state.total_failures,
                "iteration": self.state.current_iteration
            })
            if self.verbose:
                print(f"\n[DEBUG] Invoking agent with prompt length: {len(user_prompt)} chars")
            
            # Run the LangChain agent with runtime fallback support
            try:
                result = self.agent({"input": user_prompt})
            except Exception as e:
                # Runtime fallback for GPT-5 to GPT-4 if function calling issues occur
                error_msg = str(e).lower()
                model_name = getattr(self.settings, 'default_llm_model', '').lower()
                
                if ("function" in error_msg or "unsupported value" in error_msg) and \
                   (model_name.startswith("gpt-5") or model_name in ["gpt-5-turbo", "gpt-5-preview"]):
                    if self.verbose:
                        print(f"\n⚠️ {self.settings.default_llm_model} runtime error: {e}")
                        print("🔄 Falling back to GPT-4 with function calling...")
                    
                    # Update settings and rebuild agent with GPT-4
                    self.settings.default_llm_model = "gpt-4"
                    self.agent = self._build_agent()
                    
                    # Retry with GPT-4
                    result = self.agent({"input": user_prompt})
                    if self.verbose:
                        print("✅ Successfully recovered with GPT-4")
                else:
                    # Re-raise if not a GPT-5 function calling issue
                    raise
            
            if self.verbose:
                print(f"[DEBUG] Agent result type: {type(result)}")
                print(f"[DEBUG] Agent result (truncated): {str(result)[:500]}...")
            # After agent execution, run one final test suite to verify all tests
            import json
            # Use the RunTestsTool directly to get final test results (always returns JSON)
            final_test_output = None
            try:
                from nova.agent.unified_tools import RunTestsTool
                test_tool = RunTestsTool(repo_path=self.state.repo_path, verbose=self.verbose)
                output_str = test_tool._run(max_failures=10)  # Direct call to _run
                final_test_output = json.loads(output_str)
                
                if self.verbose:
                    print(f"[DEBUG] Final test results: {final_test_output}")
                    
            except json.JSONDecodeError as e:
                if self.verbose:
                    print(f"[DEBUG] JSON decode error: {e}")
                # Malformed JSON, treat as failure
                final_test_output = {"exit_code": 1, "error": "Invalid test output format"}
            except Exception as e:
                if self.verbose:
                    print(f"[DEBUG] Test execution error: {e}")
                # Fallback: direct runner if tool usage fails
                try:
                    from nova.runner import TestRunner
                    fallback_runner = TestRunner(self.state.repo_path, verbose=self.verbose)
                    failing_tests, summary = fallback_runner.run_tests()
                    final_test_output = {
                        "exit_code": 0 if not failing_tests else 1,
                        "failures": len(failing_tests) if failing_tests else 0,
                        "message": "Tests completed"
                    }
                except Exception as runner_error:
                    if self.verbose:
                        print(f"[DEBUG] Fallback runner error: {runner_error}")
                    final_test_output = {"exit_code": 1, "error": str(runner_error)}
            
            # Check test results
            if final_test_output and final_test_output.get("exit_code") == 0:
                # All tests passing
                success = True
                self.state.final_status = "success"
                self.state.total_failures = 0
                self.telemetry.log_event("deep_agent_success", {
                    "iterations": self.state.current_iteration,
                    "message": "All tests passing",
                    "tests_passed": final_test_output.get("passed", "unknown")
                })
            else:
                # Tests still failing or result unknown
                failures_count = final_test_output.get("failures", "unknown") if final_test_output else "unknown"
                self.state.final_status = "max_iters" if self.state.current_iteration >= self.state.max_iterations else "incomplete"
                self.telemetry.log_event("deep_agent_incomplete", {
                    "iterations": self.state.current_iteration,
                    "remaining_failures": failures_count,
                    "error": final_test_output.get("error") if final_test_output else None
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