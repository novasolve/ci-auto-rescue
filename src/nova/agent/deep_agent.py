"""
Nova Deep Agent Implementation
===============================
Orchestrator agent that uses LangChain's AgentExecutor to fix failing tests with minimal changes.
Utilizes a ReAct loop with tools: run_tests, apply_patch, critic_review.
"""

from typing import Optional, Any
from pathlib import Path

from langchain.agents import AgentExecutor, Tool, initialize_agent, AgentType
from langchain.agents.react.output_parser import ReActOutputParser
from langchain.schema import AgentAction, AgentFinish
from typing import Union
import re
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

# Custom wrapper for GPT-5 that removes unsupported parameters
class GPT5ChatOpenAI(ChatOpenAI):
    """Custom ChatOpenAI wrapper for GPT-5 that filters out unsupported parameters."""
    
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        """Override to remove stop parameter for GPT-5."""
        # GPT-5 doesn't support stop sequences, so remove them
        if stop is not None:
            kwargs.pop('stop', None)
        return super()._generate(messages, stop=None, run_manager=run_manager, **kwargs)


# Module-level storage for parser states to avoid Pydantic field issues
_parser_agent_states = {}

# Custom output parser for GPT-5 that handles both action and final answer in same output
class GPT5ReActOutputParser(ReActOutputParser):
    """Custom ReAct output parser that handles GPT-5's tendency to output both actions and final answers."""
    
    def __init__(self, agent_state=None):
        """Initialize parser with optional agent state for context-aware decisions."""
        super().__init__()
        # Store state using instance id as key to avoid Pydantic field validation
        if agent_state is not None:
            _parser_agent_states[id(self)] = agent_state
    
    @property
    def agent_state(self):
        """Get agent state from module-level storage."""
        return _parser_agent_states.get(id(self), None)
    
    def __del__(self):
        """Clean up state storage when parser is destroyed."""
        instance_id = id(self)
        if instance_id in _parser_agent_states:
            del _parser_agent_states[instance_id]
    
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        """Parse GPT-5 output, prioritizing actions over final answers."""
        text_lower = text.lower()
        
        # First check agent state if available (more reliable than text parsing)
        if self.agent_state:
            # Check if tests are passing based on agent state
            tests_passing = getattr(self.agent_state, 'total_failures', 1) == 0
            phase = getattr(self.agent_state, 'phase', 'unknown')
            
            # If we have a Final Answer and tests are passing, allow it
            if "final answer" in text_lower and tests_passing:
                final_answer_match = re.search(
                    r"Final\s*Answer\s*:\s*(.+?)(?=\n(?:Action:|Observation:|Thought:)|$)", 
                    text, 
                    re.DOTALL | re.IGNORECASE
                )
                if final_answer_match:
                    answer_text = final_answer_match.group(1).strip()
                    if hasattr(self.agent_state, 'verbose') and self.agent_state.verbose:
                        print(f"[Parser] Allowing Final Answer - tests passing (failures={self.agent_state.total_failures})")
                    return AgentFinish(
                        return_values={"output": answer_text}, 
                        log=text
                    )
        
        # Fallback to text-based success detection
        success_terms = ["all tests passing", "all tests pass", "0 failures", "successfully fixed", "tests passed"]
        has_success = any(term in text_lower for term in success_terms)
        
        # If tests are passing and agent provides Final Answer, allow completion
        if has_success:
            final_answer_match = re.search(
                r"Final\s*Answer\s*:\s*(.+?)(?=\n(?:Action:|Observation:|Thought:)|$)", 
                text, 
                re.DOTALL | re.IGNORECASE
            )
            if final_answer_match:
                answer_text = final_answer_match.group(1).strip()
                return AgentFinish(
                    return_values={"output": answer_text}, 
                    log=text
                )
        
        # Special handling for plan_todo responses that try to end prematurely
        # Check if output contains planning keywords AND a premature final answer
        if ("plan noted" in text_lower or "todo created" in text_lower or "plan recorded" in text_lower):
            # Check if agent is trying to provide a final answer after planning
            phase = getattr(self.agent_state, 'phase', 'planning') if self.agent_state else 'planning'
            tests_passing = getattr(self.agent_state, 'total_failures', 1) == 0 if self.agent_state else has_success
            
            if "final answer" in text_lower and not tests_passing and phase != 'complete':
                # Log the intervention
                if self.agent_state and hasattr(self.agent_state, 'verbose') and self.agent_state.verbose:
                    print(f"[Parser] Blocked premature Final Answer - phase={phase}, failures={getattr(self.agent_state, 'total_failures', '?')}")
                
                # Instead of forcing a specific file, just indicate continuation is needed
                # Let the agent figure out the next action naturally
                return AgentAction(
                    tool="run_tests",
                    tool_input={},
                    log=text + "\n[Parser: Detected premature completion after planning. Checking test status.]"
                )
        
        # First check if there's a valid action in the output
        action_match = re.search(
            r"Action\s*:\s*([^\n]+)\s*\n\s*Action\s*Input\s*:\s*(.+?)(?=\n|$)", 
            text, 
            re.DOTALL
        )
        
        if action_match:
            # If we found an action, use it even if there's also a final answer
            action = action_match.group(1).strip()
            action_input = action_match.group(2).strip()
            
            # Clean up action input if it's multiline
            if '\n' in action_input:
                # For multiline inputs, take everything until we see "Observation:" or "Final Answer:"
                cutoff_match = re.search(r'(Observation:|Final Answer:)', action_input)
                if cutoff_match:
                    action_input = action_input[:cutoff_match.start()].strip()
            
            return AgentAction(tool=action, tool_input=action_input, log=text)
        
        # If no action found, check for final answer
        final_answer_match = re.search(
            r"Final\s*Answer\s*:\s*(.+?)(?=\n(?:Action:|Observation:|Thought:)|$)", 
            text, 
            re.DOTALL | re.IGNORECASE
        )
        
        if final_answer_match:
            # Check if this is a premature final answer after planning
            answer_text = final_answer_match.group(1).strip()
            # Only block "permission-seeking" answers if we're not in success state
            if not has_success and any(phrase in answer_text.lower() for phrase in ["i will", "i need to", "to proceed", "please allow", "i should"]):
                # This looks like the agent asking for permission rather than completing
                return AgentAction(
                    tool="run_tests",
                    tool_input={},
                    log=text + "\n[Parser: Agent seems stuck - checking test status]"
                )
            
            return AgentFinish(
                return_values={"output": answer_text}, 
                log=text
            )
        
        # If neither found, try the parent parser
        try:
            return super().parse(text)
        except Exception:
            # If all else fails, guide the agent to continue
            return AgentAction(
                tool="run_tests",
                tool_input={},
                log=text + "\n[Parser: No clear action found - running tests to check status]"
            )

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
        # Choose LLM based on configuration (supports OpenAI GPT or Anthropic Claude)
        model_name = getattr(self.settings, 'default_llm_model', 'gpt-4')
        
        # Smart model selection based on available API keys
        openai_key = self.settings.openai_api_key
        anthropic_key = self.settings.anthropic_api_key
        
        # Only apply smart selection if using a default/generic model name
        if model_name in ["gpt-4", "gpt-3.5-turbo", "gpt-5", None, ""]:
            if openai_key and not anthropic_key:
                # Only OpenAI key available
                if model_name not in ["gpt-4", "gpt-3.5-turbo", "gpt-5"]:
                    model_name = "gpt-4"
                if self.verbose:
                    print(f"🔑 Using OpenAI model (only OpenAI key available)")
            elif anthropic_key and not openai_key:
                # Only Anthropic key available
                model_name = "claude-3-opus"
                if self.verbose:
                    print(f"🔑 Using Anthropic model (only Anthropic key available)")
            elif anthropic_key and openai_key:
                # Both keys available - use configured default
                if self.verbose:
                    print(f"🔑 Both API keys available, using configured model")
            else:
                # No keys available
                if self.verbose:
                    print(f"⚠️ No API keys found - please set OPENAI_API_KEY or ANTHROPIC_API_KEY")
        
        # Show what model was selected
        if self.verbose:
            print(f"📋 Selected model: {model_name}")
        
        # Map the model name using LLMClient logic
        from nova.agent.llm_client import LLMClient
        temp_client = LLMClient(settings=self.settings)
        mapped_model = temp_client._get_openai_model_name()
        
        if mapped_model != model_name and self.verbose:
            print(f"📄 Mapped to: {mapped_model}")
        
        use_react = False
        
        # Check if this is GPT-5 (which doesn't support function calling or stop sequences)
        if model_name.lower().startswith("gpt-5"):
            # GPT-5 must use ReAct mode (no function calling) and custom wrapper
            try:
                llm = GPT5ChatOpenAI(model_name=mapped_model, temperature=0)
                use_react = True  # Force ReAct for GPT-5
                if self.verbose:
                    print(f"🚀 Using model '{mapped_model}' with ReAct agent (GPT-5 mode, no stop sequences)")
            except Exception as e:
                # Fallback to GPT-4 with function calling
                fallback_model = "gpt-4-0613"
                if self.verbose:
                    print(f"⚠️ Model {mapped_model} not available ({e}), falling back to {fallback_model}")
                llm = ChatOpenAI(model_name=fallback_model, temperature=0)
                use_react = False
                if self.verbose:
                    print(f"🚀 Using OpenAI model '{fallback_model}' with function calling (fallback)")
        # If an Anthropic model (Claude) is requested and available, use it with ReAct mode (no function calling)
        elif ChatAnthropic and model_name.lower().startswith("claude"):
            try:
                llm = ChatAnthropic(model=model_name, temperature=0)
                use_react = True
                if self.verbose:
                    print(f"🚀 Using Anthropic model '{model_name}' with ReAct agent")
            except Exception as e:
                if self.verbose:
                    print(f"⚠️ Anthropic model {model_name} not available ({e}), falling back to GPT-4")
                llm = ChatOpenAI(model_name="gpt-4", temperature=0)
                use_react = False
                if self.verbose:
                    print(f"🚀 Using OpenAI model 'gpt-4' with function calling (fallback)")
        else:
            # Otherwise, use OpenAI Chat model (GPT) with function calling by default
            try:
                llm = ChatOpenAI(model_name=mapped_model, temperature=0)
                use_react = False
                if self.verbose:
                    print(f"🚀 Using OpenAI model '{mapped_model}' with function calling")
            except Exception as e:
                # Use GPT-4-0613 for fallback (supports function calling)
                fallback_model = "gpt-4-0613"
                if self.verbose:
                    print(f"⚠️ Model {mapped_model} not available ({e}), falling back to {fallback_model}")
                llm = ChatOpenAI(model_name=fallback_model, temperature=0)
                use_react = False
                if self.verbose:
                    print(f"🚀 Using OpenAI model '{fallback_model}' with function calling (fallback)")
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
            "3. **NO HALLUCINATING**: Never make things up\n"
            "   - Available tools: plan_todo, open_file, write_file, run_tests, apply_patch, critic_review\n"
            "   - Never invent or reference non-existent tools\n"
            "   - When you get 'ERROR: Access blocked', DO NOT imagine file contents\n"
            "   - If you can't read a file, work with what you have\n"
            "   - CRITICAL: Do NOT generate 'Observation:' lines - wait for actual tool responses\n"
            "   - After 'Action Input:', STOP and wait for the tool to run\n\n"
            "4. **SAFETY GUARDRAILS**: Respect all safety limits\n"
            "   - Max patch size: 500 lines\n"
            "   - Max files per patch: 10\n"
            "   - Never modify: .env, .git/, secrets/, .github/, CI/CD configs\n\n"
            "5. **VALID PATCHES ONLY**: Ensure all patches are syntactically valid\n"
            "   - Preserve indentation (spaces vs tabs)\n"
            "   - Maintain code style consistency\n"
            "   - Ensure no syntax errors introduced\n\n"
            "6. **PYTHON IMPORTS**: When resolving Python imports:\n"
            "   - Check test files for sys.path modifications (e.g., sys.path.insert)\n"
            "   - If tests import 'from module_name import ...', look for:\n"
            "     * module_name.py in the same directory\n"
            "     * module_name.py in directories added to sys.path\n"
            "     * module_name/__init__.py for packages\n"
            "   - Common patterns: src/module_name.py, lib/module_name.py\n"
            "   - NEVER guess filenames like 'module_name_module.py' or 'broken_module.py'\n\n"
            "## YOUR WORKFLOW - DETERMINISTIC MULTI-FAILURE FIX:\n"
            "1. ANALYZE: Understand ALL failing tests and their error messages\n"
            "2. INVESTIGATE: Read ALL relevant source files for failing functions\n"
            "3. PLAN: Create a comprehensive strategy to fix ALL failures at once\n"
            "4. IMPLEMENT ALL FIXES: Apply fixes for EVERY failing test sequentially\n"
            "5. VERIFY ONCE: Run tests only AFTER all fixes are applied\n"
            "6. ITERATE: Only if some tests still fail after the complete fix\n\n"
            "CRITICAL - FIX ALL FAILURES IN ONE CYCLE:\n"
            "- DO NOT fix issues one-by-one with tests after each fix\n"
            "- DO NOT run tests until ALL fixes are implemented\n"
            "- Your plan should enumerate a fix for EACH failing function\n"
            "- Apply ALL fixes before calling run_tests\n"
            "- Example: If 5 functions fail, fix all 5, then test once\n\n"
            "IMPLEMENTATION ORDER:\n"
            "1. Run tests once to see all failures\n"
            "2. Use plan_todo to list fixes for EACH failing function\n"
            "3. For each planned fix:\n"
            "   - Open the source file\n"
            "   - Apply the fix\n"
            "   - Move to the next fix WITHOUT testing\n"
            "4. Only after ALL fixes are done, run tests to verify\n"
            "5. If any tests still fail, repeat with remaining issues\n\n"
            "Remember: Your goal is to make ALL tests pass in ONE iteration with MINIMAL changes."
        )
        # Create the tool set (unified tools with safety and testing integrated)
        tools = create_default_tools(
            repo_path=self.state.repo_path,
            verbose=self.verbose,
            safety_config=self.safety_config,
            llm=llm,  # Pass LLM for critic review
            state=self.state,  # Pass agent state for review tracking
            settings=self.settings  # Pass settings for configuration
        )
        
        # Choose agent type based on model capabilities
        from langchain.agents import AgentType
        
        # Define custom parsing error handler for better error recovery
        def parsing_error_handler(error) -> str:
            """Handle parsing errors gracefully."""
            error_str = str(error).lower()
            if "both a final answer and a parse-able action" in error_str:
                # Extract any final answer from the error if possible
                return "I've completed the task. All tests are now passing."
            return "I need to reformat my response. Let me try again."
        
        if use_react:
            # For models that don't support function calling (e.g., Claude, GPT-5)
            # Check if this is GPT-5 which needs special handling
            if isinstance(llm, GPT5ChatOpenAI):
                # GPT-5 needs special handling - convert multi-input tools to single JSON input
                import json
                from langchain.tools import Tool
                
                # For GPT-5, we need to wrap all multi-input tools
                wrapped_tools = []
                
                for tool in tools:
                    # Check if this is a multi-input tool
                    if hasattr(tool, 'args_schema') and tool.args_schema and hasattr(tool.args_schema, '__fields__'):
                        fields = tool.args_schema.__fields__
                        if len(fields) > 1:
                            # This is a multi-input tool, create a JSON wrapper
                            original_tool = tool
                            tool_name = tool.name
                            tool_desc = tool.description
                            
                            # Get field descriptions
                            field_info = {}
                            for field_name, field_obj in fields.items():
                                # Extract field information from Pydantic ModelField
                                try:
                                    # Try to get the field type
                                    if hasattr(field_obj, 'type_'):
                                        field_type = str(field_obj.type_)
                                    elif hasattr(field_obj, 'annotation'):
                                        field_type = str(field_obj.annotation)
                                    else:
                                        field_type = "str"  # Default to string
                                    
                                    # Try to get required status
                                    is_required = True  # Default to required
                                    
                                    # Check for Optional types
                                    if hasattr(field_obj, 'type_'):
                                        type_str = str(field_obj.type_)
                                        if 'Optional' in type_str or 'Union[' in type_str and 'None' in type_str:
                                            is_required = False
                                    
                                    # Check for default values
                                    if hasattr(field_obj, 'default'):
                                        # In Pydantic, ... (Ellipsis) means required
                                        # Check if default is NOT Ellipsis and NOT UndefinedType
                                        default_str = str(field_obj.default)
                                        if (field_obj.default is not ... and 
                                            'Ellipsis' not in default_str and
                                            'UndefinedType' not in default_str):
                                            is_required = False
                                    
                                    # Override with explicit required attribute if present
                                    if hasattr(field_obj, 'required'):
                                        is_required = field_obj.required
                                    
                                    # Try to get description
                                    description = ""
                                    if hasattr(field_obj, 'field_info') and hasattr(field_obj.field_info, 'description'):
                                        description = field_obj.field_info.description or ""
                                    elif hasattr(field_obj, 'description'):
                                        description = field_obj.description or ""
                                    
                                    field_info[field_name] = {
                                        'type': field_type,
                                        'required': is_required,
                                        'description': description
                                    }
                                except Exception:
                                    # Fallback for any field we can't introspect
                                    field_info[field_name] = {
                                        'type': 'str',
                                        'required': True,
                                        'description': ''
                                    }
                            
                            def make_json_wrapper(t, name, fields_info):
                                def wrapper(input_str: str) -> str:
                                    try:
                                        if not input_str.strip().startswith('{'):
                                            return f"ERROR: Input must be JSON format with fields: {list(fields_info.keys())}"
                                        
                                        data = json.loads(input_str)
                                        
                                        # Validate required fields
                                        for field_name, info in fields_info.items():
                                            if info['required'] and field_name not in data:
                                                return f"ERROR: Missing required field '{field_name}'"
                                        
                                        # Call the tool with the parsed data
                                        return t._run(**data)
                                    except json.JSONDecodeError as e:
                                        return f"ERROR: Invalid JSON: {e}"
                                    except Exception as e:
                                        return f"ERROR: {str(e)}"
                                return wrapper
                            
                            # Create description with field info
                            json_desc = f"{tool_desc} Input must be JSON with fields: "
                            field_descs = []
                            for fname, finfo in field_info.items():
                                req = "required" if finfo['required'] else "optional"
                                desc = f"'{fname}' ({req})"
                                if finfo['description']:
                                    desc += f": {finfo['description']}"
                                field_descs.append(desc)
                            json_desc += ", ".join(field_descs)
                            
                            wrapped_tool = Tool(
                                name=tool_name,
                                func=make_json_wrapper(original_tool, tool_name, field_info),
                                description=json_desc
                            )
                            wrapped_tools.append(wrapped_tool)
                        else:
                            # Single input tool, keep as-is
                            wrapped_tools.append(tool)
                    else:
                        # No schema info, keep as-is
                        wrapped_tools.append(tool)
                
                # Use ZERO_SHOT_REACT_DESCRIPTION with wrapped tools and custom parser
                agent_executor = initialize_agent(
                    tools=wrapped_tools,
                    llm=llm,
                    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                    verbose=self.verbose,
                    handle_parsing_errors=parsing_error_handler,
                    max_iterations=self.settings.agent_max_iterations,
                    early_stopping_method="generate",
                    agent_kwargs={
                        "prefix": system_message + "\n\nYou have access to the following tools:",
                        "suffix": "Begin!\n\nIMPORTANT: Generate ONLY 'Thought:', 'Action:', and 'Action Input:'. Do NOT generate 'Observation:' - the system will provide real observations after running your action.\n\nQuestion: {input}\nThought: I should start by understanding what needs to be fixed.\n{agent_scratchpad}",
                        "output_parser": GPT5ReActOutputParser(agent_state=self.state),
                        "handle_parsing_errors": "Check your output and ensure it follows the correct format. Use EITHER 'Action:' followed by 'Action Input:' OR 'Final Answer:', but not both in the same response."
                    }
                )
            else:
                # For other models (Claude), use structured ReAct
                agent_executor = initialize_agent(
                    tools=tools,
                    llm=llm,
                    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
                    verbose=self.verbose,
                    handle_parsing_errors=parsing_error_handler,
                    max_iterations=self.settings.agent_max_iterations,
                    early_stopping_method="generate",
                    agent_kwargs={
                        "prefix": system_message + "\n\nYou have access to the following tools:"
                    }
                )
        else:
            # For OpenAI models that support function calling (GPT-3.5, GPT-4, GPT-5, etc.)
            agent_executor = initialize_agent(
                tools=tools,
                llm=llm,
                agent=AgentType.OPENAI_FUNCTIONS,
                verbose=self.verbose,
                agent_kwargs={"system_message": system_message},
                handle_parsing_errors=parsing_error_handler,
                max_iterations=self.settings.agent_max_iterations
            )
        
        # Log final model selection for transparency
        if self.verbose:
            try:
                actual_model_name = llm.model_name if hasattr(llm, 'model_name') else str(llm)
                mode = "ReAct (text-based)" if use_react else "OpenAI Functions"
                print(f"\n🤖 Final model configuration:")
                print(f"   Model: {actual_model_name}")
                print(f"   Mode: {mode}")
                print(f"   Temperature: 0")
                print("")
            except Exception:
                pass  # Don't fail if logging doesn't work
        
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
        
        # Check for hint file and include in prompt if found
        hint_content = ""
        hint_files = [".nova-hints", ".nova/hints.md", "HINTS.md"]
        for hint_file in hint_files:
            hint_path = self.state.repo_path / hint_file
            if hint_path.exists():
                try:
                    hint_text = hint_path.read_text()
                    hint_content = f"\n## PROJECT HINTS (from {hint_file}):\n{hint_text}\n"
                    if self.verbose:
                        print(f"📝 Found hint file: {hint_file}")
                    self.telemetry.log_event("hint_file_found", {
                        "file": hint_file,
                        "size": len(hint_text)
                    })
                    break
                except Exception as e:
                    if self.verbose:
                        print(f"⚠️ Could not read hint file {hint_file}: {e}")
        
        # Prepare a comprehensive user prompt with failing test details and structured instructions
        user_prompt = f"""Fix the following failing tests:

## FAILURES SUMMARY:
{failures_summary}

## ERROR DETAILS (Stack traces and messages):
{error_details}

{f"## RELEVANT CODE SNIPPETS:\n{code_snippets}" if code_snippets else ""}
{hint_content}
## YOUR TASK:
Use the available tools to fix the failing tests. You MUST follow these steps IN ORDER:

STEP 1: Look at the test file path (e.g., test_broken.py) and identify the likely source file
   - If test is "test_broken.py", source is likely "broken.py" 
   - Use the hint above if provided

STEP 2: IMMEDIATELY try to open the source file with 'open_file'
   - First try: broken.py (if that's the module name)
   - If "File not found", it will suggest alternatives like src/broken.py
   - Follow the suggestions and try again

STEP 3: Once you find and open the source file:
   - Identify the failing functions from the error messages
   - Fix them based on the test expectations
   - Use 'write_file' or 'apply_patch'

STEP 4: Run tests again to verify

## CRITICAL RULES:
- DO NOT give up after running tests - you MUST try to open source files
- DO NOT say "I need access to files" - just try to open them!
- When you see "ERROR: Access blocked", that means it's a test file - try the source file instead
- The source files ARE accessible, you just need to find the right path
- Common patterns: module.py, src/module.py, lib/module.py

Start NOW by trying to open the source file. DO NOT just run tests again!"""
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
                result = self.agent.invoke({"input": user_prompt})
            except Exception as e:
                # Runtime fallback for GPT-5 to GPT-4 if function calling issues occur
                error_msg = str(e).lower()
                model_name = getattr(self.settings, 'default_llm_model', '').lower()
                
                if (("function" in error_msg or "unsupported value" in error_msg or "does not support" in error_msg or 
                     "unsupported parameter" in error_msg or "'stop' is not supported" in error_msg) and 
                    (model_name.startswith("gpt-5") or model_name in ["gpt-5-turbo", "gpt-5-preview"])):
                    if self.verbose:
                        print(f"\n⚠️ {self.settings.default_llm_model} runtime error: {e}")
                        print("🔄 Falling back to GPT-4-0613 with function calling...")
                    
                    # Update settings and rebuild agent with GPT-4 (function-call enabled version)
                    original_model = self.settings.default_llm_model
                    self.settings.default_llm_model = "gpt-4-0613"
                    self.agent = self._build_agent()
                    
                    # Retry with GPT-4
                    try:
                        result = self.agent.invoke({"input": user_prompt})
                        if self.verbose:
                            print("✅ Successfully recovered with GPT-4-0613")
                    finally:
                        # Restore original model setting
                        self.settings.default_llm_model = original_model
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
                # Log structured success event (OS-1182)
                self.telemetry.log_event("deep_agent_success", {
                    "event": "run_complete",
                    "success": True,
                    "iterations": self.state.current_iteration,
                    "message": "All tests passing",
                    "tests_passed": final_test_output.get("passed", "unknown")
                })
            else:
                # Tests still failing or result unknown
                failures_count = final_test_output.get("failures", "unknown") if final_test_output else "unknown"
                
                # Determine appropriate final status
                if not self.state.patches_applied:
                    # No patches were applied at all
                    if hasattr(self.state, 'critic_feedback') and self.state.critic_feedback:
                        # Patches were rejected by critic
                        self.state.final_status = "patch_rejected"
                    else:
                        # No patches could be generated
                        self.state.final_status = "no_patch"
                elif self.state.current_iteration >= self.state.max_iterations:
                    self.state.final_status = "max_iters"
                else:
                    self.state.final_status = "incomplete"
                
                # Log structured failure event (OS-1182)
                failure_event = {
                    "event": "run_complete",
                    "success": False,
                    "failure_type": self.state.final_status,
                    "iterations": self.state.current_iteration,
                    "remaining_failures": failures_count,
                    "error": final_test_output.get("error") if final_test_output else None
                }
                
                # Add failure reason for transparency
                if self.state.final_status == "max_iters":
                    failure_event["failure_reason"] = f"Reached max {self.state.max_iterations} iterations with {failures_count} tests still failing."
                elif self.state.final_status == "patch_rejected":
                    failure_event["failure_reason"] = "All proposed patches were rejected by safety checks."
                elif self.state.final_status == "no_patch":
                    failure_event["failure_reason"] = "Could not generate a valid patch for the failing tests."
                    
                self.telemetry.log_event("deep_agent_incomplete", failure_event)
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
            
            # Store error message in state for reporting
            self.state.error_message = err_msg
            
            # Mark appropriate final status on error
            if "max iterations" in err_msg.lower():
                self.state.final_status = "max_iters"
            else:
                self.state.final_status = "error"
            success = False
        return success