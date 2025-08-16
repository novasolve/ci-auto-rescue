"""
Legacy Agent Implementation (Deprecated)
========================================

Minimal implementation of the legacy agent for backward compatibility.
This agent uses the old multi-step approach and is deprecated.
Users should migrate to the Deep Agent.
"""

import json
from typing import Optional, Dict, Any
from pathlib import Path

from nova.agent.state import AgentState
from nova.agent.llm_client import LLMClient
from nova.telemetry.logger import JSONLLogger
from nova.tools.git import GitBranchManager
from nova.runner import TestRunner
from nova.tools.fs import FileSystemTool
from nova.tools.patch_fixer import PatchFixer


class LegacyAgent:
    """
    Legacy agent implementation for backward compatibility.
    
    This is a simplified version of the old LLMAgent that follows
    the traditional plan-act-review loop. It's deprecated and will
    be removed in v2.0.
    
    ⚠️ DEPRECATED: Use the Deep Agent instead for better performance.
    """
    
    def __init__(
        self,
        state: Optional[AgentState] = None,
        telemetry: Optional[JSONLLogger] = None,
        git_manager: Optional[GitBranchManager] = None,
        verbose: bool = False,
        safety_config: Optional[Any] = None
    ):
        """Initialize the legacy agent."""
        self.state = state or AgentState(repo_path=Path("."))
        self.telemetry = telemetry
        self.git_manager = git_manager
        self.verbose = verbose
        self.safety_config = safety_config
        
        # Initialize LLM client
        self.llm_client = LLMClient()
        
        # Initialize tools
        self.runner = TestRunner(self.state.repo_path)
        self.fs_tool = FileSystemTool(self.state.repo_path)
        self.patch_fixer = PatchFixer()
        
        if self.verbose:
            print("⚠️  WARNING: Using deprecated legacy agent. Please switch to Deep Agent.")
    
    def run(self, failures_summary: str, error_details: str, code_snippets: str = "") -> bool:
        """
        Run the legacy agent to fix failing tests.
        
        Args:
            failures_summary: Summary of failing tests
            error_details: Detailed error messages
            code_snippets: Optional code snippets
            
        Returns:
            True if all tests are fixed, False otherwise
        """
        if self.telemetry:
            self.telemetry.log_event("legacy_agent_start", {
                "failures_summary": failures_summary
            })
        
        max_iterations = self.state.max_iterations
        
        for iteration in range(1, max_iterations + 1):
            if self.verbose:
                print(f"\n[Legacy Agent] Iteration {iteration}/{max_iterations}")
            
            # Step 1: Plan the fix
            plan = self._plan_fix(failures_summary, error_details, code_snippets)
            if not plan:
                if self.verbose:
                    print("[Legacy Agent] Could not generate a plan")
                break
            
            # Step 2: Generate patch
            patch = self._generate_patch(plan, failures_summary)
            if not patch:
                if self.verbose:
                    print("[Legacy Agent] Could not generate a patch")
                break
            
            # Step 3: Review patch (critic)
            if not self._review_patch(patch):
                if self.verbose:
                    print("[Legacy Agent] Patch rejected by critic")
                continue
            
            # Step 4: Apply patch
            if not self._apply_patch(patch):
                if self.verbose:
                    print("[Legacy Agent] Failed to apply patch")
                continue
            
            # Step 5: Run tests
            failing_tests, passing_count = self.runner.run_tests()
            
            if len(failing_tests) == 0:
                if self.verbose:
                    print("[Legacy Agent] ✅ All tests passing!")
                if self.telemetry:
                    self.telemetry.log_event("legacy_agent_success", {
                        "iteration": iteration
                    })
                return True
            
            # Update failures for next iteration
            failures_summary = self._format_failures(failing_tests)
            error_details = "\n\n".join(test.short_traceback for test in failing_tests[:3])
        
        if self.verbose:
            print(f"[Legacy Agent] Reached max iterations ({max_iterations})")
        
        if self.telemetry:
            self.telemetry.log_event("legacy_agent_failed", {
                "reason": "max_iterations"
            })
        
        return False
    
    def _plan_fix(self, failures: str, errors: str, snippets: str) -> str:
        """Generate a plan to fix the failing tests."""
        prompt = f"""
        You are a software engineer. Analyze these test failures and create a plan to fix them.
        
        Failing Tests:
        {failures}
        
        Error Details:
        {errors}
        
        {snippets if snippets else ''}
        
        Create a step-by-step plan to fix these issues. Be specific about what files to modify.
        """
        
        try:
            response = self.llm_client.generate(prompt, max_tokens=1000)
            return response
        except Exception as e:
            if self.verbose:
                print(f"[Legacy Agent] Error generating plan: {e}")
            return ""
    
    def _generate_patch(self, plan: str, failures: str) -> str:
        """Generate a patch based on the plan."""
        prompt = f"""
        Based on this plan, generate a git-format patch to fix the failing tests.
        
        Plan:
        {plan}
        
        Failing Tests:
        {failures}
        
        Generate a minimal patch that fixes the issues. Use git diff format.
        """
        
        try:
            response = self.llm_client.generate(prompt, max_tokens=2000)
            # Extract patch from response
            if "```diff" in response:
                start = response.find("```diff") + 7
                end = response.find("```", start)
                return response[start:end].strip()
            return response
        except Exception as e:
            if self.verbose:
                print(f"[Legacy Agent] Error generating patch: {e}")
            return ""
    
    def _review_patch(self, patch: str) -> bool:
        """Review patch for safety and correctness."""
        # Basic safety checks
        if not patch:
            return False
        
        lines = patch.split('\n')
        added_lines = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
        removed_lines = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))
        
        # Check size limits
        if added_lines + removed_lines > 200:
            if self.verbose:
                print(f"[Legacy Agent] Patch too large: {added_lines + removed_lines} lines")
            return False
        
        # Check for test file modifications
        for line in lines:
            if line.startswith('+++') or line.startswith('---'):
                if 'test' in line.lower():
                    if self.verbose:
                        print("[Legacy Agent] Patch modifies test files - rejected")
                    return False
        
        return True
    
    def _apply_patch(self, patch: str) -> bool:
        """Apply the patch to the repository."""
        try:
            # Write patch to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
                f.write(patch)
                patch_file = f.name
            
            # Apply using git
            import subprocess
            result = subprocess.run(
                ['git', 'apply', patch_file],
                cwd=self.state.repo_path,
                capture_output=True,
                text=True
            )
            
            # Clean up
            import os
            os.unlink(patch_file)
            
            return result.returncode == 0
            
        except Exception as e:
            if self.verbose:
                print(f"[Legacy Agent] Error applying patch: {e}")
            return False
    
    def _format_failures(self, failing_tests) -> str:
        """Format failing tests as a summary."""
        lines = []
        for test in failing_tests[:5]:  # Limit to first 5
            lines.append(f"- {test.test_name}: {test.error_type}")
        return "\n".join(lines)
