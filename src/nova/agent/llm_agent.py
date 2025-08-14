"""
LLM-powered agent (Planner, Actor, Critic) for Nova CI-Rescue.
Uses OpenAI or Anthropic APIs to generate fix plans, patches, and reviews.
"""
import os
import json
from typing import Optional, Dict, Any

from ..config import get_settings
from ..tools.http import AllowedHTTPClient

class LLMPlanner:
    """Planner node: generates a high-level plan for fixing failing tests using an LLM."""
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self._http = AllowedHTTPClient(self.settings, timeout=30.0)
        # Determine primary LLM service based on available API keys
        self.use_openai = bool(self.settings.openai_api_key)
        self.use_anthropic = bool(self.settings.anthropic_api_key)
        if not self.use_openai and not self.use_anthropic:
            raise RuntimeError("No LLM API key provided (OPENAI_API_KEY or ANTHROPIC_API_KEY required)")
        # Default model choices - use gpt-5 as specified
        self.openai_model = self.settings.default_llm_model or "gpt-5"
        self.anthropic_model = "claude-2"  # default Anthropics model
    
    def generate_plan(self, state: Any, failures_table: str) -> str:
        """
        Generate a plan to fix failing tests.
        
        Args:
            state: The current AgentState (provides context like failing_tests).
            failures_table: A markdown table or text listing failing tests and errors.
        Returns:
            A brief plan as a string describing the approach to fix the failures.
        """
        prompt_instructions = (
            "You are an AI assistant tasked with fixing failing tests in a software repository. "
            "Given the list of failing tests and their error messages, devise a concise plan of attack to fix the issues. "
            "Your plan should identify what needs to be fixed (e.g., incorrect logic or test expectations) and how to address it. "
            "Do not propose actual code changes, just the strategy."
        )
        plan_text: Optional[str] = None
        # Try OpenAI ChatCompletion API first
        if self.use_openai:
            try:
                url = "https://api.openai.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {self.settings.openai_api_key}"}
                messages = [
                    {"role": "system", "content": prompt_instructions},
                    {"role": "user", "content": f"Failing Tests:\n{failures_table}\n\nPlease provide a fix plan."}
                ]
                payload = {
                    "model": self.openai_model,
                    "messages": messages,
                    "temperature": 0,
                    "max_tokens": 256
                }
                response = self._http.post(url, headers=headers, json=payload)
                data = response.json()
                if response.status_code == 200 and "choices" in data:
                    plan_text = data["choices"][0]["message"]["content"].strip()
                else:
                    raise RuntimeError(f"OpenAI API error: {data.get('error', data)}")
            except Exception:
                # If OpenAI fails, fall back to Anthropic if available
                if not self.use_anthropic:
                    raise
                plan_text = None
        # Fallback to Anthropic API if OpenAI was not used or failed
        if plan_text is None and self.use_anthropic:
            try:
                url = "https://api.anthropic.com/v1/complete"
                headers = {
                    "x-api-key": self.settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
                human_prompt = (
                    f"\n\nHuman: {prompt_instructions}\nFailing Tests:\n{failures_table}\n\n"
                    "What is the plan to fix these failures?\n\nAssistant:"
                )
                payload = {
                    "model": self.anthropic_model,
                    "prompt": human_prompt,
                    "max_tokens_to_sample": 256,
                    "temperature": 0,
                    "stop_sequences": ["\n\nHuman:"]
                }
                response = self._http.post(url, headers=headers, json=payload)
                data = response.json()
                if response.status_code == 200 and "completion" in data:
                    plan_text = data["completion"].strip()
                else:
                    raise RuntimeError(f"Anthropic API error: {data.get('error', data)}")
            except Exception as e:
                raise RuntimeError(f"LLM Planner failed: {e}")
        return plan_text or ""

class LLMActor:
    """Actor node: generates a patch (code diff) to fix the failing tests using an LLM."""
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self._http = AllowedHTTPClient(self.settings, timeout=60.0)
        self.use_openai = bool(self.settings.openai_api_key)
        self.use_anthropic = bool(self.settings.anthropic_api_key)
        if not self.use_openai and not self.use_anthropic:
            raise RuntimeError("No LLM API key provided for patch generation")
        self.openai_model = self.settings.default_llm_model or "gpt-5"
        self.anthropic_model = "claude-2"
    
    def generate_patch(self, state: Any, plan: str, failures_table: str) -> Optional[str]:
        """
        Generate a unified diff patch to implement the fix.
        
        Args:
            state: Current AgentState (for context).
            plan: The plan/approach description from the planner.
            failures_table: Table or text of failing tests and errors.
        Returns:
            A unified diff (as text) with the code changes, or None if generation failed.
        """
        user_request = (
            "Using the following plan, generate a patch as a unified diff to fix the failing tests. "
            "Only output the diff, with no extra explanation. The diff should apply cleanly to the repository to make all tests pass."
        )
        patch_diff: Optional[str] = None
        if self.use_openai:
            try:
                url = "https://api.openai.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {self.settings.openai_api_key}"}
                messages = [
                    {"role": "system", "content": "You are a software engineer assistant who writes code patches to fix failing tests."},
                    {"role": "user", "content": f"Failing Tests:\n{failures_table}\n\nPlan:\n{plan}\n\n{user_request}"}
                ]
                payload = {
                    "model": self.openai_model,
                    "messages": messages,
                    "temperature": 0,
                    "max_tokens": 1024
                }
                response = self._http.post(url, headers=headers, json=payload)
                data = response.json()
                if response.status_code == 200 and "choices" in data:
                    patch_diff = data["choices"][0]["message"]["content"]
                    patch_diff = patch_diff.strip()
                else:
                    raise RuntimeError(f"OpenAI API error: {data.get('error', data)}")
            except Exception:
                if not self.use_anthropic:
                    raise
                patch_diff = None
        if patch_diff is None and self.use_anthropic:
            try:
                url = "https://api.anthropic.com/v1/complete"
                headers = {
                    "x-api-key": self.settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
                human_prompt = (
                    f"\n\nHuman: The following tests are failing:\n{failures_table}\n"
                    f"Planned approach:\n{plan}\n"
                    f"{user_request}\n\nAssistant:"
                )
                payload = {
                    "model": self.anthropic_model,
                    "prompt": human_prompt,
                    "max_tokens_to_sample": 1024,
                    "temperature": 0,
                    "stop_sequences": ["\n\nHuman:"]
                }
                response = self._http.post(url, headers=headers, json=payload)
                data = response.json()
                if response.status_code == 200 and "completion" in data:
                    patch_diff = data["completion"].strip()
                else:
                    raise RuntimeError(f"Anthropic API error: {data.get('error', data)}")
            except Exception as e:
                raise RuntimeError(f"LLM Actor failed: {e}")
        # Ensure the output contains diff markers to be a valid patch
        if patch_diff and "--- a/" in patch_diff and "+++ b/" in patch_diff:
            return patch_diff
        return None

class LLMCritic:
    """Critic node: evaluates the proposed patch using an LLM to decide approval or rejection."""
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self._http = AllowedHTTPClient(self.settings, timeout=30.0)
        self.use_openai = bool(self.settings.openai_api_key)
        self.use_anthropic = bool(self.settings.anthropic_api_key)
        if not self.use_openai and not self.use_anthropic:
            raise RuntimeError("No LLM API key provided for patch review")
        self.openai_model = self.settings.default_llm_model or "gpt-5"
        self.anthropic_model = "claude-2"
    
    def review_patch(self, state: Any, patch_diff: str, failures_table: str = "") -> bool:
        """
        Review a patch diff and decide whether to approve it.
        
        Args:
            state: Current AgentState (for context if needed).
            patch_diff: The unified diff text proposed by the actor.
            failures_table: (Optional) Failing tests info for context.
        Returns:
            True if the patch is approved, False if rejected.
        """
        instruction = (
            "You are a code reviewer. Verify whether the following patch correctly fixes the failing tests "
            "without introducing new issues. If the patch is adequate and likely to make all tests pass, respond with 'Approved'. "
            "If not, respond with 'Rejected' and a brief reason."
        )
        review_result: Optional[str] = None
        if self.use_openai:
            try:
                url = "https://api.openai.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {self.settings.openai_api_key}"}
                content = f"Failing Tests:\n{failures_table}\n\nPatch Diff:\n{patch_diff}\n\n{instruction}"
                messages = [
                    {"role": "system", "content": "You are a senior engineer reviewing a code patch."},
                    {"role": "user", "content": content}
                ]
                payload = {
                    "model": self.openai_model,
                    "messages": messages,
                    "temperature": 0,
                    "max_tokens": 200
                }
                response = self._http.post(url, headers=headers, json=payload)
                data = response.json()
                if response.status_code == 200 and "choices" in data:
                    review_result = data["choices"][0]["message"]["content"].strip()
                else:
                    raise RuntimeError(f"OpenAI API error: {data.get('error', data)}")
            except Exception:
                if not self.use_anthropic:
                    raise
                review_result = None
        if review_result is None and self.use_anthropic:
            try:
                url = "https://api.anthropic.com/v1/complete"
                headers = {
                    "x-api-key": self.settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
                human_prompt = (
                    f"\n\nHuman: {instruction}\nFailing Tests:\n{failures_table}\n\nPatch Diff:\n{patch_diff}\n\nAssistant:"
                )
                payload = {
                    "model": self.anthropic_model,
                    "prompt": human_prompt,
                    "max_tokens_to_sample": 200,
                    "temperature": 0,
                    "stop_sequences": ["\n\nHuman:"]
                }
                response = self._http.post(url, headers=headers, json=payload)
                data = response.json()
                if response.status_code == 200 and "completion" in data:
                    review_result = data["completion"].strip()
                else:
                    raise RuntimeError(f"Anthropic API error: {data.get('error', data)}")
            except Exception as e:
                raise RuntimeError(f"LLM Critic failed: {e}")
        if not review_result:
            return False
        # Normalize result to determine approval
        result_lower = review_result.lower()
        if "rejected" in result_lower or "reject" in result_lower:
            return False
        if "approved" in result_lower or "approve" in result_lower:
            return True
        return False

# Backward compatibility - keep the old LLMAgent class for existing code
class LLMAgent:
    """Wrapper class that combines Planner, Actor, and Critic for backward compatibility."""
    
    def __init__(self, repo_path=None):
        self.repo_path = repo_path
        self.settings = get_settings()
        self.planner = LLMPlanner(self.settings)
        self.actor = LLMActor(self.settings)
        self.critic = LLMCritic(self.settings)
    
    def generate_patch(self, failing_tests, iteration):
        """Generate a patch using the actor."""
        # Convert failing tests to a table format
        failures_table = self._format_failures(failing_tests)
        # Generate plan first
        plan = self.planner.generate_plan(None, failures_table)
        # Then generate patch
        return self.actor.generate_patch(None, plan, failures_table)
    
    def review_patch(self, patch, failing_tests):
        """Review a patch using the critic."""
        failures_table = self._format_failures(failing_tests)
        approved = self.critic.review_patch(None, patch, failures_table)
        return approved, "Approved" if approved else "Rejected"
    
    def create_plan(self, failing_tests, iteration):
        """Create a plan using the planner."""
        failures_table = self._format_failures(failing_tests)
        plan_text = self.planner.generate_plan(None, failures_table)
        return {
            "approach": plan_text,
            "target_tests": failing_tests[:2] if len(failing_tests) > 2 else failing_tests
        }
    
    def _format_failures(self, failing_tests):
        """Format failing tests as a table."""
        if not failing_tests:
            return "No failing tests"
        lines = ["| Test Name | File:Line | Error |", "|-----------|-----------|-------|"]
        for test in failing_tests[:5]:  # Limit to 5 tests
            name = test.get('name', 'unknown')
            file = test.get('file', 'unknown')
            line = test.get('line', 0)
            error = test.get('short_traceback', 'No error')[:50] + "..."
            location = f"{file}:{line}" if line > 0 else file
            lines.append(f"| {name} | {location} | {error} |")
        return "\n".join(lines)