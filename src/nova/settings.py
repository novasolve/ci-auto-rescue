from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class NovaSettings(BaseSettings):
    """Configuration for Nova CI-Rescue, sourced from environment/.env.

    Environment variables map 1:1 to fields below. See .env.example for keys.
    """

    # LLM providers
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = Field(default="gpt-4o-mini")
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = Field(default="claude-3-5-sonnet-latest")

    # OpenSWE service
    OPENSWE_BASE_URL: Optional[str] = None
    OPENSWE_API_KEY: Optional[str] = None

    # Policy & limits
    MAX_ITERS: int = 6
    GLOBAL_TIMEOUT_S: int = 1200
    PYTEST_TIMEOUT_S: int = 600
    DIFF_MAX_CHANGED_LINES: int = 50
    ALLOW_TEST_MODS: bool = False

    # Telemetry and artifacts
    TELEMETRY_ENABLED: bool = True
    ARTIFACTS_ROOT: str = ".nova"

    # Network allow-list (comma-separated or list)
    NETWORK_ALLOWLIST: List[str] = Field(
        default_factory=lambda: ["api.openai.com", "api.anthropic.com"]
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="", case_sensitive=False, extra="ignore"
    )

    @field_validator("NETWORK_ALLOWLIST", mode="before")
    @classmethod
    def _split_allowlist(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            # Accept comma or newline separated
            parts = [p.strip() for p in v.replace("\n", ",").split(",") if p.strip()]
            return parts
        return v


@lru_cache(maxsize=1)
def get_settings() -> NovaSettings:
    """Singleton accessor for loaded settings."""
    return NovaSettings()  # type: ignore[arg-type]


__all__ = ["NovaSettings", "get_settings"]
