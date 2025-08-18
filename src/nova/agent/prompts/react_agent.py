"""
ReAct Agent Implementation for Nova
====================================

Implements the ReAct (Reasoning and Acting) pattern for better agent performance.
Ready for current models (GPT-4) and future models (GPT-5).
"""

from typing import Optional, Dict, Any, List
import json
import re
from langchain.agents import AgentType, initialize_agent, Tool
from langchain.prompts import PromptTemplate
from langchain.schema import AgentAction, AgentFinish
from langchain.agents.agent import AgentOutputParser

from .model_config import ModelFactory, ModelConfig, get_optimal_model_for_task
from .system_prompt import NovaSystemPrompt
from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger


class ReActPrompt:
    """ReAct-specific prompts for Nova agent."""
    
    PREFIX = """You are Nova, an advanced AI using the ReAct (Reasoning and Acting) paradigm to fix failing tests.

## Core Rules (NEVER VIOLATE):
{core_rules}

## ReAct Process:
You will solve problems by interleaving Thought, Action, and Observation steps:
- Thought: Reason about the current situation and what to do next
- Action: Use a tool to gather information or make changes
- Observation: Observe the result of your action
- Repeat until the problem is solved

## Available Tools:
{tools}

## Example ReAct Trace:
Question: Fix failing test_calculator.py

Thought: I need to first understand what tests are failing and why.
Action: run_tests
Action Input: {{}}
Observation: test_add failed: AssertionError: 5 != 6

Thought: The test expects 6 but gets 5. I should examine the add function.
Action: open_file
Action Input: {{"path": "calculator.py"}}
Observation: def add(a, b): return a + b - 1  # Bug here

Thought: I found the bug - the function subtracts 1. I'll fix it.
Action: write_file
Action Input: {{"path": "calculator.py", "content": "def add(a, b): return a + b"}}
Observation: File written successfully

Thought: Now I'll verify the fix works by running tests. This step is MANDATORY.
Action: run_tests
Action Input: {{}}
Observation: All tests passing

Thought: The issue is resolved. I've verified all tests pass.
Final Answer: Fixed the add function by removing the incorrect subtraction of 1.

## Note on Tool Responses:

Some tools may return SKIP messages when preventing redundant operations:
- "SKIP: File already opened" - The file content is in your previous observation, DO NOT try to open it again
- "SKIP: Plan already noted" - Continue with implementation, DO NOT plan again
- "SKIP: No changes since last run" - Use previous test results, DO NOT run tests again

These are NOT errors - they help you work efficiently by avoiding duplicate work.

IMPORTANT: When you see a SKIP message:
1. Look back at your previous observations for the information
2. Continue with your next action using that information
3. DO NOT repeat the same action that was skipped

## Your Task:
{input}

## Begin ReAct Process:
{agent_scratchpad}"""
    
    FORMAT_INSTRUCTIONS = """
Use the following format EXACTLY:

Thought: [your reasoning about what to do next]
Action: [tool name]
Action Input: [tool input as JSON]
Observation: [tool output - this will be filled in automatically]
... (repeat Thought/Action/Observation as needed)
Thought: [final reasoning]
Final Answer: [summary of what was fixed]
"""


class ReActOutputParser(AgentOutputParser):
    """Parser for ReAct format outputs."""
    
    def parse(self, llm_output: str) -> AgentAction | AgentFinish:
        """Parse LLM output in ReAct format."""
        
        # Check for Final Answer
        if "Final Answer:" in llm_output:
            return AgentFinish(
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                log=llm_output
            )
        
        # Parse Action and Action Input
        action_match = re.search(r"Action:\s*(.+?)(?:\n|$)", llm_output)
        action_input_match = re.search(r"Action Input:\s*(.+?)(?:\n|$)", llm_output, re.DOTALL)
        
        if action_match and action_input_match:
            action = action_match.group(1).strip()
            action_input = action_input_match.group(1).strip()
            
            # Try to parse JSON input
            try:
                if action_input.startswith("{"):
                    action_input = json.loads(action_input)
                else:
                    # Convert to appropriate format for the tool
                    action_input = action_input.strip('"')
            except:
                pass  # Use raw string if not JSON
            
            return AgentAction(
                tool=action,
                tool_input=action_input,
                log=llm_output
            )
        
        raise ValueError(f"Could not parse LLM output: {llm_output}")


class NovaReActAgent:
    """
    Nova agent using ReAct pattern, ready for GPT-5 and future models.
    """
    
    def __init__(
        self,
        state: AgentState,
        telemetry: Optional[JSONLLogger] = None,
        model_name: Optional[str] = None,
        model_config: Optional[ModelConfig] = None,
        verbose: bool = False,
        use_react: bool = True
    ):
        """
        Initialize ReAct agent with flexible model configuration.
        
        Args:
            state: Agent state for tracking
            telemetry: Optional telemetry logger
            model_name: Model to use (e.g., "gpt-5", "gpt-4", "claude-3.5-sonnet")
            model_config: Custom model configuration
            verbose: Enable verbose output
            use_react: Use ReAct pattern (vs function calling)
        """
        self.state = state
        self.telemetry = telemetry
        self.verbose = verbose
        self.use_react = use_react
        
        # Determine model configuration
        if model_config:
            self.model_config = model_config
        elif model_name:
            self.model_config = ModelFactory.get_config(model_name)
        else:
            # Auto-select optimal model
            task_complexity = self._assess_task_complexity()
            optimal_model = get_optimal_model_for_task(
                task_type=task_complexity,
                require_json=True,
                future_models_enabled=True
            )
            self.model_config = ModelFactory.get_config(optimal_model)
        
        if self.verbose:
            print(f"🤖 Using model: {self.model_config.name}")
            print(f"   Provider: {self.model_config.provider}")
            print(f"   Capabilities: {self.model_config.capabilities}")
        
        # Create LLM
        self.llm = ModelFactory.create_llm(self.model_config)
        
        # Create agent
        self.agent = self._create_agent()
    
    def _assess_task_complexity(self) -> str:
        """Assess task complexity based on state."""
        failure_count = len(self.state.failing_tests) if hasattr(self.state, 'failing_tests') else 0
        
        if failure_count <= 2:
            return "simple_fix"
        elif failure_count <= 5:
            return "complex_fix"
        else:
            return "multi_file"
    
    def _create_agent(self):
        """Create the agent with appropriate configuration."""
        from nova.agent.unified_tools import create_default_tools
        
        # Get tools
        tools = create_default_tools(
            repo_path=self.state.repo_path,
            verbose=self.verbose
        )
        
        if self.use_react and self.model_config.capabilities.supports_react:
            # Use ReAct pattern
            return self._create_react_agent(tools)
        else:
            # Use function calling (for models that support it)
            return self._create_function_agent(tools)
    
    def _create_react_agent(self, tools: List[Tool]):
        """Create a ReAct-style agent."""
        # Get core rules
        core_rules = NovaSystemPrompt.CORE_RULES
        
        # Create prompt
        prompt = PromptTemplate(
            template=ReActPrompt.PREFIX + "\n\n" + ReActPrompt.FORMAT_INSTRUCTIONS,
            input_variables=["input", "agent_scratchpad"],
            partial_variables={
                "core_rules": core_rules,
                "tools": "\n".join([f"- {t.name}: {t.description}" for t in tools])
            }
        )
        
        # Create agent with ReAct parser
        try:
            from langchain.agents import create_react_agent
            agent = create_react_agent(
                llm=self.llm,
                tools=tools,
                prompt=prompt,
                output_parser=ReActOutputParser()
            )
        except ImportError:
            # Fallback for older LangChain versions
            from langchain.agents import ZeroShotAgent, LLMChain
            
            llm_chain = LLMChain(llm=self.llm, prompt=prompt)
            agent = ZeroShotAgent(
                llm_chain=llm_chain,
                tools=tools,
                output_parser=ReActOutputParser()
            )
        
        from langchain.agents import AgentExecutor
        
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=self.verbose,
            max_iterations=15,  # More iterations for ReAct
            handle_parsing_errors=True
        )
    
    def _create_function_agent(self, tools: List[Tool]):
        """Create a function-calling agent (fallback)."""
        return initialize_agent(
            tools=tools,
            llm=self.llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=self.verbose,
            agent_kwargs={
                "system_message": NovaSystemPrompt.get_full_prompt()
            }
        )
    
    def run(
        self,
        failures_summary: str,
        error_details: str,
        code_snippets: str = ""
    ) -> bool:
        """
        Run the ReAct agent to fix failing tests.
        
        Args:
            failures_summary: Summary of failing tests
            error_details: Detailed error messages
            code_snippets: Optional relevant code
            
        Returns:
            True if all tests pass, False otherwise
        """
        # Format input
        user_input = f"""Fix the following failing tests:

FAILURES:
{failures_summary}

ERROR DETAILS:
{error_details}

{f"CODE CONTEXT:\n{code_snippets}" if code_snippets else ""}

Remember: Follow all core rules, especially never modifying test files."""
        
        # Log start
        if self.telemetry:
            self.telemetry.log_event("react_agent_start", {
                "model": self.model_config.name,
                "use_react": self.use_react,
                "task_complexity": self._assess_task_complexity()
            })
        
        try:
            # Run agent
            if self.verbose:
                print("\n" + "="*60)
                print("🚀 Starting ReAct Agent Process")
                print("="*60 + "\n")
            
            result = self.agent.invoke({"input": user_input})
            
            if self.verbose:
                print("\n" + "="*60)
                print("✅ ReAct Process Complete")
                print("="*60 + "\n")
            
            # Log completion
            if self.telemetry:
                self.telemetry.log_event("react_agent_complete", {
                    "model": self.model_config.name,
                    "success": True,
                    "output_length": len(str(result))
                })
            
            # Check if tests pass
            return self._verify_tests_pass()
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Agent error: {e}")
            
            if self.telemetry:
                self.telemetry.log_event("react_agent_error", {
                    "model": self.model_config.name,
                    "error": str(e)
                })
            
            return False
    
    def _verify_tests_pass(self) -> bool:
        """Verify all tests are passing."""
        from nova.runner import TestRunner
        runner = TestRunner(self.state.repo_path)
        failing_tests, _ = runner.run_tests()
        return len(failing_tests) == 0


def create_gpt5_agent(
    state: AgentState,
    telemetry: Optional[JSONLLogger] = None,
    verbose: bool = False
) -> NovaReActAgent:
    """
    Create a GPT-5 optimized agent (forward-compatible).
    
    When GPT-5 becomes available, this will automatically use it.
    Until then, it uses the best available model.
    
    Args:
        state: Agent state
        telemetry: Optional telemetry
        verbose: Enable verbose output
        
    Returns:
        NovaReActAgent configured for GPT-5 (or best available)
    """
    # Try GPT-5 first, fall back to best available
    try:
        return NovaReActAgent(
            state=state,
            telemetry=telemetry,
            model_name="gpt-5",
            verbose=verbose,
            use_react=True  # GPT-5 should excel at ReAct
        )
    except:
        # GPT-5 not available yet, use best current model
        if verbose:
            print("⚠️ GPT-5 not available, using GPT-4 Turbo")
        
        return NovaReActAgent(
            state=state,
            telemetry=telemetry,
            model_name="gpt-4-turbo-preview",
            verbose=verbose,
            use_react=True
        )
