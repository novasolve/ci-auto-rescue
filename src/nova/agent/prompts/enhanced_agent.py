"""
Enhanced Deep Agent with Structured Prompts
============================================

Integration of structured prompts, output parsing, and validation into Deep Agent.
"""

from typing import Optional, Dict, Any, List
import json

from langchain.agents import AgentExecutor, initialize_agent, AgentType
from langchain.schema import BaseMessage, SystemMessage
from langchain.callbacks import StdOutCallbackHandler
from langchain_openai import ChatOpenAI

from .system_prompt import NovaSystemPrompt, ResponseFormat
from .output_parser import AgentOutputParser
from nova.agent.unified_tools import create_default_tools
from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger


class EnhancedDeepAgent:
    """
    Deep Agent with enhanced prompting, structured outputs, and validation.
    """
    
    def __init__(
        self,
        state: AgentState,
        telemetry: Optional[JSONLLogger] = None,
        verbose: bool = False,
        use_structured_output: bool = True
    ):
        """
        Initialize enhanced deep agent.
        
        Args:
            state: Agent state for tracking
            telemetry: Optional telemetry logger
            verbose: Enable verbose output
            use_structured_output: Whether to enforce structured JSON outputs
        """
        self.state = state
        self.telemetry = telemetry
        self.verbose = verbose
        self.use_structured_output = use_structured_output
        
        # Initialize components
        self.parser = AgentOutputParser()
        self.system_prompt = NovaSystemPrompt.get_full_prompt()
        
        # Initialize LLM with JSON mode if needed
        self.llm = self._create_llm()
        
        # Create agent with enhanced prompt
        self.agent = self._create_agent()
    
    def _create_llm(self):
        """Create LLM with appropriate configuration."""
        config = {
            "temperature": 0.1,
            "max_tokens": 4000
        }
        
        if self.use_structured_output:
            # Use JSON mode for structured outputs
            config["model_kwargs"] = {"response_format": {"type": "json_object"}}
        
        return ChatOpenAI(model="gpt-4", **config)
    
    def _create_agent(self) -> AgentExecutor:
        """Create agent with enhanced system prompt and tools."""
        tools = create_default_tools(
            repo_path=self.state.repo_path,
            verbose=self.verbose
        )
        
        # Add validation wrapper to tools
        wrapped_tools = self._wrap_tools_with_validation(tools)
        
        agent = initialize_agent(
            tools=wrapped_tools,
            llm=self.llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=self.verbose,
            agent_kwargs={"system_message": self.system_prompt},
            callbacks=[EnhancedCallback(self.parser)] if self.verbose else []
        )
        
        return agent
    
    def _wrap_tools_with_validation(self, tools: List) -> List:
        """Wrap tools with validation logic."""
        wrapped = []
        
        for tool in tools:
            original_func = tool.func
            
            def validated_func(input_str: str, _original=original_func, _name=tool.name):
                """Wrapper that validates tool inputs/outputs."""
                # Pre-validation
                if _name == "write_file":
                    # Check for test file modification attempt
                    if "test" in input_str.lower():
                        return "ERROR: Cannot modify test files (CORE RULE #1)"
                
                if _name == "apply_patch":
                    # Validate patch before applying
                    is_valid, error = self.parser.validate_patch(input_str)
                    if not is_valid:
                        return f"ERROR: Invalid patch - {error}"
                
                # Execute original function
                result = _original(input_str)
                
                # Post-validation and parsing
                parsed_response = self.parser.parse_tool_response(_name, result)
                
                # Log to telemetry
                if self.telemetry:
                    self.telemetry.log_event("tool_execution", {
                        "tool": _name,
                        "success": parsed_response.success,
                        "error": parsed_response.error
                    })
                
                return result
            
            tool.func = validated_func
            wrapped.append(tool)
        
        return wrapped
    
    def run(
        self,
        failures_summary: str,
        error_details: str,
        code_snippets: str = ""
    ) -> bool:
        """
        Run the enhanced agent to fix failing tests.
        
        Args:
            failures_summary: Summary of failing tests
            error_details: Detailed error messages
            code_snippets: Optional relevant code
            
        Returns:
            True if all tests pass, False otherwise
        """
        # Format input with structured prompt
        if self.use_structured_output:
            user_input = f"""
Fix the following failing tests. Provide your response in JSON format:

FAILURES:
{failures_summary}

ERRORS:
{error_details}

{code_snippets}

Remember to follow all core rules and provide structured responses.
"""
        else:
            user_input = f"""
Fix the following failing tests:

{failures_summary}

Error details:
{error_details}

{code_snippets}
"""
        
        try:
            # Run the agent
            result = self.agent.run(user_input)
            
            # Parse structured response if enabled
            if self.use_structured_output:
                parsed = self.parser.parse_json_response(result)
                if parsed:
                    if self.verbose:
                        print(f"Reasoning: {parsed.reasoning}")
                        print(f"Confidence: {parsed.confidence}")
                        print(f"Planned changes: {parsed.planned_changes}")
                    
                    # Log structured response
                    if self.telemetry:
                        self.telemetry.log_event("structured_response", {
                            "confidence": parsed.confidence,
                            "changes_count": len(parsed.planned_changes),
                            "has_risks": len(parsed.risks) > 0
                        })
            
            # Check if tests pass
            return self._check_tests_pass()
            
        except Exception as e:
            if self.telemetry:
                self.telemetry.log_event("agent_error", {"error": str(e)})
            return False
    
    def _check_tests_pass(self) -> bool:
        """Check if all tests are passing."""
        from nova.runner import TestRunner
        runner = TestRunner(self.state.repo_path)
        failing_tests, _ = runner.run_tests()
        return len(failing_tests) == 0


class EnhancedCallback(StdOutCallbackHandler):
    """Enhanced callback for parsing and validating agent outputs."""
    
    def __init__(self, parser: AgentOutputParser):
        super().__init__()
        self.parser = parser
    
    def on_llm_end(self, response, **kwargs):
        """Parse and validate LLM responses."""
        if response.generations:
            text = response.generations[0][0].text
            
            # Try to parse structured response
            parsed = self.parser.parse_json_response(text)
            if parsed:
                print(f"\n[Structured Response Detected]")
                print(f"  Confidence: {parsed.confidence}")
                print(f"  Changes: {len(parsed.planned_changes)}")
            
            # Check for tool hallucination
            tool_calls = self.parser.extract_tool_calls(text)
            for call in tool_calls:
                known_tools = ['open_file', 'write_file', 'run_tests', 'apply_patch', 'critic_review']
                if call['name'] not in known_tools:
                    print(f"\n⚠️ WARNING: Hallucinated tool detected: {call['name']}")


def upgrade_existing_agent(
    existing_agent: Any,
    use_enhanced_prompts: bool = True,
    use_structured_output: bool = True
) -> Any:
    """
    Upgrade an existing Deep Agent with enhanced capabilities.
    
    Args:
        existing_agent: The existing agent to upgrade
        use_enhanced_prompts: Whether to use enhanced prompts
        use_structured_output: Whether to enforce structured outputs
        
    Returns:
        Upgraded agent
    """
    if use_enhanced_prompts:
        # Replace system message with enhanced prompt
        enhanced_prompt = NovaSystemPrompt.get_full_prompt()
        
        if hasattr(existing_agent, 'agent'):
            # LangChain agent
            if hasattr(existing_agent.agent, 'llm_chain'):
                existing_agent.agent.llm_chain.prompt.messages[0] = SystemMessage(
                    content=enhanced_prompt
                )
        
        # Add parser
        existing_agent.parser = AgentOutputParser()
    
    if use_structured_output:
        # Enable JSON mode if using OpenAI
        if hasattr(existing_agent, 'llm'):
            existing_agent.llm.model_kwargs = {"response_format": {"type": "json_object"}}
    
    return existing_agent
