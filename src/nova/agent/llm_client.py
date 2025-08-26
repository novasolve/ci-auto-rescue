"""
Unified LLM client for Nova CI-Rescue supporting OpenAI and Anthropic.
"""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timezone
import os

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
import time


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
        
        # Map special names to actual API model names
        if model == "gpt-5-chat-latest":
            # Use full GPT-5 model
            return "gpt-5"
        elif "gpt-5" in model.lower():
            # Use the GPT-5 variant requested
            if "mini" in model.lower():
                return "gpt-5-mini"
            elif "nano" in model.lower():
                return "gpt-5-nano"
            else:
                # Default to full GPT-5 model for best reasoning
                return "gpt-5"
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
        # Log the request details
        print(f"[Nova Debug - LLM] Provider: {self.provider}, Model: {self.model}")
        print(f"[Nova Debug - LLM] Request params: temperature={temperature}, max_tokens={max_tokens}")
        print(f"[Nova Debug - LLM] System prompt length: {len(system)} chars")
        print(f"[Nova Debug - LLM] User prompt length: {len(user)} chars")
        
        # Daily usage tracking and alerts
        self._increment_daily_usage()
        start = time.time()
        try:
            if self.provider == "openai":
                return self._complete_openai(system, user, temperature, max_tokens)
            elif self.provider == "anthropic":
                return self._complete_anthropic(system, user, temperature, max_tokens)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
        finally:
            elapsed = time.time() - start
            if elapsed > self.settings.llm_call_timeout_sec:
                print(f"[Nova Warn] LLM call exceeded {self.settings.llm_call_timeout_sec}s (took {int(elapsed)}s)")

    def _usage_path(self) -> Path:
        root = Path(os.path.expanduser("~")) / ".nova"
        try:
            root.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return root / "usage.json"

    def _increment_daily_usage(self) -> None:
        try:
            path = self._usage_path()
            data: Dict[str, Any] = {}
            if path.exists():
                try:
                    data = json.loads(path.read_text() or "{}")
                except Exception:
                    data = {}
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            counts = data.get(today, {"calls": 0})
            counts["calls"] = int(counts.get("calls", 0)) + 1
            data[today] = counts
            try:
                path.write_text(json.dumps(data))
            except Exception:
                pass
            # Alerts
            max_calls = int(getattr(self.settings, "max_daily_llm_calls", 0) or 0)
            warn_pct = float(getattr(self.settings, "warn_daily_llm_calls_pct", 0.8) or 0.8)
            if max_calls > 0:
                warn_threshold = int(max_calls * warn_pct)
                if counts["calls"] == warn_threshold:
                    print(f"[Nova Warn] Daily LLM calls reached {counts['calls']}/{max_calls} ({int(warn_pct*100)}%).")
                if counts["calls"] > max_calls:
                    print(f"[Nova Warn] Daily LLM calls exceeded limit: {counts['calls']}/{max_calls}. Consider pausing or lowering usage.")
        except Exception:
            # Never block on usage tracking
            pass
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def _complete_openai(self, system: str, user: str, temperature: float, max_tokens: int) -> str:
        """Complete using OpenAI API."""
        try:
            # Use Chat Completions API for all models
            # Build kwargs
            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ]
            }
            
            # Handle model-specific parameters
            if "gpt-5" in self.model.lower():
                # GPT-5 uses max_completion_tokens instead of max_tokens
                kwargs["max_completion_tokens"] = max_tokens
                # GPT-5 only supports temperature=1.0
                kwargs["temperature"] = 1.0
                # Set reasoning effort to high for maximum reasoning quality
                kwargs["reasoning_effort"] = "high"
            else:
                kwargs["max_tokens"] = max_tokens
                kwargs["temperature"] = temperature
            
            response = self.client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            if content:
                content = content.strip()
                print(f"[Nova Debug - LLM] OpenAI response length: {len(content)} chars")
                print(f"[Nova Debug - LLM] Response preview (first 100 chars): {content[:100]}...")
            else:
                print(f"[Nova Debug - LLM] WARNING: OpenAI returned None/empty content!")
                content = ""
            return content
                
        except Exception as e:
            print(f"[Nova Debug - LLM] OpenAI API error: {type(e).__name__}: {e}")
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
            if response.content and len(response.content) > 0:
                content = response.content[0].text
                if content:
                    content = content.strip()
                    print(f"[Nova Debug - LLM] Anthropic response length: {len(content)} chars")
                    print(f"[Nova Debug - LLM] Response preview (first 100 chars): {content[:100]}...")
                else:
                    print(f"[Nova Debug - LLM] WARNING: Anthropic returned None/empty text!")
                    content = ""
            else:
                print(f"[Nova Debug - LLM] WARNING: Anthropic returned empty content array!")
                content = ""
            return content
        except Exception as e:
            print(f"[Nova Debug - LLM] Anthropic API error: {type(e).__name__}: {e}")
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
        except json.JSONDecodeError as e:
            # JSON parsing failed, fall back to bullet parsing
            pass
        except Exception as e:
            # Other unexpected error, fall back to bullet parsing
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
    
    prompt += "Analyze these failing tests and create a plan to fix them:\n\n"
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
    prompt += "\n"
    prompt += "WARNING: Avoid quick hacks like hardcoding values. Focus on the root cause.\n"
    prompt += "If the test's expected value is mathematically or logically wrong, fix the test.\n"
    prompt += "\n"
    prompt += "Return ONLY the unified diff, starting with --- and no other text."
    
    return prompt
