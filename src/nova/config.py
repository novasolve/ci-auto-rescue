from __future__ import annotations

import os
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field


def _default_allowed_domains() -> List[str]:
    return [
        "api.openai.com",
        "api.anthropic.com",
        "pypi.org",
        "files.pythonhosted.org",
        "github.com",
        "raw.githubusercontent.com",
    ]


class NovaSettings(BaseModel):
    """Runtime configuration for Nova CI‑Rescue.

    Uses python-dotenv to load a local .env (if present), and reads values from
    environment variables. We avoid depending on pydantic-settings to keep
    compatibility consistent across Pydantic versions.
    """

    # Secrets and API endpoints
    openai_api_key: Optional[str] = Field(default=None)
    anthropic_api_key: Optional[str] = Field(default=None)
    openswe_base_url: Optional[str] = Field(default=None)
    openswe_api_key: Optional[str] = Field(default=None)

    # Policy and runtime settings
    allowed_domains: List[str] = Field(default_factory=_default_allowed_domains)
    max_iters: int = 6
    run_timeout_sec: int = 1200
    test_timeout_sec: int = 600
    telemetry_dir: str = "telemetry"
    default_llm_model: str = "gpt-5"

    @classmethod
    def from_env(cls) -> "NovaSettings":
        """Load settings from .env and environment variables."""
        load_dotenv()

        def _get(name: str, default: Optional[str] = None) -> Optional[str]:
            return os.environ.get(name, default)

        def _get_int(name: str, default: int) -> int:
            val = os.environ.get(name)
            try:
                return int(val) if val is not None else default
            except Exception:
                return default

        # Optional override for domain allow-list via NOVA_ALLOWED_DOMAINS
        domains_env = os.environ.get("NOVA_ALLOWED_DOMAINS")
        if domains_env:
            allowed = [d.strip() for d in domains_env.split(",") if d.strip()]
        else:
            allowed = _default_allowed_domains()

        return cls(
            openai_api_key=_get("OPENAI_API_KEY"),
            anthropic_api_key=_get("ANTHROPIC_API_KEY"),
            openswe_base_url=_get("OPENSWE_BASE_URL"),
            openswe_api_key=_get("OPENSWE_API_KEY"),
            allowed_domains=allowed,
            max_iters=_get_int("NOVA_MAX_ITERS", 6),
            run_timeout_sec=_get_int("NOVA_RUN_TIMEOUT_SEC", 1200),
            test_timeout_sec=_get_int("NOVA_TEST_TIMEOUT_SEC", 600),
            telemetry_dir=os.environ.get("NOVA_TELEMETRY_DIR", "telemetry"),
            default_llm_model=os.environ.get("NOVA_DEFAULT_LLM_MODEL", "gpt-5-chat-latest"),
        )


_CACHED_SETTINGS: Optional[NovaSettings] = None


def get_settings() -> NovaSettings:
    """Return a cached NovaSettings instance loaded from environment (.env)."""
    global _CACHED_SETTINGS
    if _CACHED_SETTINGS is None:
        _CACHED_SETTINGS = NovaSettings.from_env()
    return _CACHED_SETTINGS


# Configuration model for CLI YAML files
class CLIConfig(BaseModel):
    """Configuration options for Nova CLI loaded from a YAML file."""
    repo_path: Optional[str] = None
    model: Optional[str] = None
    timeout: Optional[int] = Field(None, ge=60, le=7200)
    max_iters: Optional[int] = Field(None, ge=1, le=20)
    blocked_paths: Optional[List[str]] = None
    max_changed_lines: Optional[int] = Field(None, ge=1)
    max_changed_files: Optional[int] = Field(None, ge=1)

    class Config:
        extra = "forbid"

def load_yaml_config(config_path: os.PathLike) -> CLIConfig:
    """Load configuration from a YAML file into a CLIConfig object."""
    try:
        import yaml
    except ImportError:
        raise RuntimeError("PyYAML is required for loading config files. Please install PyYAML.")
    
    # Read YAML content
    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load YAML config file: {e}")
    
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError("Configuration file must contain a key-value mapping (YAML dictionary).")
    
    # Resolve and validate repo_path if provided
    if "repo_path" in data and data["repo_path"] is not None:
        raw_path = str(data["repo_path"])
        expanded = os.path.expanduser(raw_path)
        from pathlib import Path
        path_obj = Path(expanded)
        if not path_obj.is_absolute():
            # Make relative paths relative to the config file location
            path_obj = (Path(config_path).parent / path_obj).resolve()
        else:
            path_obj = path_obj.resolve()
        if not path_obj.exists() or not path_obj.is_dir():
            raise ValueError(f"Repository path '{path_obj}' in config does not exist or is not a directory.")
        data["repo_path"] = str(path_obj)
    
    # Create and validate the config object
    return CLIConfig(**data)

__all__ = ["NovaSettings", "get_settings", "CLIConfig", "load_yaml_config"]
