"""
Nova Deep Agent - Best of Both Worlds
======================================

Enhanced implementation that combines our clean design with production features.
Supports both class-based and function-based tools, multiple LLMs, and YAML config.
"""

from typing import Optional, List, Dict, Any, Union
from pathlib import Path
import json

from langchain.agents import AgentExecutor, initialize_agent, AgentType, Tool
from langchain.tools import BaseTool

# LLM imports with fallbacks
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    from langchain.chat_models import ChatOpenAI

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

try:
    from langchain_community.llms import HuggingFacePipeline
except ImportError:
    HuggingFacePipeline = None

from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger
from nova.tools.git import GitBranchManager
from nova.config import NovaSettings, SafetyConfig


class NovaDeepAgent:
    """
    Enhanced Deep Agent that combines the best of both implementations.
    
    Features:
    - Supports both class-based and function-based tools
    - Multiple LLM support (GPT, Claude, Llama)
    - YAML configuration
    - Pre-agent test discovery
    - Full telemetry integration
    """
    
    SYSTEM_PROMPT = """You are Nova, an AI software engineer fixing failing tests.

Your workflow:
1. Run tests to see failures
2. Plan your approach
3. Review relevant code files
4. Create a patch
5. Have it reviewed by the critic
6. Apply approved patches
7. Verify tests pass

Rules:
- NEVER modify test files
- Keep changes minimal and focused
- Use proper unified diff format
- Always get critic approval before applying patches
- Stop when all tests pass

Available tools:
- run_tests: Check current test status
- open_file: Read source code (if available)
- write_file: Modify source code (if available)
- critic_review: Review patches before applying
- apply_patch: Apply approved patches

You have {max_iterations} iterations to fix all tests."""
    
    def __init__(
        self,
        tools: Optional[List[Union[BaseTool, Tool]]] = None,
        state: Optional[AgentState] = None,
        telemetry: Optional[JSONLLogger] = None,
        llm_model: Optional[str] = None,
        settings: Optional[NovaSettings] = None,
        verbose: bool = False
    ):
        """
        Initialize the Nova Deep Agent.
        
        Args:
            tools: List of tools (can be class-based or function-based)
            state: Agent state for tracking progress
            telemetry: Telemetry logger
            llm_model: LLM model name (gpt-4, claude-3, llama-2, etc.)
            settings: Nova settings (loads from YAML if not provided)
            verbose: Enable verbose output
        """
        self.settings = settings or NovaSettings()
        self.state = state
        self.telemetry = telemetry
        self.verbose = verbose
        
        # Determine LLM model
        self.llm_model = llm_model or self.settings.default_llm_model
        
        # Initialize tools
        if tools:
            self.tools = self._normalize_tools(tools)
        else:
            self.tools = self._create_default_tools()
        
        # Initialize the LLM
        self.llm = self._create_llm()
        
        # Create the agent
        self.agent = self._create_agent()
    
    def _normalize_tools(self, tools: List[Union[BaseTool, Tool]]) -> List[Tool]:
        """
        Normalize tools to ensure compatibility.
        
        Converts class-based tools to Tool instances if needed.
        """
        normalized = []
        
        for tool in tools:
            if isinstance(tool, BaseTool):
                # Convert BaseTool to Tool
                normalized.append(Tool(
                    name=tool.name,
                    func=tool._run,
                    description=tool.description
                ))
            elif isinstance(tool, Tool):
                normalized.append(tool)
            else:
                # Assume it's a function with tool decorator
                normalized.append(tool)
        
        return normalized
    
    def _create_default_tools(self) -> List[Tool]:
        """Create default tool set if none provided."""
        # Import unified tools module
        from nova.agent.unified_tools import create_default_tools
        from nova.tools.safety_limits import SafetyConfig
        
        # Determine repository path
        if self.state:
            repo_path = self.state.repo_path
        else:
            repo_path = Path(".")
        
        # Create tools using unified module
        tools = create_default_tools(
            repo_path=repo_path,
            verbose=self.verbose,
            safety_config=SafetyConfig(),
            llm=None  # Will use default GPT-4 in CriticReviewTool
        )
        
        # Convert to Tool instances if needed
        return self._normalize_tools(tools)
    
    def _create_llm(self):
        """Create the appropriate LLM based on model name."""
        model_lower = self.llm_model.lower()
        
        # OpenAI GPT models
        if "gpt" in model_lower:
            return ChatOpenAI(
                model=self.llm_model,
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_tokens
            )
        
        # Anthropic Claude models
        elif "claude" in model_lower and ChatAnthropic:
            return ChatAnthropic(
                model=self.llm_model,
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_tokens
            )
        
        # Llama models (local)
        elif "llama" in model_lower and HuggingFacePipeline:
            try:
                return HuggingFacePipeline.from_model_id(
                    model_id=self.llm_model,
                    task="text-generation",
                    model_kwargs={"temperature": self.settings.temperature}
                )
            except Exception as e:
                if self.verbose:
                    print(f"Failed to load Llama model: {e}, falling back to GPT-4")
                return ChatOpenAI(model="gpt-4", temperature=self.settings.temperature)
        
        # Default fallback
        else:
            if self.verbose:
                print(f"Unknown model {self.llm_model}, using GPT-4")
            return ChatOpenAI(model="gpt-4", temperature=self.settings.temperature)
    
    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain agent executor."""
        # Format system prompt with max iterations
        system_message = self.SYSTEM_PROMPT.format(
            max_iterations=self.state.max_iterations if self.state else 5
        )
        
        # Create agent with appropriate type
        agent_type = AgentType.OPENAI_FUNCTIONS if "gpt" in self.llm_model.lower() else AgentType.ZERO_SHOT_REACT_DESCRIPTION
        
        agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=agent_type,
            verbose=self.verbose,
            max_iterations=self.state.max_iterations * 3 if self.state else 15,
            max_execution_time=self.settings.timeout_seconds,
            handle_parsing_errors=True,
            agent_kwargs={"system_message": system_message} if agent_type == AgentType.OPENAI_FUNCTIONS else {}
        )
        
        return agent
    
    def run(
        self,
        failing_tests: Optional[str] = None,
        failures_summary: Optional[str] = None,
        error_details: Optional[str] = None
    ) -> bool:
        """
        Run the agent to fix failing tests.
        
        Args:
            failing_tests: Description of failing tests
            failures_summary: Summary table of failures
            error_details: Detailed error messages
            
        Returns:
            True if all tests were fixed, False otherwise
        """
        # Log start
        if self.telemetry:
            self.telemetry.log_event("deep_agent_start", {
                "model": self.llm_model,
                "tools": [t.name for t in self.tools],
                "max_iterations": self.state.max_iterations if self.state else 5
            })
        
        # Build prompt
        prompt_parts = []
        
        if failures_summary:
            prompt_parts.append(f"Failing Tests Summary:\n{failures_summary}")
        elif failing_tests:
            prompt_parts.append(f"Failing Tests:\n{failing_tests}")
        
        if error_details:
            prompt_parts.append(f"\nError Details:\n{error_details}")
        
        if not prompt_parts:
            prompt_parts.append("Please run tests to identify failures, then fix them.")
        
        prompt = "\n".join(prompt_parts)
        
        # Run the agent
        try:
            result = self.agent.run(prompt)
            
            # Check final test status
            success = self._check_success()
            
            # Update state
            if self.state:
                if success:
                    self.state.final_status = "success"
                    self.state.total_failures = 0
                elif self.state.current_iteration >= self.state.max_iterations:
                    self.state.final_status = "max_iterations"
                else:
                    self.state.final_status = "incomplete"
            
            # Log completion
            if self.telemetry:
                self.telemetry.log_event("deep_agent_complete", {
                    "success": success,
                    "iterations": self.state.current_iteration if self.state else 0,
                    "final_status": self.state.final_status if self.state else "unknown"
                })
            
            return success
            
        except Exception as e:
            # Log error
            if self.telemetry:
                self.telemetry.log_event("deep_agent_error", {
                    "error": str(e)
                })
            
            if self.state:
                self.state.final_status = "error"
            
            if self.verbose:
                print(f"Agent error: {e}")
            
            return False
    
    def _check_success(self) -> bool:
        """
        Check if all tests are passing.
        
        Returns:
            True if all tests pass, False otherwise
        """
        # Try to run tests to check status
        for tool in self.tools:
            if tool.name == "run_tests":
                try:
                    result = tool.func()
                    
                    # Parse result
                    if "FAILURES: 0" in result:
                        return True
                    elif isinstance(result, str):
                        # Try to parse as JSON
                        try:
                            data = json.loads(result)
                            if data.get("exit_code") == 0:
                                return True
                        except:
                            pass
                    
                    return False
                    
                except:
                    return False
        
        # If no test tool available, check state
        if self.state:
            return self.state.total_failures == 0
        
        return False
