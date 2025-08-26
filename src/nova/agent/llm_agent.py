"""
Real LLM agent for generating patches to fix test failures.
Uses OpenAI or Anthropic to analyze failures and generate fixes.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from openai import OpenAI
from nova.config import get_settings


class LLMAgent:
    """LLM agent that generates patches using OpenAI/Anthropic."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.settings = get_settings()
        
        # Initialize OpenAI client
        if not self.settings.openai_api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.model = self.settings.default_llm_model
    
    def generate_patch(self, failing_tests: List[Dict[str, Any]], iteration: int, plan: Dict[str, Any] = None, critic_feedback: Optional[str] = None) -> Optional[str]:
        """
        Generate a patch to fix failing tests using LLM.
        
        Args:
            failing_tests: List of failing test details
            iteration: Current iteration number
            
        Returns:
            Unified diff string or None if no patch can be generated
        """
        if not failing_tests:
            return None
        
        # Read the test files
        test_contents = {}
        for test in failing_tests:
            test_file = test.get("file", "")
            if test_file and test_file not in test_contents:
                test_path = self.repo_path / test_file
                if test_path.exists():
                    test_contents[test_file] = test_path.read_text()
        
        # Prepare the prompt for the LLM
        prompt = self._create_patch_prompt(failing_tests, test_contents, iteration)
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert software engineer tasked with fixing failing tests. Generate a unified diff patch that fixes the test failures."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            patch_diff = response.choices[0].message.content.strip()
            
            # Extract the diff from the response (it might be wrapped in markdown)
            if "```diff" in patch_diff:
                start = patch_diff.find("```diff") + 7
                end = patch_diff.find("```", start)
                patch_diff = patch_diff[start:end].strip()
            elif "```" in patch_diff:
                start = patch_diff.find("```") + 3
                if patch_diff[start:start+1] == "\n":
                    start += 1
                end = patch_diff.find("```", start)
                patch_diff = patch_diff[start:end].strip()
            
            return patch_diff
            
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return None
    
    def _create_patch_prompt(self, failing_tests: List[Dict[str, Any]], test_contents: Dict[str, str], iteration: int) -> str:
        """Create a prompt for the LLM to generate a patch."""
        prompt = f"Fix the following failing tests (iteration {iteration}):\n\n"
        
        # Add failure information
        prompt += "FAILING TESTS:\n"
        for i, test in enumerate(failing_tests[:3], 1):  # Limit to first 3 tests
            prompt += f"\n{i}. Test: {test.get('name', 'unknown')}\n"
            prompt += f"   File: {test.get('file', 'unknown')}\n"
            prompt += f"   Line: {test.get('line', 0)}\n"
            prompt += f"   Error:\n{test.get('short_traceback', 'No traceback available')}\n"
        
        # Add test file contents
        prompt += "\n\nTEST FILE CONTENTS:\n"
        for file_path, content in test_contents.items():
            prompt += f"\n=== {file_path} ===\n"
            prompt += content[:2000]  # Limit content size
            if len(content) > 2000:
                prompt += "\n... (truncated)"
        
        prompt += "\n\nGenerate a unified diff patch that fixes these test failures. "
        prompt += "The patch should be in standard unified diff format (like 'git diff' output). "
        prompt += "Only fix the actual issues - don't change unrelated code.\n"
        prompt += "Return ONLY the diff, no explanations.\n"
        
        return prompt
    
    def review_patch(self, patch: str, failing_tests: List[Dict[str, Any]]) -> tuple[bool, str]:
        """
        Review a patch using LLM (critic).
        
        Args:
            patch: The patch diff to review
            failing_tests: List of failing tests this patch should fix
            
        Returns:
            Tuple of (approved: bool, reason: str)
        """
        if not patch:
            return False, "Empty patch"
        
        prompt = f"""Review this patch that attempts to fix failing tests:

PATCH:
```diff
{patch}
```

FAILING TESTS IT SHOULD FIX:
{json.dumps([{'name': t.get('name'), 'error': t.get('short_traceback', '')[:100]} for t in failing_tests[:3]], indent=2)}

Evaluate if this patch:
1. Actually fixes the failing tests
2. Doesn't introduce new bugs
3. Follows good coding practices
4. Is minimal and focused

Respond with JSON:
{{"approved": true/false, "reason": "brief explanation"}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a code reviewer. Review patches critically but approve if they fix the issues."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            review = response.choices[0].message.content.strip()
            
            # Parse the JSON response
            if "{" in review and "}" in review:
                start = review.find("{")
                end = review.rfind("}") + 1
                review_json = json.loads(review[start:end])
                return review_json.get("approved", False), review_json.get("reason", "No reason provided")
            
            # Fallback to simple approval
            return True, "Patch looks reasonable"
            
        except Exception as e:
            print(f"Error in patch review: {e}")
            # Default to rejecting if review fails
            return False, "Review failed due to error, patch not approved"
    
    def create_plan(self, failing_tests: List[Dict[str, Any]], iteration: int, critic_feedback: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a plan for fixing the failing tests.
        
        Args:
            failing_tests: List of failing test details
            iteration: Current iteration number
            
        Returns:
            Plan dictionary with approach and target tests
        """
        if not failing_tests:
            return {"approach": "No failures to fix", "target_tests": []}
        
        prompt = f"""Create a plan to fix these failing tests (iteration {iteration}):

{json.dumps([{'name': t.get('name'), 'file': t.get('file'), 'error': t.get('short_traceback', '')[:100]} for t in failing_tests[:5]], indent=2)}

Respond with a JSON plan:
{{"approach": "brief strategy", "priority_tests": ["test1", "test2"], "fix_strategy": "how to fix"}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a test fixing strategist. Create concise plans."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            plan_text = response.choices[0].message.content.strip()
            
            # Parse JSON from response
            if "{" in plan_text and "}" in plan_text:
                start = plan_text.find("{")
                end = plan_text.rfind("}") + 1
                plan = json.loads(plan_text[start:end])
                return {
                    "approach": plan.get("approach", "Fix failing assertions"),
                    "target_tests": failing_tests[:2] if len(failing_tests) > 2 else failing_tests,
                    "strategy": plan.get("fix_strategy", "Direct fixes")
                }
        except Exception as e:
            print(f"Error creating plan: {e}")
        
        # Fallback plan
        return {
            "approach": "Fix failing tests incrementally",
            "target_tests": failing_tests[:2] if len(failing_tests) > 2 else failing_tests
        }
