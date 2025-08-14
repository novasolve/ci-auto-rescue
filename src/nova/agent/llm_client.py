"""
Unified LLM client for Nova CI-Rescue supporting OpenAI and Anthropic.
"""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import anthropic
except ImportError:
    anthropic = None

from nova.config import get_settings
from nova.tools.http import AllowedHTTPClient


class LLMClient:
    """Unified LLM client that supports OpenAI and Anthropic models."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.provider = None
        
        # Determine which provider to use based on model name and available API keys
        model_name = self.settings.default_llm_model.lower()
        
        if "claude" in model_name and self.settings.anthropic_api_key:
            # Use Anthropic
            if anthropic is None:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
            self.client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
            self.provider = "anthropic"
            self.model = self._get_anthropic_model_name()
        elif self.settings.openai_api_key:
            # Use OpenAI
            if OpenAI is None:
                raise ImportError("openai package not installed. Run: pip install openai")
            self.client = OpenAI(api_key=self.settings.openai_api_key)
            self.provider = "openai"
            self.model = self._get_openai_model_name()
        else:
            raise ValueError("No valid API key found. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY.")
    
    def _get_openai_model_name(self) -> str:
        """Get the OpenAI model name to use."""
        model = self.settings.default_llm_model
        
        # Map special names to actual models
        if model == "gpt-5-chat-latest":
            # GPT-5 not available yet, fallback to GPT-4
            return "gpt-4o"
        elif "gpt-5" in model.lower():
            # Fallback to GPT-4 for any GPT-5 variant
            return "gpt-4o"
        elif model in ["gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]:
            return model
        else:
            # Default to GPT-4o
            return "gpt-4o"
    
    def _get_anthropic_model_name(self) -> str:
        """Get the Anthropic model name to use."""
        model = self.settings.default_llm_model.lower()
        
        # Map to actual Anthropic models
        if "claude-3-opus" in model:
            return "claude-3-opus-20240229"
        elif "claude-3-sonnet" in model:
            return "claude-3-sonnet-20240229"
        elif "claude-3-haiku" in model:
            return "claude-3-haiku-20240307"
        elif "claude-3.5-sonnet" in model or "claude-3-5-sonnet" in model:
            return "claude-3-5-sonnet-20241022"
        else:
            # Default to Claude 3.5 Sonnet
            return "claude-3-5-sonnet-20241022"
    
    def complete(self, system: str, user: str, temperature: float = 0.3, max_tokens: int = 2000) -> str:
        """
        Get a completion from the LLM.
        
        Args:
            system: System prompt
            user: User prompt
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            
        Returns:
            The LLM's response text
        """
        if self.provider == "openai":
            return self._complete_openai(system, user, temperature, max_tokens)
        elif self.provider == "anthropic":
            return self._complete_anthropic(system, user, temperature, max_tokens)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def _complete_openai(self, system: str, user: str, temperature: float, max_tokens: int) -> str:
        """Complete using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
            raise
    
    def _complete_anthropic(self, system: str, user: str, temperature: float, max_tokens: int) -> str:
        """Complete using Anthropic API."""
        try:
            response = self.client.messages.create(
                model=self.model,
                system=system,
                messages=[
                    {"role": "user", "content": user}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.content[0].text.strip()
        except Exception as e:
            print(f"Anthropic API error: {e}")
            raise


def parse_plan(response: str) -> Dict[str, Any]:
    """
    Parse the LLM's planning response into a structured plan.
    
    Args:
        response: The LLM's response text
        
    Returns:
        Structured plan dictionary
    """
    # Try to extract JSON if present
    if "{" in response and "}" in response:
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            plan_json = json.loads(response[start:end])
            return plan_json
        except:
            pass
    
    # Parse numbered list or bullets
    lines = response.strip().split('\n')
    steps = []
    
    for line in lines:
        line = line.strip()
        # Remove numbering or bullets
        if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
            # Remove leading numbers, dots, dashes, etc.
            import re
            cleaned = re.sub(r'^[\d\.\-\*\s]+', '', line).strip()
            if cleaned:
                steps.append(cleaned)
    
    if steps:
        return {
            "approach": "Fix failing tests systematically",
            "steps": steps
        }
    else:
        # Return the whole response as the approach
        return {
            "approach": response.strip(),
            "steps": []
        }


def build_planner_prompt(failing_tests: List[Dict[str, Any]]) -> str:
    """
    Build a prompt for the planner to analyze failures and create a fix strategy.
    
    Args:
        failing_tests: List of failing test details
        
    Returns:
        Formatted prompt string
    """
    prompt = "Analyze these failing tests and create a plan to fix them:\n\n"
    prompt += "FAILING TESTS:\n"
    prompt += "| Test Name | File | Line | Error |\n"
    prompt += "|-----------|------|------|-------|\n"
    
    for test in failing_tests[:10]:  # Limit to first 10 tests
        name = test.get('name', 'unknown')[:40]
        file = test.get('file', 'unknown')[:30]
        line = test.get('line', 0)
        error = test.get('short_traceback', '')
        if error:
            # Get first line of error
            error = error.split('\n')[0][:50]
        else:
            error = 'No error details'
        
        prompt += f"| {name} | {file} | {line} | {error} |\n"
    
    if len(failing_tests) > 10:
        prompt += f"\n... and {len(failing_tests) - 10} more failing tests\n"
    
    prompt += "\n"
    prompt += "Provide a structured plan to fix these failures. Include:\n"
    prompt += "1. A general approach/strategy\n"
    prompt += "2. Specific steps to take\n"
    prompt += "3. Which tests to prioritize\n"
    prompt += "\n"
    prompt += "Format your response as a numbered list of actionable steps."
    
    return prompt


def build_patch_prompt(plan: Dict[str, Any], failing_tests: List[Dict[str, Any]], 
                       test_contents: Dict[str, str] = None, 
                       source_contents: Dict[str, str] = None) -> str:
    """
    Build a prompt for the actor to generate a patch based on the plan.
    
    Args:
        plan: The plan created by the planner
        failing_tests: List of failing test details
        test_contents: Optional dict of test file contents
        source_contents: Optional dict of source file contents
        
    Returns:
        Formatted prompt string
    """
    prompt = "Generate a unified diff patch to fix the failing tests.\n\n"
    
    # Include the plan
    if plan:
        prompt += "PLAN:\n"
        if isinstance(plan.get('approach'), str):
            prompt += f"Approach: {plan['approach']}\n"
        if plan.get('steps'):
            prompt += "Steps:\n"
            for i, step in enumerate(plan['steps'][:5], 1):
                prompt += f"  {i}. {step}\n"
        prompt += "\n"
    
    # Include failing test details
    prompt += "FAILING TESTS TO FIX:\n"
    for i, test in enumerate(failing_tests[:3], 1):
        prompt += f"\n{i}. Test: {test.get('name', 'unknown')}\n"
        prompt += f"   File: {test.get('file', 'unknown')}\n"
        prompt += f"   Line: {test.get('line', 0)}\n"
        prompt += f"   Error:\n{test.get('short_traceback', 'No traceback')[:200]}\n"
    
    # Include test file contents if provided
    if test_contents:
        prompt += "\n\nTEST FILE CONTENTS (DO NOT MODIFY - these define correct behavior):\n"
        for file_path, content in test_contents.items():
            prompt += f"\n=== {file_path} ===\n"
            prompt += content[:2000]
            if len(content) > 2000:
                prompt += "\n... (truncated)"
    
    # Include source file contents if provided
    if source_contents:
        prompt += "\n\nSOURCE CODE (FIX THESE FILES):\n"
        for file_path, content in source_contents.items():
            prompt += f"\n=== {file_path} ===\n"
            prompt += content[:2000]
            if len(content) > 2000:
                prompt += "\n... (truncated)"
    
    prompt += "\n\n"
    prompt += "Generate a unified diff patch that fixes these test failures.\n"
    prompt += "The patch should:\n"
    prompt += "1. Be in standard unified diff format (like 'git diff' output)\n"
    prompt += "2. Include proper file paths (--- a/file and +++ b/file)\n"
    prompt += "3. Include proper @@ hunk headers with line numbers\n"
    prompt += "4. Fix the actual issues causing test failures\n"
    prompt += "5. Not modify the test files (unless the tests themselves are wrong)\n"
    prompt += "6. Be minimal and focused\n"
    prompt += "\n"
    prompt += "Return ONLY the unified diff, starting with --- and no other text."
    
    return prompt
