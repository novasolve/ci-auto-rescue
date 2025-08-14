"""
Agent state management for Nova CI-Rescue.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path


@dataclass
class AgentState:
    """State container for the Nova agent."""
    
    # Repository information
    repo_path: Path
    branch_name: Optional[str] = None
    original_commit: Optional[str] = None
    
    # Test failure information
    failing_tests: List[Dict[str, Any]] = field(default_factory=list)
    total_failures: int = 0
    
    # Planning information
    plan: Optional[Dict[str, Any]] = None
    critic_feedback: Optional[str] = None  # Feedback from previous critic rejection
    
    # Execution state
    current_iteration: int = 0
    max_iterations: int = 6
    timeout_seconds: int = 1200
    start_time: datetime = field(default_factory=datetime.now)
    current_step: int = 0  # Track step number for commits
    
    # Results
    patches_applied: List[str] = field(default_factory=list)
    test_results: List[Dict[str, Any]] = field(default_factory=list)
    final_status: Optional[str] = None  # 'success', 'timeout', 'max_iters', 'error'
    
    def add_failing_tests(self, tests: List[Any]) -> None:
        """Add failing tests to the state."""
        self.failing_tests = [
            test.to_dict() if hasattr(test, 'to_dict') else test 
            for test in tests
        ]
        self.total_failures = len(self.failing_tests)
    
    def get_planner_context(self) -> Dict[str, Any]:
        """Get context for the planner prompt."""
        return {
            "repo_path": str(self.repo_path),
            "failing_tests": self.failing_tests,
            "total_failures": self.total_failures,
            "current_iteration": self.current_iteration,
            "max_iterations": self.max_iterations,
            "patches_applied": len(self.patches_applied),
        }
    
    def increment_iteration(self) -> bool:
        """Increment iteration counter and check if we should continue."""
        self.current_iteration += 1
        return self.current_iteration <= self.max_iterations
    
    def increment_step(self) -> int:
        """Increment and return the step counter for patch commits."""
        self.current_step += 1
        return self.current_step
    
    def check_timeout(self) -> bool:
        """Check if we've exceeded the timeout."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return elapsed >= self.timeout_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "repo_path": str(self.repo_path),
            "branch_name": self.branch_name,
            "original_commit": self.original_commit,
            "failing_tests": self.failing_tests,
            "total_failures": self.total_failures,
            "current_iteration": self.current_iteration,
            "max_iterations": self.max_iterations,
            "timeout_seconds": self.timeout_seconds,
            "start_time": self.start_time.isoformat(),
            "patches_applied": self.patches_applied,
            "test_results": self.test_results,
            "final_status": self.final_status,
        }
