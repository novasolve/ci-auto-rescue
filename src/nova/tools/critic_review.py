"""
Critic Review Tool for Nova Deep Agent
=======================================

DEPRECATED: This file is being replaced by nova.agent.unified_tools.
Please use CriticReviewTool from the unified tools module instead.

This file is kept for backward compatibility but will be removed in a future version.
"""

from typing import Optional, Type, List, Dict, Any
from pathlib import Path
import json
import re

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    from langchain.chat_models import ChatOpenAI

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None


class CriticReviewInput(BaseModel):
    """Input schema for CriticReviewTool."""
    patch_diff: str = Field(
        description="The patch diff to review"
    )
    failing_tests: Optional[str] = Field(
        default=None,
        description="Optional context about failing tests"
    )


class CriticReviewTool(BaseTool):
    """
    Tool to critically review a patch before applying.
    
    Combines safety checks with LLM-based semantic review.
    """
    name: str = "critic_review"
    description: str = (
        "Review a patch diff to decide if it should be applied. "
        "Returns 'APPROVED: reason' or 'REJECTED: reason'. "
        "Always review patches before applying them."
    )
    args_schema: Type[BaseModel] = CriticReviewInput
    
    verbose: bool = False
    llm: Optional[Any] = None
    
    # Safety patterns
    FORBIDDEN_PATTERNS = [
        r"test_.*\.py",  # Test files
        r".*_test\.py",  # Test files
        r"/tests?/",     # Test directories
        r"\.github/",    # GitHub workflows
        r"setup\.py",    # Setup files
        r"pyproject\.toml",  # Project config
        r"requirements.*\.txt",  # Dependencies
    ]
    
    def __init__(self, verbose: bool = False, llm: Optional[Any] = None, **kwargs):
        """Initialize with optional LLM for semantic review."""
        super().__init__(**kwargs)
        self.verbose = verbose
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.1)
    
    def _check_safety(self, patch_diff: str) -> tuple[bool, str]:
        """
        Perform safety checks on the patch.
        
        Returns:
            Tuple of (is_safe, reason)
        """
        lines = patch_diff.split("\n")
        
        # Check for test file modifications
        for line in lines:
            if line.startswith("+++") or line.startswith("---"):
                # Extract file path
                parts = line.split()
                if len(parts) >= 2:
                    file_path = parts[1]
                    if file_path.startswith("a/"):
                        file_path = file_path[2:]
                    elif file_path.startswith("b/"):
                        file_path = file_path[2:]
                    
                    # Check against forbidden patterns
                    for pattern in self.FORBIDDEN_PATTERNS:
                        if re.search(pattern, file_path):
                            return False, f"Modifies forbidden path: {file_path}"
        
        # Check patch size
        added = sum(1 for line in lines if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in lines if line.startswith("-") and not line.startswith("---"))
        
        if added + removed > 500:
            return False, f"Patch too large: {added} additions, {removed} deletions"
        
        # Check for suspicious patterns in additions
        suspicious = [
            r"exec\(",
            r"eval\(",
            r"__import__",
            r"os\.system",
            r"subprocess\.call\(",
            r"rm\s+-rf",
        ]
        
        for line in lines:
            if line.startswith("+"):
                for pattern in suspicious:
                    if re.search(pattern, line, re.IGNORECASE):
                        return False, f"Suspicious pattern detected: {pattern}"
        
        return True, "Safety checks passed"
    
    def _llm_review(self, patch_diff: str, failing_tests: Optional[str] = None) -> tuple[bool, str]:
        """
        Use LLM to semantically review the patch.
        
        Returns:
            Tuple of (approved, reason)
        """
        # Prepare the review prompt
        system_prompt = """You are a code reviewer for an AI test-fixing agent.
Review the patch and decide if it should be applied.
Consider:
1. Does it address the failing tests?
2. Is it minimal and focused?
3. Could it break existing functionality?
4. Does it follow good practices?

Respond with JSON: {"approved": true/false, "reason": "brief explanation"}"""
        
        user_prompt = f"""Review this patch:

```diff
{patch_diff[:3000]}  # Truncate for context window
```"""
        
        if failing_tests:
            user_prompt += f"\n\nFailing tests context:\n{failing_tests[:500]}"
        
        try:
            response = self.llm.predict(user_prompt, system=system_prompt)
            
            # Parse JSON response
            if "{" in response and "}" in response:
                start = response.index("{")
                end = response.rindex("}") + 1
                result = json.loads(response[start:end])
                return result.get("approved", False), result.get("reason", "No reason provided")
            else:
                return False, "Invalid review response format"
                
        except Exception as e:
            if self.verbose:
                print(f"LLM review error: {e}")
            return False, f"LLM review failed: {e}"
    
    def _run(self, patch_diff: str, failing_tests: Optional[str] = None) -> str:
        """
        Review the patch and return decision.
        
        Returns:
            "APPROVED: reason" or "REJECTED: reason"
        """
        # First, run safety checks
        safe, safety_reason = self._check_safety(patch_diff)
        
        if not safe:
            return f"REJECTED: {safety_reason}"
        
        # Then, run LLM review
        approved, llm_reason = self._llm_review(patch_diff, failing_tests)
        
        if approved:
            return f"APPROVED: {llm_reason}"
        else:
            return f"REJECTED: {llm_reason}"
    
    async def _arun(self, patch_diff: str, failing_tests: Optional[str] = None) -> str:
        """Async version not implemented."""
        raise NotImplementedError("CriticReviewTool does not support async execution")
