"""
Unified LLM interface for Nova CI-Rescue.
All LLM calls should go through this module for consistency and maintainability.
"""

import os
import time
from typing import Optional, Dict, Any, Tuple
from nova.agent.llm_client import LLMClient


class UnifiedLLMInterface:
    """Centralized interface for all LLM interactions in Nova."""
    
    def __init__(self, verbose: bool = False):
        self.client = LLMClient()
        self.verbose = verbose
    
    def _get_reasoning_params(self, task_type: str) -> Tuple[str, str]:
        """Get optimal reasoning effort and verbosity for different tasks."""
        # Based on GPT-5 documentation recommendations
        if task_type == "critic":
            # Fast, concise feedback
            return "minimal", "low"
        elif task_type == "planner":
            # Balanced planning
            return "medium", "medium"
        elif task_type == "actor":
            # Best code generation
            return "high", "high"
        else:
            # Default to high quality
            return "high", "medium"
    
    def _get_temperature(self, task_type: str) -> float:
        """Get optimal temperature for different tasks."""
        # GPT-5 always uses 1.0, others vary by task
        if self.client.provider == "openai" and "gpt-5" in self.client.model.lower():
            return 1.0
        
        # For non-GPT-5 models
        if task_type == "critic":
            return 0.1  # Low temperature for consistent evaluation
        elif task_type == "planner":
            return 0.3  # Medium temperature for planning
        elif task_type == "actor":
            return 1.0  # High temperature for creative code generation
        else:
            return 0.3  # Default
    
    def complete_with_retries(
        self, 
        system: str,
        user: str,
        task_type: str,
        max_tokens: int = 2000,
        retries: int = 3,
        base_tokens: Optional[int] = None,
        retry_increment: int = 200
    ) -> Optional[str]:
        """
        Complete with automatic retries and optimal parameters for task type.
        
        Args:
            system: System prompt
            user: User prompt
            task_type: One of "critic", "planner", "actor", or "general"
            max_tokens: Maximum tokens (or base tokens if base_tokens is set)
            retries: Number of retry attempts
            base_tokens: If set, max_tokens increases with each retry
            retry_increment: How much to increase tokens on each retry
            
        Returns:
            The LLM response or None if all attempts fail
        """
        # Get optimal parameters for this task type
        reasoning_effort, verbosity = self._get_reasoning_params(task_type)
        base_temperature = self._get_temperature(task_type)
        
        # Get retry settings from environment if available
        env_retries = os.getenv(f"NOVA_{task_type.upper()}_RETRIES")
        if env_retries:
            retries = int(env_retries)
        
        env_tokens = os.getenv(f"NOVA_{task_type.upper()}_MAX_TOKENS")
        if env_tokens:
            max_tokens = int(env_tokens)
            if base_tokens is None:
                base_tokens = max_tokens
        
        # If base_tokens is set, we'll increment max_tokens each retry
        if base_tokens is None:
            base_tokens = max_tokens
        
        response = ""
        last_error = None
        
        for attempt in range(max(1, retries)):
            try:
                # Calculate tokens for this attempt
                current_tokens = base_tokens + (attempt * retry_increment)
                
                # Slightly increase temperature on retries for variety
                temperature = base_temperature
                if attempt > 0 and task_type != "critic":
                    temperature = min(1.0, base_temperature + 0.1)
                
                if self.verbose:
                    print(f"[Nova Debug - {task_type.title()}] Attempt {attempt + 1}/{retries}, "
                          f"temperature={temperature}, max_tokens={current_tokens}")
                
                # Make the LLM call with task-specific parameters
                response = self.client.complete(
                    system=system,
                    user=user,
                    temperature=temperature,
                    max_tokens=current_tokens,
                    reasoning_effort=reasoning_effort,
                    verbosity=verbosity
                )
                
                if response and response.strip():
                    if self.verbose:
                        print(f"[Nova Debug - {task_type.title()}] Got response of {len(response)} chars")
                    return response
                else:
                    if self.verbose:
                        print(f"[Nova Debug - {task_type.title()}] WARNING: Empty response on attempt {attempt + 1}")
                        
            except Exception as e:
                last_error = e
                if self.verbose:
                    print(f"[Nova Debug - {task_type.title()}] Error on attempt {attempt + 1}: "
                          f"{type(e).__name__}: {e}")
                response = ""
            
            # Brief backoff between retries
            if attempt < retries - 1:
                time.sleep(0.2 * (attempt + 1))
        
        # All attempts failed
        if self.verbose:
            print(f"[Nova Debug - {task_type.title()}] ERROR: No response after {retries} attempts")
            if last_error:
                print(f"[Nova Debug - {task_type.title()}] Last error: {last_error}")
        
        return None
    
    def critic_review(self, system: str, user: str) -> Optional[str]:
        """Specialized method for critic reviews."""
        return self.complete_with_retries(
            system=system,
            user=user,
            task_type="critic",
            base_tokens=int(os.getenv("NOVA_CRITIC_MAX_TOKENS", "800")),
            retries=int(os.getenv("NOVA_CRITIC_RETRIES", "3"))
        )
    
    def planner_plan(self, system: str, user: str) -> Optional[str]:
        """Specialized method for planner."""
        return self.complete_with_retries(
            system=system,
            user=user,
            task_type="planner",
            base_tokens=int(os.getenv("NOVA_PLANNER_MAX_TOKENS", "800")),
            retries=int(os.getenv("NOVA_PLANNER_RETRIES", "3"))
        )
    
    def actor_generate(self, system: str, user: str) -> Optional[str]:
        """Specialized method for actor code generation."""
        return self.complete_with_retries(
            system=system,
            user=user,
            task_type="actor",
            max_tokens=8000,  # Actor needs more tokens
            retries=int(os.getenv("NOVA_ACTOR_RETRIES", "3"))
        )
    
    def general_complete(self, system: str, user: str, max_tokens: int = 2000) -> Optional[str]:
        """General purpose completion."""
        return self.complete_with_retries(
            system=system,
            user=user,
            task_type="general",
            max_tokens=max_tokens,
            retries=3
        )
