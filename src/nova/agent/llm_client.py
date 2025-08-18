"""
Unified LLM client for Nova CI-Rescue supporting OpenAI and Anthropic.
"""

import json
import re
import time
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
    
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self.client = None
        self.provider = None
        
        # Determine which provider to use based on model name and available API keys
        model_name = self.settings.default_llm_model.lower()
        openai_key = self.settings.openai_api_key
        anthropic_key = self.settings.anthropic_api_key
        
        # Smart provider selection
        if "claude" in model_name and anthropic_key:
            # Claude model requested and key available
            if anthropic is None:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
            self.client = anthropic.Anthropic(api_key=anthropic_key)
            self.provider = "anthropic"
            self.model = self._get_anthropic_model_name()
        elif "claude" in model_name and not anthropic_key and openai_key:
            # Claude requested but only OpenAI key available - fallback to GPT
            print(f"Warning: Claude model '{self.settings.default_llm_model}' requested but no Anthropic key found. Using OpenAI instead.")
            if OpenAI is None:
                raise ImportError("openai package not installed. Run: pip install openai")
            self.client = OpenAI(api_key=openai_key)
            self.provider = "openai"
            self.model = "gpt-4"  # Fallback to GPT-4
        elif openai_key:
            # OpenAI model or default
            if OpenAI is None:
                raise ImportError("openai package not installed. Run: pip install openai")
            self.client = OpenAI(api_key=openai_key)
            self.provider = "openai"
            self.model = self._get_openai_model_name()
        elif anthropic_key:
            # Only Anthropic key available, use Claude even if not explicitly requested
            print(f"Note: Using Claude model (only Anthropic key available)")
            if anthropic is None:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
            self.client = anthropic.Anthropic(api_key=anthropic_key)
            self.provider = "anthropic"
            self.model = self._get_anthropic_model_name()
        else:
            raise ValueError("No valid API key found. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY.")
    
    def _get_openai_model_name(self) -> str:
        """Get the OpenAI model name to use."""
        model = self.settings.default_llm_model
        model_lower = model.lower()
        
        # Map known aliases and variations to valid OpenAI models
        if "gpt-5" in model_lower:
            # Return GPT-5 as-is (Deep Agent will handle it specially)
            return model
        elif "gpt-4.1" in model_lower:
            # Handle GPT-4.1 variations (including "gpt-4.1alias")
            return "gpt-4"
        elif model in ["gpt-4", "gpt-4-turbo", "gpt-4-0613", "gpt-4-32k", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"]:
            # Known valid OpenAI models
            return model
        elif model_lower == "gpt-4o" or model_lower == "gpt-4o-mini":
            # Map internal aliases to valid models
            return "gpt-4"
        else:
            # Default to GPT-4 for any unknown model
            print(f"Warning: Unknown model '{model}', falling back to gpt-4")
            return "gpt-4"
    
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
        """Complete using OpenAI API with retry on rate limits and model fallback."""
        original_model = self.model
        for attempt in range(3):  # try up to 3 times
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
                err_msg = str(e).lower()
                # If model not found, try fallback
                if ("model" in err_msg and "not found" in err_msg) or "model_not_found" in err_msg:
                    if self.model != "gpt-4" and attempt == 0:  # First attempt with invalid model
                        print(f"Warning: Model '{self.model}' not found, falling back to gpt-4")
                        self.model = "gpt-4"
                        continue  # retry with gpt-4
                # If rate limit encountered, backoff and retry
                elif "rate limit" in err_msg or "rate exceeded" in err_msg:
                    if attempt < 2:  # not last attempt
                        delay = 2 ** attempt  # exponential backoff: 1s, 2s, ...
                        print(f"Warning: OpenAI rate limit hit (attempt {attempt+1}). Retrying in {delay}s...")
                        time.sleep(delay)
                        continue  # retry loop
                    else:
                        print("Error: OpenAI API rate limit exceeded after 3 attempts.")
                        # Fall through to raise the exception on final attempt
                # If authentication or credentials issue, provide clear message (caught upstream as well)
                elif "api key" in err_msg or "authentication" in err_msg:
                    print("OpenAI API error: Authentication failed (invalid API key).")
                # Re-raise the exception for any non-retried or final errors
                raise
    
    def _complete_anthropic(self, system: str, user: str, temperature: float, max_tokens: int) -> str:
        """Complete using Anthropic API with retry on rate limits."""
        for attempt in range(3):  # try up to 3 times
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
                err_msg = str(e).lower()
                # If rate limit encountered, backoff and retry
                if "rate limit" in err_msg or "rate exceeded" in err_msg:
                    if attempt < 2:  # not last attempt
                        delay = 2 ** attempt  # exponential backoff: 1s, 2s, ...
                        print(f"Warning: Anthropic rate limit hit (attempt {attempt+1}). Retrying in {delay}s...")
                        time.sleep(delay)
                        continue  # retry loop
                    else:
                        print("Error: Anthropic API rate limit exceeded after retries.")
                        # Fall through to raise the exception on final attempt
                # If authentication or credentials issue, provide clear message (caught upstream as well)
                if "api key" in err_msg or "authentication" in err_msg:
                    print("Anthropic API error: Authentication failed (invalid API key).")
                # Re-raise the exception for any non-retried or final errors
                raise


def parse_plan(response: str) -> Dict[str, Any]:
    """
    Parse the LLM's planning response into a structured plan.
    
    Args:
        response: The LLM's response text
        
    Returns:
        Structured plan dictionary
    """
    # Try to parse as JSON first
    if "{" in response and "}" in response:
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            plan_json = json.loads(response[start:end])
            # Clean any formatting artifacts in the JSON fields
            if isinstance(plan_json, dict):
                if "approach" in plan_json and isinstance(plan_json["approach"], str):
                    plan_json["approach"] = re.sub(r'\*\*|\*|`', '', plan_json["approach"]).strip()
                if "steps" in plan_json and isinstance(plan_json["steps"], list):
                    plan_json["steps"] = [re.sub(r'\*\*|\*|`', '', str(s)).strip() for s in plan_json["steps"]]
                if "priority_tests" in plan_json and isinstance(plan_json["priority_tests"], list):
                    plan_json["priority_tests"] = [re.sub(r'\*\*|\*|`', '', str(t)).strip().strip('"\'`') for t in plan_json["priority_tests"]]
            return plan_json
        except Exception:
            pass
    
    # If JSON parse failed, fall back to parsing as text list
    lines = response.strip().split('\n')
    steps: List[str] = []
    approach_text: Optional[str] = None
    priority_list: List[str] = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Extract approach if explicitly provided (e.g., "Approach: ...")
        if re.match(r'(?i)^(approach|strategy)[:\\-\\s]', line):
            approach_text = re.split(r'[:\\-]', line, 1)[1].strip()
            approach_text = re.sub(r'\*\*|\*|`', '', approach_text).strip()
            continue
        
        # Extract priority tests if mentioned (e.g., "Priority tests: ...")
        if re.match(r'(?i)^.*(priority\s*tests?|tests?\s*to\s*prioritize)[:\\-\\s]', line):
            # Get text after the separator (colon or hyphen)
            prt = line.split(':', 1)[1] if ':' in line else line.split('-', 1)[1] if '-' in line else line
            for item in re.split(r'[,\s]+', prt):
                item_clean = item.strip().strip('`"\'')
                if item_clean:
                    priority_list.append(re.sub(r'\*\*|\*|`', '', item_clean))
            continue
        
        # Identify step lines (numbered or bullet) and clean them
        if line[0].isdigit() or line.startswith('-') or line.startswith('*'):
            cleaned = re.sub(r'^[\d\.\-\*\s]+', '', line).strip()
            if cleaned:
                cleaned = re.sub(r'\*\*|\*|`', '', cleaned).strip()
                steps.append(cleaned)
    
    # Construct the plan dictionary
    if steps:
        return {
            "approach": approach_text if approach_text else "Fix failing tests systematically",
            "steps": steps,
            **({"priority_tests": priority_list} if priority_list else {})
        }
    else:
        # If no steps were parsed, treat the whole response as the approach
        approach_full = re.sub(r'\*\*|\*|`', '', response.strip())
        plan = {"approach": approach_full, "steps": []}
        if priority_list:
            plan["priority_tests"] = priority_list
        return plan


def build_planner_prompt(failing_tests: List[Dict[str, Any]], critic_feedback: Optional[str] = None) -> str:
    """
    Build a prompt for the planner to analyze failures and create a fix strategy.
    
    Args:
        failing_tests: List of failing test details
        critic_feedback: Optional feedback from previous critic rejection
        
    Returns:
        Formatted prompt string
    """
    prompt = ""
    
    # Include critic feedback if available
    if critic_feedback:
        prompt += "⚠️ PREVIOUS ATTEMPT REJECTED:\n"
        prompt += f"The critic rejected the last patch with this feedback:\n"
        prompt += f'"{critic_feedback}"\n\n'
        prompt += "Please create a NEW plan that addresses this feedback and avoids the same mistakes.\n\n"
    
    prompt += "🎯 DETERMINISTIC MULTI-FAILURE FIX STRATEGY\n\n"
    prompt += "You have multiple failing tests. Your goal is to fix ALL of them in ONE CYCLE.\n"
    prompt += "Do NOT fix them one-by-one. Plan and execute ALL fixes before running tests again.\n\n"
    
    prompt += f"TOTAL FAILING TESTS: {len(failing_tests)}\n\n"
    prompt += "DETAILED FAILURE ANALYSIS:\n"
    prompt += "| Test Name | File | Line | Error Message |\n"
    prompt += "|-----------|------|------|---------------|\n"
    
    # Show all tests (or up to 20 for very large suites)
    for i, test in enumerate(failing_tests[:20]):
        name = test.get('name', 'unknown')[:40]
        file = test.get('file', 'unknown')[:30]
        line = test.get('line', 0)
        error = test.get('short_traceback', '')
        if error:
            # Get the actual error message, not just first line
            error_lines = error.split('\n')
            # Look for assertion errors or exception messages
            for err_line in error_lines:
                if 'AssertionError:' in err_line or 'Error:' in err_line or 'assert' in err_line:
                    error = err_line.strip()[:80]
                    break
            else:
                error = error_lines[0][:80]
        else:
            error = 'No error details'
        
        prompt += f"| {name} | {file} | {line} | {error} |\n"
    
    if len(failing_tests) > 20:
        prompt += f"\n... and {len(failing_tests) - 20} more failing tests\n"
    
    prompt += "\n"
    prompt += "REQUIRED PLANNING APPROACH:\n"
    prompt += "1. Analyze ALL failures to understand the pattern\n"
    prompt += "2. Create a SINGLE comprehensive plan that addresses EVERY failure\n"
    prompt += "3. List specific fixes for EACH failing function/method\n"
    prompt += "4. Execute ALL fixes sequentially WITHOUT running tests until done\n"
    prompt += "5. Only run tests ONCE after ALL fixes are applied\n\n"
    
    prompt += "Provide a structured plan in JSON format with keys 'approach', 'steps', and 'priority_tests'.\n"
    prompt += "Your 'steps' MUST enumerate a fix for EACH failing test.\n"
    prompt += "Respond only with a JSON object containing:\n"
    prompt += '- "approach": overall strategy to fix ALL tests in one go\n'
    prompt += '- "steps": ordered list with one step per failing function/test to fix\n'
    prompt += '- "priority_tests": list ALL failing test names (not just a subset)\n\n'
    prompt += "Example format:\n"
    prompt += "{\n"
    prompt += '  "approach": "Fix all 5 failing functions by adding proper error handling and type checks",\n'
    prompt += '  "steps": [\n'
    prompt += '    "Fix divide_numbers: Add TypeError handling for non-numeric inputs",\n'
    prompt += '    "Fix validate_age: Add ValidationError for invalid ages",\n'
    prompt += '    "Fix process_data: Handle None/empty data with ValueError",\n'
    prompt += '    "Fix FileProcessor: Add FileNotFoundError handling",\n'
    prompt += '    "Fix safe_conversion: Handle unsupported types",\n'
    prompt += '    "Apply all fixes and run tests once to verify"\n'
    prompt += "  ],\n"
    prompt += '  "priority_tests": ["test_divide_numbers", "test_validate_age", ...]\n'
    prompt += "}\n"
    prompt += "Remember: Fix ALL tests in ONE iteration. Do NOT test after each fix."
    
    return prompt


def build_patch_prompt(plan: Dict[str, Any], failing_tests: List[Dict[str, Any]], 
                       test_contents: Dict[str, str] = None, 
                       source_contents: Dict[str, str] = None,
                       critic_feedback: Optional[str] = None) -> str:
    """
    Build a prompt for the actor to generate a patch based on the plan.
    
    Args:
        plan: The plan created by the planner
        failing_tests: List of failing test details
        test_contents: Optional dict of test file contents
        source_contents: Optional dict of source file contents
        critic_feedback: Optional feedback from previous critic rejection
        
    Returns:
        Formatted prompt string
    """
    prompt = ""
    
    # Include critic feedback if available
    if critic_feedback:
        prompt += "⚠️ PREVIOUS PATCH REJECTED:\n"
        prompt += f'"{critic_feedback}"\n\n'
        prompt += "Generate a DIFFERENT patch that avoids these issues.\n\n"
    
    prompt += "Generate a unified diff patch to fix the failing tests.\n\n"
    
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
    
    # Include failing test details with clear actual vs expected
    prompt += "FAILING TESTS TO FIX:\n"
    for i, test in enumerate(failing_tests[:3], 1):
        prompt += f"\n{i}. Test: {test.get('name', 'unknown')}\n"
        prompt += f"   File: {test.get('file', 'unknown')}\n"
        prompt += f"   Line: {test.get('line', 0)}\n"
        
        # Extract actual vs expected from error message if present
        error_msg = test.get('short_traceback', 'No traceback')[:400]
        prompt += f"   Error:\n{error_msg}\n"
        
        # Highlight the mismatch if we can identify it
        if "Expected" in error_msg and "but got" in error_msg:
            prompt += "   ⚠️ Pay attention to the EXACT expected vs actual values above!\n"
            prompt += "   If the expected value is logically wrong, fix the test, not the code.\n"
    
    # Include test file contents if provided
    if test_contents:
        prompt += "\n\nTEST FILE CONTENTS (modify ONLY if tests have wrong expectations):\n"
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
    prompt += "5. IMPORTANT: If a test expects an obviously wrong value (e.g., 2+2=5, sum([1,2,3,4,5])=20), \n"
    prompt += "   fix the TEST's expectation, not the implementation\n"
    prompt += "6. Be minimal and focused\n"
    prompt += "7. DO NOT introduce arbitrary constants or magic numbers just to make tests pass\n"
    prompt += "8. DO NOT add/remove spaces or characters unless they logically belong there\n"
    prompt += "9. CRITICAL: When modifying functions, REPLACE the entire function definition and body.\n"
    prompt += "   DO NOT add duplicate 'def function_name():' lines.\n"
    prompt += "   The patch must show '-def function_name():' removing the old definition\n"
    prompt += "   and '+def function_name():' adding the new one.\n"
    prompt += "   NEVER have two consecutive 'def' lines for the same function.\n"
    prompt += "\n"
    prompt += "WARNING: Avoid quick hacks like hardcoding values. Focus on the root cause.\n"
    prompt += "If the test's expected value is mathematically or logically wrong, fix the test.\n"
    prompt += "\n"
    prompt += "CRITICAL: For function modifications, the patch must properly remove old lines with '-' and add new lines with '+'.\n"
    prompt += "Example of CORRECT patch for fixing a function:\n"
    prompt += "  -def add(a, b):\n"
    prompt += "  -    return a - b  # wrong\n"
    prompt += "  +def add(a, b):\n"
    prompt += "  +    return a + b  # fixed\n"
    prompt += "\n"
    prompt += "Return ONLY the unified diff, starting with --- and no other text."
    
    return prompt
