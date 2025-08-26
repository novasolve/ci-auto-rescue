"""
Unified LLM interface for Nova CI-Rescue.

All LLM calls should go through this module for consistency and maintainability.

Fixes:
- Removes use of unsupported parameter `response_format.verbosity`.
- Uses only `reasoning_effort` for models that support it; gracefully
  disables if the provider/model rejects reasoning parameters.
"""

import os
import time
from typing import Optional
from nova.agent.llm_client import LLMClient


class UnifiedLLMInterface:
    """Centralized interface for all LLM interactions in Nova."""

    def __init__(self, verbose: bool = False):
        self.client = LLMClient()
        self.verbose = verbose

    # -------- Parameter helpers ------------------------------------------------

    def _get_reasoning_effort(self, task_type: str) -> str:
        """
        Map task type to OpenAI-style reasoning effort values: low|medium|high.
        """
        mapping = {
            "critic": "low",     # fast, deterministic feedback
            "planner": "medium", # balanced depth/speed
            "actor": "high",     # best codegen
        }
        return mapping.get(task_type, "medium")

    def _get_temperature(self, task_type: str) -> float:
        """
        Pick temperature based on task type. If GPT‑5/OpenAI is in use,
        we still allow explicit temperature unless your client overrides it.
        """
        # Prefer stable outputs for critic/planner; more creative for actor.
        if task_type == "critic":
            return 0.1
        if task_type == "planner":
            return 0.3
        if task_type == "actor":
            return 1.0
        return 0.3

    def _is_reasoning_model(self) -> bool:
        """
        Heuristic: enable reasoning_effort only for OpenAI reasoning-capable models.
        Adjust tokens as your catalog evolves.
        """
        provider = getattr(self.client, "provider", "").lower()
        model = getattr(self.client, "model", "").lower()
        if provider != "openai":
            return False
        # Common patterns for reasoning-capable models (extend as needed).
        reasoning_markers = ("gpt-5", "o4", "o3")
        return any(m in model for m in reasoning_markers)

    # -------- Core call with retries -------------------------------------------

    def complete_with_retries(
        self,
        system: str,
        user: str,
        task_type: str,
        max_tokens: int = 2000,
        retries: int = 3,
        base_tokens: Optional[int] = None,
        retry_increment: int = 200,
    ) -> Optional[str]:
        """
        Complete with automatic retries and task-aware parameters.

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
        # Task-specific params
        reasoning_effort = self._get_reasoning_effort(task_type)
        base_temperature = self._get_temperature(task_type)

        # Env overrides
        env_retries = os.getenv(f"NOVA_{task_type.upper()}_RETRIES")
        if env_retries:
            try:
                retries = max(1, int(env_retries))
            except ValueError:
                pass

        env_tokens = os.getenv(f"NOVA_{task_type.upper()}_MAX_TOKENS")
        if env_tokens:
            try:
                max_tokens = int(env_tokens)
                if base_tokens is None:
                    base_tokens = max_tokens
            except ValueError:
                pass

        if base_tokens is None:
            base_tokens = max_tokens

        response = ""
        last_error: Optional[Exception] = None

        # Parameter negotiation flags (auto-disable on provider reject)
        allow_reasoning = self._is_reasoning_model()

        for attempt in range(max(1, retries)):
            current_tokens = base_tokens + (attempt * retry_increment)

            # Slightly increase temperature on retries (non-critic) for variety
            temperature = base_temperature
            if attempt > 0 and task_type != "critic":
                temperature = min(1.0, base_temperature + 0.1)

            # Build request kwargs — IMPORTANT: no 'verbosity' anywhere.
            kwargs = dict(
                system=system,
                user=user,
                temperature=temperature,
                max_tokens=current_tokens,
            )
            if allow_reasoning:
                # Your LLMClient already understands 'reasoning_effort'
                # (as evidenced in your logs). We avoid any response_format.*.
                kwargs["reasoning_effort"] = reasoning_effort

            if self.verbose:
                total = max(1, retries)
                print(
                    f"[Nova Debug - {task_type.title()}] Attempt {attempt + 1}/{total}, "
                    f"temperature={temperature}, max_tokens={current_tokens}, "
                    f"allow_reasoning={allow_reasoning}"
                )

            try:
                response = self.client.complete(**kwargs)

                if response and str(response).strip():
                    if self.verbose:
                        print(
                            f"[Nova Debug - {task_type.title()}] Got response of "
                            f"{len(str(response))} chars"
                        )
                    return response

                if self.verbose:
                    print(f"[Nova Debug - {task_type.title()}] WARNING: Empty response on attempt {attempt + 1}")

            except Exception as e:  # rely on client to raise provider-specific errors
                last_error = e
                msg = str(e)
                if self.verbose:
                    print(f"[Nova Debug - {task_type.title()}] Error on attempt {attempt + 1}: {type(e).__name__}: {e}")

                # If the model/provider rejects reasoning parameters, disable and retry.
                if allow_reasoning and ("reasoning_effort" in msg or "reasoning" in msg):
                    allow_reasoning = False
                    if self.verbose:
                        print(f"[Nova Debug - {task_type.title()}] Disabling reasoning_effort and retrying …")
                    # small backoff then continue to next attempt
                    time.sleep(0.2 * (attempt + 1))
                    continue

                # Note: We intentionally do not special-case verbosity here —
                # we never send any verbosity or response_format fields.

            # Backoff (if more retries remain)
            if attempt < retries - 1:
                time.sleep(0.2 * (attempt + 1))

        # All attempts failed
        if self.verbose:
            print(f"[Nova Debug - {task_type.title()}] ERROR: No response after {retries} attempts")
            if last_error:
                print(f"[Nova Debug - {task_type.title()}] Last error: {last_error}")
        return None

    # -------- Convenience wrappers ---------------------------------------------

    def critic_review(self, system: str, user: str) -> Optional[str]:
        """Specialized method for critic reviews."""
        return self.complete_with_retries(
            system=system,
            user=user,
            task_type="critic",
            base_tokens=int(os.getenv("NOVA_CRITIC_MAX_TOKENS", "800")),
            retries=int(os.getenv("NOVA_CRITIC_RETRIES", "3")),
        )

    def planner_plan(self, system: str, user: str) -> Optional[str]:
        """Specialized method for planning."""
        return self.complete_with_retries(
            system=system,
            user=user,
            task_type="planner",
            base_tokens=int(os.getenv("NOVA_PLANNER_MAX_TOKENS", "800")),
            retries=int(os.getenv("NOVA_PLANNER_RETRIES", "3")),
        )

    def actor_generate(self, system: str, user: str) -> Optional[str]:
        """Specialized method for actor code generation."""
        return self.complete_with_retries(
            system=system,
            user=user,
            task_type="actor",
            max_tokens=8000,  # actor typically needs longer outputs
            retries=int(os.getenv("NOVA_ACTOR_RETRIES", "3")),
        )

    def general_complete(self, system: str, user: str, max_tokens: int = 2000) -> Optional[str]:
        """General purpose completion."""
        return self.complete_with_retries(
            system=system,
            user=user,
            task_type="general",
            max_tokens=max_tokens,
            retries=3,
        )
