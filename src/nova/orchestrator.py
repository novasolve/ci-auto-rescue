"""
Nova CI-Rescue Orchestrator Loop
=================================

Main orchestration loop that integrates the LangChain Deep Agent
into Nova's fix workflow.
"""

import json
import subprocess
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

from nova.agent.state import AgentState
from nova.telemetry.logger import JSONLLogger
from nova.tools.git import GitBranchManager
from nova.agent.llm_agent import LLMAgent
from nova.agent.deep_agent import NovaDeepAgent

# Import SafetyConfig with fallback
try:
    from nova.config import SafetyConfig
except ImportError:
    # Create a basic SafetyConfig if it doesn't exist
    class SafetyConfig:
        def __init__(self):
            self.max_patch_lines = 1000
            self.max_affected_files = 10


class NovaOrchestrator:
    """
    Main orchestrator for Nova CI-Rescue that coordinates the Deep Agent
    with planning, critic review, and git operations.
    """
    
    def __init__(
        self,
        repo_path: Path,
        state: AgentState,
        telemetry: JSONLLogger,
        git_manager: Optional[GitBranchManager] = None,
        safety_config: Optional[SafetyConfig] = None,
        verbose: bool = False,
        max_iters: int = 5
    ):
        """
        Initialize the orchestrator.
        
        Args:
            repo_path: Path to the repository
            state: AgentState for tracking progress
            telemetry: Logger for telemetry events
            git_manager: Git manager for version control operations
            safety_config: Safety configuration for patch limits
            verbose: Enable verbose output
            max_iters: Maximum number of fix iterations
        """
        self.repo_path = repo_path
        self.state = state
        self.telemetry = telemetry
        self.git_manager = git_manager
        self.safety_config = safety_config or SafetyConfig()
        self.verbose = verbose
        self.max_iters = max_iters
        
        # Initialize components
        self.planner = LLMAgent(repo_path)  # Use LLMAgent for planning
        self.critic = LLMAgent(repo_path)   # Use LLMAgent for critic review
        self.deep_agent = NovaDeepAgent(
            state=state,
            telemetry=telemetry,
            git_manager=git_manager,
            verbose=verbose,
            safety_config=safety_config
        )
    
    def run(self) -> Dict[str, Any]:
        """
        Run the main orchestration loop.
        
        Returns:
            Dictionary with execution results
        """
        results = {
            "success": False,
            "iterations": 0,
            "patches_applied": [],
            "final_status": None
        }
        
        for iteration in range(1, self.max_iters + 1):
            if self.verbose:
                print(f"\n=== Iteration {iteration}/{self.max_iters} ===")
            
            self.state.current_iteration = iteration
            results["iterations"] = iteration
            
            # 1. Planner: analyze test failures and come up with a strategy
            failing_tests = self.gather_failing_tests()
            if not failing_tests:
                if self.verbose:
                    print("✅ All tests passing!")
                results["success"] = True
                results["final_status"] = "success"
                break
            
            plan_notes = self.plan_fixes(failing_tests)
            
            # Prepare the agent's input prompt with failing test details and plan hints
            user_prompt = self.format_agent_prompt(failing_tests, plan_notes)
            
            # 2. Deep Agent (Actor replacement): use LangChain agent to attempt a fix
            if self.verbose:
                print(f"Iteration {iteration}: invoking agent...")
            
            # Run the agent
            agent_success = self.deep_agent.run(
                failures_summary=self.format_failures_summary(failing_tests),
                error_details=self.format_error_details(failing_tests),
                code_snippets=""  # Could gather relevant source code snippets if available
            )
            
            # 3. After agent acts, collect the diff of changes it made
            diff = self.get_git_diff()
            if not diff:
                if self.verbose:
                    print("Agent made no changes. Stopping.")
                break
            
            # 4. Critic review: have an LLM review the diff for issues
            critic_verdict, critic_reason = self.review_patch(diff)
            
            # Enforce safety limits (e.g., maximum patch size or disallowed content)
            if critic_verdict == "reject" or self.patch_too_large(diff):
                if self.verbose:
                    print(f"Critic rejected the patch: {critic_reason}")
                    print("Rolling back changes.")
                
                self.rollback_working_copy()
                continue  # try another iteration with a new approach
            
            # 5. Apply patch: commit the agent's changes (since Critic approved)
            self.git_add_all()
            commit_msg = f"Nova DeepAgent fix iteration {iteration}"
            self.git_commit(commit_msg)
            
            results["patches_applied"].append({
                "iteration": iteration,
                "diff": diff,
                "commit_msg": commit_msg
            })
            
            # 6. Verify tests: run the test suite again to confirm all tests pass
            final_results = self.run_tests_in_sandbox()
            
            if final_results.get("all_passed", False):
                if self.verbose:
                    print(f"✅ All tests passed after iteration {iteration}")
                results["success"] = True
                results["final_status"] = "success"
                break
            else:
                if self.verbose:
                    print(f"Tests still failing after iteration {iteration}. Proceeding to next iteration.")
        else:
            if self.verbose:
                print("❌ Exceeded maximum iterations without fully passing tests.")
            results["final_status"] = "max_iterations"
        
        return results
    
    def gather_failing_tests(self) -> List[Dict[str, Any]]:
        """Gather information about currently failing tests."""
        # Run tests and parse results
        from nova.agent.unified_tools import run_tests
        test_result_str = run_tests()
        test_result = json.loads(test_result_str)
        
        failing_tests = []
        if "tests" in test_result:
            for test in test_result["tests"]:
                if test.get("outcome") in ["failed", "error"]:
                    failing_tests.append({
                        "name": test.get("nodeid", "unknown"),
                        "file": test.get("nodeid", "").split("::")[0],
                        "error": test.get("call", {}).get("longrepr", ""),
                        "traceback": test.get("call", {}).get("traceback", [])
                    })
        
        return failing_tests
    
    def plan_fixes(self, failing_tests: List[Dict[str, Any]]) -> str:
        """Generate a high-level plan for fixing the tests."""
        # Use the planner LLM to analyze failures
        prompt = f"""Analyze these failing tests and suggest a fix strategy:

{self.format_failures_summary(failing_tests)}

Provide a high-level plan for fixing these issues. Focus on:
1. Common patterns in the failures
2. Likely root causes
3. Suggested fix approach
"""
        
        plan = self.planner.generate_response(prompt, max_tokens=500)
        return plan
    
    def format_agent_prompt(self, failing_tests: List[Dict[str, Any]], plan_notes: str) -> str:
        """Format the prompt for the deep agent."""
        return f"""Plan notes from analysis:
{plan_notes}

Failing tests:
{self.format_failures_summary(failing_tests)}

Please fix these failing tests by modifying the source code.
"""
    
    def format_failures_summary(self, failing_tests: List[Dict[str, Any]]) -> str:
        """Format failing tests as a summary string."""
        lines = []
        for test in failing_tests:
            lines.append(f"- {test['file']}::{test['name']}")
        return "\n".join(lines)
    
    def format_error_details(self, failing_tests: List[Dict[str, Any]]) -> str:
        """Format error details from failing tests."""
        details = []
        for test in failing_tests[:3]:  # First 3 tests
            details.append(f"Test: {test['name']}")
            details.append(f"Error: {test.get('error', 'Unknown error')[:500]}")
            details.append("")
        return "\n".join(details)
    
    def get_git_diff(self) -> str:
        """Get the current git diff."""
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )
            return result.stdout
        except Exception:
            return ""
    
    def review_patch(self, diff: str) -> Tuple[str, str]:
        """Have the critic review a patch."""
        prompt = f"""Review this patch for fixing failing tests:

```diff
{diff[:5000]}  # Truncate for context limits
```

Is this patch safe and likely to fix the issues without breaking other functionality?
Respond with either "APPROVE" or "REJECT" followed by a brief reason.
"""
        
        response = self.critic.generate_response(prompt, max_tokens=200)
        
        if "APPROVE" in response.upper():
            return "approve", "Patch looks good"
        else:
            # Extract reason from response
            reason = response.replace("REJECT", "").strip()
            return "reject", reason
    
    def patch_too_large(self, diff: str) -> bool:
        """Check if a patch exceeds safety limits."""
        lines = diff.split("\n")
        
        # Count added/removed lines
        added = sum(1 for line in lines if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in lines if line.startswith("-") and not line.startswith("---"))
        
        # Check limits
        if added + removed > self.safety_config.max_patch_lines:
            return True
        
        # Count affected files
        files = sum(1 for line in lines if line.startswith("+++") or line.startswith("---"))
        if files > self.safety_config.max_affected_files * 2:  # *2 because +++ and --- for each file
            return True
        
        return False
    
    def rollback_working_copy(self):
        """Roll back uncommitted changes."""
        subprocess.run(
            ["git", "reset", "--hard", "HEAD"],
            cwd=self.repo_path,
            capture_output=True
        )
    
    def git_add_all(self):
        """Stage all changes."""
        subprocess.run(
            ["git", "add", "-A"],
            cwd=self.repo_path,
            capture_output=True
        )
    
    def git_commit(self, message: str):
        """Commit staged changes."""
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.repo_path,
            capture_output=True
        )
    
    def run_tests_in_sandbox(self) -> Dict[str, Any]:
        """Run tests and check if all pass."""
        from nova.agent.unified_tools import run_tests
        test_result_str = run_tests()
        test_result = json.loads(test_result_str)
        
        all_passed = test_result.get("exit_code") == 0
        return {
            "all_passed": all_passed,
            "results": test_result
        }
