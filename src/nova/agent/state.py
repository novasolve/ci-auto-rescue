from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    id: int
    description: str
    target_files: Optional[List[str]] = Field(default=None)


class Plan(BaseModel):
    steps: List[PlanStep] = Field(default_factory=list)


class TestResult(BaseModel):
    failed: List[dict] = Field(default_factory=list)
    passed: List[str] = Field(default_factory=list)
    errors: List[dict] = Field(default_factory=list)
    duration: float = 0.0


class AgentState(BaseModel):
    plan: Optional[Plan] = None
    step: int = 0
    diffs: List[str] = Field(default_factory=list)
    test_result: Optional[TestResult] = None
    reflections: List[str] = Field(default_factory=list)
    done: bool = False
    repo_root: str
    # Additional flag to support graph branching on review
    critic_approved: Optional[bool] = None


__all__ = [
    "PlanStep",
    "Plan",
    "TestResult",
    "AgentState",
]
