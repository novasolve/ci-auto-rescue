"""
CI-Rescue Pipeline Integration
===============================

Integrates the LangChain Deep Agent into the CI-Rescue workflow.
"""

import json
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging

from ..agent.deep_agent import DeepAgent
from ..agent.agent_config import AgentConfig
from ..tools.agent_tools import run_tests_tool
from .critic import Critic


logger = logging.getLogger(__name__)


class CIRescuePipeline:
    """
    Main pipeline for CI-Rescue with Deep Agent integration.
    
    This replaces the multi-node architecture with a streamlined
    agent-based approach.
    """
    
    def __init__(
        self,
        agent_config: Optional[AgentConfig] = None,
        max_iterations: int = 5,
        auto_commit: bool = True,
        verbose: bool = True
    ):
        """
        Initialize the CI-Rescue pipeline.
        
        Args:
            agent_config: Configuration for the deep agent.
            max_iterations: Maximum fix attempts.
            auto_commit: Whether to auto-commit successful fixes.
            verbose: Enable verbose output.
        """
        self.agent_config = agent_config or AgentConfig()
        self.max_iterations = max_iterations
        self.auto_commit = auto_commit
        self.verbose = verbose
        
        # Initialize components
        self.agent = DeepAgent(self.agent_config)
        self.critic = Critic(
            max_lines=self.agent_config.max_patch_lines,
            max_files=self.agent_config.max_affected_files
        )
        
        # State tracking
        self.current_iteration = 0
        self.fix_history = []
    
    def run(
        self,
        initial_test_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run the CI-Rescue pipeline.
        
        Args:
            initial_test_results: Optional pre-computed test results.
            
        Returns:
            Dictionary with pipeline results.
        """
        self._log("Starting CI-Rescue Pipeline with Deep Agent")
        
        # Get initial test results if not provided
        if initial_test_results is None:
            self._log("Running initial test suite...")
            initial_test_results = json.loads(run_tests_tool())
        
        # Check if there are failing tests
        failing_tests = self._extract_failing_tests(initial_test_results)
        
        if not failing_tests:
            self._log("✅ All tests are passing! No fixes needed.")
            return {
                "status": "success",
                "message": "All tests passing",
                "iterations": 0,
                "initial_results": initial_test_results
            }
        
        self._log(f"Found {len(failing_tests)} failing tests")
        
        # Main fix loop
        for iteration in range(1, self.max_iterations + 1):
            self.current_iteration = iteration
            self._log(f"\n=== Iteration {iteration}/{self.max_iterations} ===")
            
            # Run the deep agent to fix tests
            success, patch_diff = self._run_fix_iteration(failing_tests)
            
            if success:
                # Verify all tests pass
                self._log("Verifying fix...")
                final_results = json.loads(run_tests_tool())
                final_failing = self._extract_failing_tests(final_results)
                
                if not final_failing:
                    self._log("✅ All tests passing after fix!")
                    
                    if self.auto_commit:
                        self._commit_changes(iteration)
                    
                    return {
                        "status": "success",
                        "message": "All tests fixed",
                        "iterations": iteration,
                        "initial_failing": len(failing_tests),
                        "patch_diff": patch_diff,
                        "initial_results": initial_test_results,
                        "final_results": final_results
                    }
                else:
                    self._log(f"⚠️ Still have {len(final_failing)} failing tests")
                    failing_tests = final_failing
            else:
                self._log("❌ Fix attempt failed, rolling back...")
                self._rollback_changes()
        
        # Max iterations reached
        self._log(f"❌ Failed to fix all tests after {self.max_iterations} iterations")
        
        return {
            "status": "failure",
            "message": f"Could not fix all tests after {self.max_iterations} iterations",
            "iterations": self.max_iterations,
            "remaining_failures": len(failing_tests),
            "initial_results": initial_test_results
        }
    
    def _run_fix_iteration(
        self,
        failing_tests: List[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Run a single fix iteration.
        
        Returns:
            Tuple of (success, patch_diff)
        """
        # Create a planning prompt
        planner_notes = self._generate_plan(failing_tests)
        
        # Build the agent prompt
        failing_tests_desc = self._format_failing_tests(failing_tests)
        
        user_prompt = f"""Fix the following failing tests:

{failing_tests_desc}

Approach:
{planner_notes}

Please analyze the failures, read the relevant source files, make the necessary fixes, and verify the tests pass.
Remember to make minimal changes and do not modify the test files themselves."""
        
        # Run the agent
        self._log("Running deep agent to fix tests...")
        try:
            agent_output = self.agent.run(user_prompt)
            self._log(f"Agent output: {agent_output[:500]}..." if len(agent_output) > 500 else f"Agent output: {agent_output}")
        except Exception as e:
            self._log(f"Agent error: {e}")
            return False, None
        
        # Generate patch diff
        patch_diff = self._get_current_diff()
        
        if not patch_diff:
            self._log("No changes detected")
            return False, None
        
        # Review the patch with Critic
        self._log("Reviewing patch with Critic...")
        approved, feedback, metadata = self.critic.review_patch(
            patch_diff,
            failing_tests,
            use_llm=False  # Can enable LLM review if configured
        )
        
        self._log(f"Critic decision: {'APPROVED' if approved else 'REJECTED'}")
        self._log(f"Critic feedback: {feedback}")
        
        if metadata:
            self._log(f"Patch stats: {metadata.get('added_lines', 0)} additions, "
                     f"{metadata.get('removed_lines', 0)} deletions, "
                     f"{metadata.get('file_count', 0)} files")
        
        if approved:
            # Save to fix history
            self.fix_history.append({
                "iteration": self.current_iteration,
                "patch": patch_diff,
                "metadata": metadata,
                "failing_tests": len(failing_tests)
            })
            
            return True, patch_diff
        else:
            # Rollback changes
            self._rollback_changes()
            return False, None
    
    def _extract_failing_tests(
        self, 
        test_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract failing test information from test results."""
        failing_tests = []
        
        # Check for failing_tests key (from our test runner)
        if "failing_tests" in test_results:
            return test_results["failing_tests"]
        
        # Check for tests array (pytest-json-report format)
        if "tests" in test_results:
            for test in test_results["tests"]:
                if test.get("outcome") in ["failed", "error"]:
                    failing_tests.append({
                        "name": test.get("nodeid", "unknown"),
                        "file": test.get("nodeid", "").split("::")[0] if "::" in test.get("nodeid", "") else "",
                        "outcome": test.get("outcome"),
                        "message": test.get("call", {}).get("longrepr", "")
                    })
        
        return failing_tests
    
    def _generate_plan(self, failing_tests: List[Dict[str, Any]]) -> str:
        """Generate a plan for fixing the tests."""
        plan = []
        
        # Group failures by file
        failures_by_file = {}
        for test in failing_tests:
            file_path = test.get("file", "unknown")
            if file_path not in failures_by_file:
                failures_by_file[file_path] = []
            failures_by_file[file_path].append(test)
        
        # Create plan based on failure patterns
        plan.append("1. Analyze error patterns across failing tests")
        plan.append("2. Identify common root causes")
        
        for file_path, tests in failures_by_file.items():
            plan.append(f"3. Fix issues in {file_path} ({len(tests)} failures)")
        
        plan.append("4. Verify all fixes work together")
        
        return "\n".join(plan)
    
    def _format_failing_tests(
        self, 
        failing_tests: List[Dict[str, Any]]
    ) -> str:
        """Format failing tests for display."""
        lines = []
        for test in failing_tests:
            name = test.get("name", "unknown")
            file_path = test.get("file", "unknown")
            message = test.get("message", "No error message")
            
            # Truncate long messages
            if len(message) > 200:
                message = message[:200] + "..."
            
            lines.append(f"- {file_path}::{name}")
            lines.append(f"  Error: {message}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _get_current_diff(self) -> str:
        """Get the current git diff."""
        try:
            result = subprocess.run(
                ["git", "diff"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout
        except Exception as e:
            self._log(f"Error getting diff: {e}")
            return ""
    
    def _commit_changes(self, iteration: int):
        """Commit changes to git."""
        try:
            subprocess.run(["git", "add", "."], check=True)
            commit_msg = f"nova: fix failing tests (iteration {iteration})"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            self._log(f"✅ Changes committed: {commit_msg}")
        except Exception as e:
            self._log(f"Error committing changes: {e}")
    
    def _rollback_changes(self):
        """Rollback uncommitted changes."""
        try:
            subprocess.run(["git", "reset", "--hard", "HEAD"], check=True)
            self._log("Changes rolled back")
        except Exception as e:
            self._log(f"Error rolling back changes: {e}")
    
    def _log(self, message: str):
        """Log a message."""
        if self.verbose:
            print(f"[CI-Rescue] {message}")
        logger.info(message)
