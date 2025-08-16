"""Configuration for the Nova Deep Agent."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentConfig:
    """Configuration for the Nova Deep Agent."""
    
    # Model configuration
    model_name: str = "gpt-4"
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    
    # Agent behavior
    verbose: bool = True
    max_iterations: int = 10
    max_execution_time: Optional[float] = 600.0  # 10 minutes
    
    # Safety limits
    max_patch_lines: int = 1000
    max_affected_files: int = 10
    max_file_size: int = 100_000  # 100KB
    
    # Tool configuration
    enable_planning: bool = True
    enable_file_access: bool = True
    enable_testing: bool = True
    
    # System prompt customization
    system_prompt: Optional[str] = None
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> "AgentConfig":
        """Create config from dictionary."""
        return cls(**{
            k: v for k, v in config_dict.items() 
            if k in cls.__dataclass_fields__
        })
