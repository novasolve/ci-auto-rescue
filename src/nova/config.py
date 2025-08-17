"""
Configuration management for Nova CI-Rescue
============================================

Supports both Python-based and YAML configuration.
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class NovaSettings:
    """Main settings for Nova CI-Rescue."""
    
    # LLM Configuration
    default_llm_model: str = field(default_factory=lambda: os.getenv("NOVA_MODEL") or os.getenv("NOVA_DEFAULT_LLM_MODEL") or os.getenv("MODEL") or "gpt-4")
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    
    # API Keys (loaded from environment)
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    anthropic_api_key: Optional[str] = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    
    # Execution Settings
    max_iterations: int = 6
    timeout_seconds: int = 1200
    verbose: bool = False
    
    # Backward compatibility aliases
    max_iters: int = 6
    run_timeout_sec: int = 1200
    test_timeout_sec: int = 300
    
    # Safety Configuration
    max_patch_lines: int = 500
    max_affected_files: int = 10
    max_file_size: int = 100_000
    
    # Docker Configuration
    docker_image: str = "nova-ci-rescue-sandbox:latest"
    use_docker: bool = True
    
    # Telemetry
    telemetry_enabled: bool = True
    telemetry_dir: Path = field(default_factory=lambda: Path(".nova/telemetry"))
    
    @classmethod
    def from_yaml(cls, path: Path) -> "NovaSettings":
        """Load settings from YAML file."""
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        
        # Create settings with YAML data
        settings = cls()
        
        # Update with YAML values
        if data:
            # Handle 'model' as an alias for 'default_llm_model'
            if 'model' in data and 'default_llm_model' not in data:
                data['default_llm_model'] = data.pop('model')
            
            for key, value in data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
        
        return settings
    
    def merge_with_yaml(self, yaml_path: Path):
        """Merge current settings with YAML file."""
        if yaml_path.exists():
            with open(yaml_path, "r") as f:
                data = yaml.safe_load(f)
            
            if data:
                # Handle 'model' as an alias for 'default_llm_model'
                if 'model' in data and 'default_llm_model' not in data:
                    data['default_llm_model'] = data.pop('model')
                
                # Save current model if it was set by environment variable
                env_model = os.getenv("NOVA_MODEL") or os.getenv("NOVA_DEFAULT_LLM_MODEL") or os.getenv("MODEL")
                
                for key, value in data.items():
                    if hasattr(self, key) and value is not None:
                        # Don't override model if environment variable is set
                        if key == 'default_llm_model' and env_model:
                            continue
                        setattr(self, key, value)


@dataclass 
class SafetyConfig:
    """Safety configuration for patch validation."""
    
    max_lines_changed: int = 500
    max_files_modified: int = 10
    max_additions: int = 300
    max_deletions: int = 300
    
    # Paths that should never be modified
    denied_paths: List[str] = field(default_factory=lambda: [
        "test_*.py",
        "*_test.py", 
        "tests/",
        ".github/",
        "setup.py",
        "pyproject.toml",
        "requirements.txt",
        "poetry.lock",
        "Pipfile",
        ".env"
    ])
    
    # Patterns that should trigger review
    suspicious_patterns: List[str] = field(default_factory=lambda: [
        r"exec\(",
        r"eval\(",
        r"__import__",
        r"os\.system",
        r"subprocess\.call",
        r"rm\s+-rf"
    ])
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SafetyConfig":
        """Create from dictionary (e.g., from YAML)."""
        config = cls()
        
        for key, value in data.items():
            if hasattr(config, key):
                if key == "denied_paths" and isinstance(value, list):
                    config.denied_paths.extend(value)
                else:
                    setattr(config, key, value)
        
        return config


def load_yaml_config(path: Path) -> Optional[Dict[str, Any]]:
    """
    Load configuration from YAML file.
    
    Args:
        path: Path to YAML configuration file
        
    Returns:
        Dictionary of configuration values or None
    """
    if not path.exists():
        return None
    
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Failed to load config from {path}: {e}")
        return None


def get_settings(config_file: Optional[Path] = None) -> NovaSettings:
    """
    Get Nova settings, optionally loading from config file.
    
    Args:
        config_file: Optional path to YAML config file
        
    Returns:
        NovaSettings instance
    """
    settings = NovaSettings()
    
    # Check for default config locations
    if not config_file:
        # Check current directory and parent directories up to 3 levels
        search_dirs = [Path.cwd()]
        current = Path.cwd()
        for _ in range(3):
            if current.parent != current:
                current = current.parent
                search_dirs.append(current)
        
        # Also check the Nova package directory
        nova_root = Path(__file__).parent.parent.parent
        if nova_root.exists():
            search_dirs.append(nova_root)
        
        # Search for config files in all directories
        for search_dir in search_dirs:
            for config_name in [
                ".nova.yml",
                ".nova.yaml", 
                "nova.config.yml",
                "nova.config.yaml"
            ]:
                possible_path = search_dir / config_name
                if possible_path.exists():
                    config_file = possible_path
                    break
            if config_file:
                break
    
    # Load from config file if found
    if config_file:
        settings.merge_with_yaml(config_file)
    
    return settings