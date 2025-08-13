from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    repo_path: str
    run_id: Optional[str] = None
    artifacts_dir: Optional[str] = None

    plan: Optional[List[str]] = None
    step: int = 0
    diffs: List[dict] = Field(default_factory=list)
    failing_targets: Optional[List[str]] = None
    test_result: Optional[dict] = None
    reflections: List[str] = Field(default_factory=list)
    done: bool = False

    branch_name: Optional[str] = None
    last_error: Optional[str] = None
    used_tools: List[str] = Field(default_factory=list)

    # Control flags
    dry_run: bool = False
    approved: Optional[bool] = None
    proposed_diff: Optional[str] = None
    allow_tests_mods: bool = False


__all__ = ["AgentState"]
