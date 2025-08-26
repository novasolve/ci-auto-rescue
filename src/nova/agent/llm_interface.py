"""
Unified LLM interface for Nova CI-Rescue.

Fixes & improvements:
- Removes unsupported `response_format.verbosity`.
- Enforces GPT-5's fixed temperature=1.0 with a single warning (planner/actor/etc.).
- Sends `reasoning_effort` only when likely supported; auto-disables on provider/model rejection.
- Consistent, minimal debug logging and adaptive retries.
"""

import os
import time
from typing import Optional
from nova.agent.llm_client import LLMClient


class LLMNoResponseError(Exception):
    def __init__(self, task_type: str, model: str, provider: str, attempts: int, last_error: Optional[Exception]):
        self.task_type = task_type
        self.model = model
        self.provider = provider
        self.attempts = attempts
        self.last_error = last_error
        message = (
            f"LLM returned no response after {attempts} attempt(s) "
            f"(task={task_type}, model={model}, provider={provider}). "
            f"Last error: {last_error!r}"
        )
        super().__init__(message)


class UnifiedLLMInterface:
    """Centralized interface for all LLM interactions in Nova."""

    # One-time warning flags per process
    _warned_fixed_temp: bool = False

    def __init__(self, verbose: bool = False):
        self.client = LLMClient()
        self.verbose = verbose

    # -------------------------------------------------------------------------
    # Capability heuristics
    # -------------------------------------------------------------------------

    def _provider(self) -> str:
        return getattr(self.client, "provider", "").lower()

    def _model(self) -> str:
        return getattr(self.client, "model", "").lower()

    def _is_reasoning_model(self) -> bool:
        """
        Heuristic: models that likely support `reasoning_effort`.
        Extend as catalog evolves.
        """
        if self._provider() != "openai":
            return False
        return any(tag in self._model() for tag in ("gpt-5", "o4", "o3"))

    def _fixed_temperature(self) -> Optional[float]:
        """
        Return a fixed temperature requirement if the model enforces one.
        From logs: GPT-5 requires temperature=1.0.
        """
        if self._provider() == "openai" and "gpt-5" in self._model():
            return 1.0
        return None

    # -------------------------------------------------------------------------
    # Task tuning
    # -------------------------------------------------------------------------

    def _get_reasoning_effort(self, task_type: str) -> str:
        """low|medium|high by task role."""
        return {
            "critic": "low",
            "planner": "medium",
            "actor": "high",
        }.get(task_type, "medium")

    def _get_base_temperature(self, task_type: str) -> float:
        """Stability for critic/planner, exploration for actor/general."""
        return {
            "critic": 0.1,
            "planner": 0.3,
            "actor": 1.0,
            "general": 0.3,
        }.get(task_type, 0.3)

    # -------------------------------------------------------------------------
    # Core call with retries
    # -------------------------------------------------------------------------

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
        Perform a completion request with automatic retries and adaptive params.
        """
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

        # Task defaults
        base_temperature = self._get_base_temperature(task_type)
        reasoning_effort = self._get_reasoning_effort(task_type)
        allow_reasoning = self._is_reasoning_model()

        # Model capability enforcement
        fixed_temp = self._fixed_temperature()
        if fixed_temp is not None and base_temperature != fixed_temp and not self._warned_fixed_temp:
            # Single, non-spammy warning
            print(f"[Nova Debug - LLM] NOTE: {self._model()} enforces temperature={fixed_temp}. Overriding requested {base_temperature}.")
            self.__class__._warned_fixed_temp = True
        if fixed_temp is not None:
            base_temperature = fixed_temp  # hard override for all attempts

        last_error: Optional[Exception] = None

        for attempt in range(max(1, retries)):
            current_tokens = base_tokens + (attempt * retry_increment)

            # Retry policy: for non-critic tasks, increase temp slightly — but respect fixed temp if present.
            if fixed_temp is not None:
                temperature = fixed_temp
            else:
                temperature = base_temperature if attempt == 0 or task_type == "critic" else min(1.0, base_temperature + 0.1 * attempt)

            kwargs = {
                "system": system,
                "user": user,
                "temperature": temperature,
                "max_tokens": current_tokens,
            }
            if allow_reasoning:
                kwargs["reasoning_effort"] = reasoning_effort  # never send any response_format.*

            if self.verbose:
                print(
                    f"[Nova Debug - {task_type.title()}] Attempt {attempt+1}/{retries}, "
                    f"temperature={temperature}, max_tokens={current_tokens}, "
                    f"allow_reasoning={allow_reasoning}"
                )

            try:
                response = self.client.complete(**kwargs)
                if response and str(response).strip():
                    if self.verbose:
                        print(f"[Nova Debug - {task_type.title()}] Received {len(str(response))} chars")
                    return response

                # Empty response case — log deeper debug info
                resp_type = type(response).__name__
                resp_preview = str(response)[:200] if response else "None"
                print(
                    f"[Nova Debug - {task_type.title()}] WARNING: Empty response on attempt {attempt+1} "
                    f"(model={self._model()}, provider={self._provider()}, "
                    f"tokens={current_tokens}, temp={temperature}, type={resp_type}, preview={resp_preview!r})"
                )

            except Exception as e:
                last_error = e
                msg = str(e)
                if self.verbose:
                    print(f"[Nova Debug - {task_type.title()}] Error on attempt {attempt+1}: {type(e).__name__}: {e}")

                # If provider/model rejects reasoning params, disable and retry.
                if allow_reasoning and "reasoning" in msg.lower():
                    allow_reasoning = False
                    if self.verbose:
                        print(f"[Nova Debug - {task_type.title()}] Disabling reasoning_effort and retrying…")
                    time.sleep(0.2 * (attempt + 1))
                    continue

            # Backoff before next retry (linear backoff is fine here)
            if attempt < retries - 1:
                time.sleep(0.2 * (attempt + 1))

        if self.verbose:
            print(f"[Nova Debug - {task_type.title()}] ERROR: No response after {retries} attempts")
            if last_error:
                print(f"[Nova Debug - {task_type.title()}] Last error: {last_error}")
        # Fail-fast: raise a descriptive exception so callers can exit early with context
        raise LLMNoResponseError(
            task_type=task_type,
            model=self._model(),
            provider=self._provider(),
            attempts=retries,
            last_error=last_error,
        )

    # -------------------------------------------------------------------------
    # Convenience wrappers
    # -------------------------------------------------------------------------

    def critic_review(self, system: str, user: str) -> Optional[str]:
        return self.complete_with_retries(
            system=system,
            user=user,
            task_type="critic",
            base_tokens=int(os.getenv("NOVA_CRITIC_MAX_TOKENS", "800")),
            retries=int(os.getenv("NOVA_CRITIC_RETRIES", "3")),
        )

    def planner_plan(self, system: str, user: str) -> Optional[str]:
        return self.complete_with_retries(
            system=system,
            user=user,
            task_type="planner",
            base_tokens=int(os.getenv("NOVA_PLANNER_MAX_TOKENS", "1200")),
            retries=int(os.getenv("NOVA_PLANNER_RETRIES", "3")),
        )

    def actor_generate(self, system: str, user: str) -> Optional[str]:
        return self.complete_with_retries(
            system=system,
            user=user,
            task_type="actor",
            max_tokens=8000,  # actor usually needs longer outputs
            retries=int(os.getenv("NOVA_ACTOR_RETRIES", "3")),
        )

    def general_complete(self, system: str, user: str, max_tokens: int = 2000) -> Optional[str]:
        return self.complete_with_retries(
            system=system,
            user=user,
            task_type="general",
            max_tokens=max_tokens,
            retries=3,
        )
