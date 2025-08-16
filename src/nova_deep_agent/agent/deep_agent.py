"""
Nova Deep Agent Implementation
===============================

LangChain-based deep agent for automatically fixing failing CI tests.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType, Tool
from langchain.schema import SystemMessage

from ..tools.agent_tools import (
    plan_todo_tool,
    open_file_tool,
    write_file_tool,
    run_tests_tool
)
from .agent_config import AgentConfig


class DeepAgent:
    """
    Deep Agent for fixing failing tests using LangChain.
    
    This agent replaces the multi-node pipeline with a single intelligent
    agent that can plan, read files, write fixes, and run tests autonomously.
    """
    
    DEFAULT_SYSTEM_PROMPT = """You are an AI software agent tasked with fixing failing unit tests in a codebase.

You have access to the repository and can perform these actions:
1. Plan your approach using the 'plan_todo' tool (to outline fix steps).
2. Read code or test files using the 'open_file' tool.
3. Modify source code files using the 'write_file' tool.
4. Run the test suite using the 'run_tests' tool to check your fix.

Your goal is to make all tests pass by **minimally** editing the source code (do NOT edit the tests themselves).

Guidelines:
- Start by planning your approach to understand the failing tests
- Read relevant files to understand the code structure
- Make targeted, minimal changes to fix the issues
- Always verify your fixes by running the tests
- Iterate if needed until all tests pass
- Focus on fixing the root cause, not symptoms
- Preserve existing functionality while fixing bugs

Use the tools step-by-step: first plan your solution, then open relevant files, apply fixes, and run tests to verify.
Iterate as needed until all tests are passing. When all failures are resolved, stop and provide a final confirmation."""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the Deep Agent.
        
        Args:
            config: Agent configuration. Uses defaults if not provided.
        """
        self.config = config or AgentConfig()
        self.llm = None
        self.agent = None
        self.tools = []
        
        # Initialize the agent
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the LangChain agent with tools and configuration."""
        # Initialize the OpenAI model
        self.llm = ChatOpenAI(
            model=self.config.model_name,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        # Register all agent tools
        self.tools = self._create_tools()
        
        # Get system prompt
        system_prompt = self.config.system_prompt or self.DEFAULT_SYSTEM_PROMPT
        
        # Initialize the agent with OpenAI function-calling agent type
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=self.config.verbose,
            max_iterations=self.config.max_iterations,
            max_execution_time=self.config.max_execution_time,
            handle_parsing_errors=True
        )
        
        # Set the system message
        if hasattr(self.agent, 'agent') and hasattr(self.agent.agent, 'llm_chain'):
            # Update the system message in the prompt
            self.agent.agent.llm_chain.prompt.messages[0] = SystemMessage(content=system_prompt)
    
    def _create_tools(self) -> List[Tool]:
        """Create and return the list of tools for the agent."""
        tools = []
        
        if self.config.enable_planning:
            tools.append(Tool(
                name="plan_todo",
                func=plan_todo_tool,
                description=(
                    "Plan the next steps to fix the failing tests. "
                    "Input: optional notes/context. "
                    "Output: a step-by-step TODO plan."
                )
            ))
        
        if self.config.enable_file_access:
            tools.append(Tool(
                name="open_file",
                func=open_file_tool,
                description=(
                    "Read the contents of a file from the repository. "
                    "Input: file path relative to repo root. "
                    "Output: the file content as text (or an error message)."
                )
            ))
            
            tools.append(Tool(
                name="write_file",
                func=write_file_tool,
                description=(
                    "Write content to a file in the repository. "
                    "Input: file path and new content separated by '|||'. "
                    "Example: 'path/to/file.py|||new content here'. "
                    "Output: success confirmation or error message."
                ),
                # Custom wrapper to handle the special input format
                func=self._write_file_wrapper
            ))
        
        if self.config.enable_testing:
            tools.append(Tool(
                name="run_tests",
                func=run_tests_tool,
                description=(
                    "Run the full test suite in a sandboxed environment. "
                    "Input: none (just call the tool). "
                    "Output: JSON string with test results (passing/failing tests)."
                )
            ))
        
        return tools
    
    def _write_file_wrapper(self, input_str: str) -> str:
        """
        Wrapper for write_file_tool to handle LangChain's input format.
        
        LangChain passes a single string, so we need to parse it into
        file_path and content.
        """
        # Split on a delimiter (using ||| as it's unlikely to appear in code)
        parts = input_str.split("|||", 1)
        
        if len(parts) != 2:
            return "Error: Invalid input format. Use: 'file_path|||content'"
        
        file_path = parts[0].strip()
        content = parts[1]
        
        return write_file_tool(file_path, content)
    
    def run(self, user_prompt: str) -> str:
        """
        Run the agent with the given prompt.
        
        Args:
            user_prompt: The user's request or problem description.
            
        Returns:
            The agent's final output/response.
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized")
        
        try:
            result = self.agent.run(user_prompt)
            return result
        except Exception as e:
            return f"Error during agent execution: {e}"
    
    def fix_failing_tests(
        self,
        failing_tests: List[Dict[str, Any]],
        planner_notes: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Fix failing tests using the deep agent.
        
        Args:
            failing_tests: List of failing test information.
            planner_notes: Optional notes from a planning stage.
            
        Returns:
            Tuple of (success, message, patch_diff)
        """
        # Build the agent's user prompt with plan notes and failing test details
        failing_tests_desc = ""
        for test in failing_tests:
            file_path = test.get("file", "<unknown file>")
            test_name = test.get("name", "")
            error_msg = test.get("message", test.get("error", ""))
            failing_tests_desc += f"- {file_path}::{test_name}: {error_msg}\n"
        
        user_prompt = ""
        if planner_notes:
            user_prompt += f"Plan:\n{planner_notes}\n\n"
        
        user_prompt += f"Failing Tests:\n{failing_tests_desc}\n"
        user_prompt += "Please fix these failing tests by modifying the source code."
        
        # Run the agent
        result = self.run(user_prompt)
        
        # Check if tests are passing (would need to parse the agent's output)
        # For now, return the result
        return True, result, None
    
    def reset(self):
        """Reset the agent state."""
        # Re-initialize the agent to clear any state
        self._initialize_agent()
