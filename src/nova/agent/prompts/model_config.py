"""
Model Configuration for Nova Deep Agent
========================================

Flexible configuration for current and future LLM models including GPT-5.
"""

from typing import Dict, Any, Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field


class ModelProvider(str, Enum):
    """Supported model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    CUSTOM = "custom"


class ModelGeneration(str, Enum):
    """Model generations for configuration."""
    # Current models
    GPT_35_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_4O = "gpt-4o"
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    CLAUDE_35_SONNET = "claude-3.5-sonnet"
    
    # Future models (reserved)
    GPT_5 = "gpt-5"
    GPT_5_TURBO = "gpt-5-turbo"
    GPT_6 = "gpt-6"
    CLAUDE_4 = "claude-4"
    
    # Custom models
    CUSTOM = "custom"


class ModelCapabilities(BaseModel):
    """Capabilities and limits for different models."""
    
    max_tokens: int = Field(description="Maximum tokens in response")
    context_window: int = Field(description="Maximum context window size")
    supports_functions: bool = Field(default=True, description="Supports function calling")
    supports_json_mode: bool = Field(default=False, description="Supports JSON response format")
    supports_react: bool = Field(default=True, description="Can work with ReAct pattern")
    supports_tools: bool = Field(default=True, description="Supports tool use")
    temperature_range: tuple[float, float] = Field(default=(0.0, 2.0))
    
    # Future capabilities
    supports_multimodal: bool = Field(default=False, description="Supports images/audio")
    supports_code_execution: bool = Field(default=False, description="Can execute code directly")
    supports_web_browsing: bool = Field(default=False, description="Can browse web directly")
    supports_long_context: bool = Field(default=False, description="128K+ context window")


class ModelConfig(BaseModel):
    """Configuration for a specific model."""
    
    name: str = Field(description="Model identifier")
    provider: ModelProvider = Field(description="Model provider")
    generation: ModelGeneration = Field(description="Model generation")
    capabilities: ModelCapabilities = Field(description="Model capabilities")
    
    # Configuration parameters
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, description="Max response tokens")
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    
    # Advanced settings
    use_json_mode: bool = Field(default=False)
    use_react_pattern: bool = Field(default=False)
    reasoning_strategy: Literal["direct", "chain-of-thought", "react", "tree-of-thought"] = "direct"
    
    # Custom parameters for future models
    custom_params: Dict[str, Any] = Field(default_factory=dict)


# Model capability definitions
MODEL_CAPABILITIES: Dict[str, ModelCapabilities] = {
    # Current models
    "gpt-3.5-turbo": ModelCapabilities(
        max_tokens=4096,
        context_window=16385,
        supports_functions=True,
        supports_json_mode=True,
        supports_react=True
    ),
    
    "gpt-4": ModelCapabilities(
        max_tokens=8192,
        context_window=8192,
        supports_functions=True,
        supports_json_mode=True,
        supports_react=True
    ),
    
    "gpt-4-turbo-preview": ModelCapabilities(
        max_tokens=4096,
        context_window=128000,
        supports_functions=True,
        supports_json_mode=True,
        supports_react=True,
        supports_long_context=True
    ),
    
    "gpt-4o": ModelCapabilities(
        max_tokens=4096,
        context_window=128000,
        supports_functions=True,
        supports_json_mode=True,
        supports_react=True,
        supports_multimodal=True,
        supports_long_context=True
    ),
    
    "claude-3-opus": ModelCapabilities(
        max_tokens=4096,
        context_window=200000,
        supports_functions=True,
        supports_json_mode=False,
        supports_react=True,
        supports_long_context=True
    ),
    
    "claude-3.5-sonnet": ModelCapabilities(
        max_tokens=8192,
        context_window=200000,
        supports_functions=True,
        supports_json_mode=False,
        supports_react=True,
        supports_long_context=True
    ),
    
    # Future model projections (speculative)
    "gpt-5": ModelCapabilities(
        max_tokens=16384,
        context_window=256000,
        supports_functions=True,
        supports_json_mode=True,
        supports_react=True,
        supports_multimodal=True,
        supports_code_execution=True,
        supports_web_browsing=True,
        supports_long_context=True,
        temperature_range=(0.0, 3.0)
    ),
    
    "gpt-5-turbo": ModelCapabilities(
        max_tokens=8192,
        context_window=512000,
        supports_functions=True,
        supports_json_mode=True,
        supports_react=True,
        supports_multimodal=True,
        supports_code_execution=True,
        supports_web_browsing=True,
        supports_long_context=True,
        temperature_range=(0.0, 3.0)
    ),
    
    "gpt-6": ModelCapabilities(
        max_tokens=32768,
        context_window=1000000,
        supports_functions=True,
        supports_json_mode=True,
        supports_react=True,
        supports_multimodal=True,
        supports_code_execution=True,
        supports_web_browsing=True,
        supports_long_context=True,
        temperature_range=(0.0, 5.0)
    )
}


class ModelFactory:
    """Factory for creating model configurations."""
    
    @staticmethod
    def get_config(model_name: str, **overrides) -> ModelConfig:
        """
        Get configuration for a specific model.
        
        Args:
            model_name: Name of the model (e.g., "gpt-5")
            **overrides: Override default settings
            
        Returns:
            ModelConfig instance
        """
        # Determine provider from model name
        if "gpt" in model_name.lower():
            provider = ModelProvider.OPENAI
            generation = ModelGeneration(model_name) if model_name in ModelGeneration._value2member_map_ else ModelGeneration.CUSTOM
        elif "claude" in model_name.lower():
            provider = ModelProvider.ANTHROPIC
            generation = ModelGeneration(model_name) if model_name in ModelGeneration._value2member_map_ else ModelGeneration.CUSTOM
        else:
            provider = ModelProvider.CUSTOM
            generation = ModelGeneration.CUSTOM
        
        # Get capabilities
        capabilities = MODEL_CAPABILITIES.get(
            model_name,
            ModelCapabilities()  # Default capabilities
        )
        
        # Create config
        config = ModelConfig(
            name=model_name,
            provider=provider,
            generation=generation,
            capabilities=capabilities,
            **overrides
        )
        
        # Auto-set max_tokens if not specified
        if config.max_tokens is None:
            config.max_tokens = min(4096, capabilities.max_tokens)
        
        return config
    
    @staticmethod
    def create_llm(config: ModelConfig):
        """
        Create an LLM instance from config.
        
        Args:
            config: Model configuration
            
        Returns:
            LangChain LLM instance
        """
        if config.provider == ModelProvider.OPENAI:
            from langchain_openai import ChatOpenAI
            
            kwargs = {
                "model": config.name,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
            }
            
            if config.top_p is not None:
                kwargs["top_p"] = config.top_p
            if config.frequency_penalty is not None:
                kwargs["frequency_penalty"] = config.frequency_penalty
            if config.presence_penalty is not None:
                kwargs["presence_penalty"] = config.presence_penalty
            
            # Enable JSON mode if supported and requested
            if config.use_json_mode and config.capabilities.supports_json_mode:
                kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
            
            # Add custom parameters for future models
            if config.custom_params:
                kwargs.update(config.custom_params)
            
            return ChatOpenAI(**kwargs)
        
        elif config.provider == ModelProvider.ANTHROPIC:
            from langchain_anthropic import ChatAnthropic
            
            kwargs = {
                "model": config.name,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
            }
            
            if config.top_p is not None:
                kwargs["top_p"] = config.top_p
            
            # Add custom parameters
            if config.custom_params:
                kwargs.update(config.custom_params)
            
            return ChatAnthropic(**kwargs)
        
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")


def get_optimal_model_for_task(
    task_type: Literal["simple_fix", "complex_fix", "multi_file", "refactoring"],
    prefer_fast: bool = False,
    require_long_context: bool = False,
    require_json: bool = False,
    future_models_enabled: bool = True
) -> str:
    """
    Get the optimal model for a specific task type.
    
    Args:
        task_type: Type of task to perform
        prefer_fast: Prefer faster/cheaper models
        require_long_context: Need 128K+ context
        require_json: Need JSON mode support
        future_models_enabled: Allow future models like GPT-5
        
    Returns:
        Model name string
    """
    # If GPT-5 is available and enabled, prefer it for complex tasks
    if future_models_enabled and task_type in ["complex_fix", "multi_file", "refactoring"]:
        # Check if GPT-5 is actually available (would need runtime check)
        return "gpt-5"
    
    # For simple fixes, use efficient models
    if task_type == "simple_fix" and prefer_fast:
        return "gpt-3.5-turbo" if require_json else "claude-3.5-sonnet"
    
    # For complex fixes requiring long context
    if require_long_context:
        return "gpt-4-turbo-preview" if require_json else "claude-3-opus"
    
    # Default to GPT-4 for reliability
    return "gpt-4"
