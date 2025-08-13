from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..settings import get_settings, NovaSettings
from ..telemetry import TelemetryRun


class LLMError(Exception):
    pass


class NetworkNotAllowed(LLMError):
    pass


def _check_allowlist(url: str, settings: NovaSettings) -> None:
    host = urlparse(url).netloc.split(":")[0]
    if host not in settings.NETWORK_ALLOWLIST:
        raise NetworkNotAllowed(f"Host not in allowlist: {host}")


class LLMClient:
    """Provider-agnostic LLM client for OpenAI/Anthropic chat-style models."""

    def __init__(
        self,
        provider: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        telemetry: Optional[TelemetryRun] = None,
        timeout_s: int = 60,
    ) -> None:
        self.settings = get_settings()
        self.provider = provider.lower()
        self.model = model or (self.settings.OPENAI_MODEL if self.provider == "openai" else self.settings.ANTHROPIC_MODEL)
        self.api_key = api_key or (
            self.settings.OPENAI_API_KEY if self.provider == "openai" else self.settings.ANTHROPIC_API_KEY
        )
        self.telemetry = telemetry
        self.timeout_s = timeout_s
        self._client = httpx.Client(timeout=self.timeout_s)

    def _log(self, kind: str, payload: Dict[str, Any]) -> None:
        if self.telemetry:
            self.telemetry.log_event({"event": f"llm_{kind}", **payload})

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception_type((httpx.HTTPError, LLMError)),
    )
    def complete(
        self,
        *,
        system: Optional[str] = None,
        user: Optional[str] = None,
        temperature: float = 0.2,
        json_schema: Optional[Dict[str, Any]] = None,
        max_tokens: int = 2048,
    ) -> str:
        if self.provider == "openai":
            return self._openai_complete(system=system, user=user, temperature=temperature, json_schema=json_schema, max_tokens=max_tokens)
        elif self.provider == "anthropic":
            return self._anthropic_complete(system=system, user=user, temperature=temperature, json_schema=json_schema, max_tokens=max_tokens)
        else:
            raise LLMError(f"Unsupported provider: {self.provider}")

    def _openai_complete(
        self,
        *,
        system: Optional[str],
        user: Optional[str],
        temperature: float,
        json_schema: Optional[Dict[str, Any]],
        max_tokens: int,
    ) -> str:
        base = "https://api.openai.com/v1/chat/completions"
        _check_allowlist(base, self.settings)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        if user:
            messages.append({"role": "user", "content": user})
        body: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_schema:
            # Use response_format json_schema if supported; otherwise rely on instruction-only schema adherence
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": json_schema,
            }
        self._log("request", {"provider": "openai", "model": self.model, "prompt": user or "", "system": bool(system)})
        try:
            resp = self._client.post(base, headers=headers, json=body)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise LLMError(f"OpenAI request failed: {e}") from e
        data = resp.json()
        try:
            text = data["choices"][0]["message"]["content"]
        except Exception:
            text = json.dumps(data)
        self._log("response", {"provider": "openai", "model": self.model, "response": text})
        return text

    def _anthropic_complete(
        self,
        *,
        system: Optional[str],
        user: Optional[str],
        temperature: float,
        json_schema: Optional[Dict[str, Any]],
        max_tokens: int,
    ) -> str:
        base = "https://api.anthropic.com/v1/messages"
        _check_allowlist(base, self.settings)
        headers = {
            "x-api-key": self.api_key or "",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body: Dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": user or ""}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            body["system"] = system
        if json_schema:
            body["response_format"] = {"type": "json_schema", "json_schema": json_schema}
        self._log("request", {"provider": "anthropic", "model": self.model, "prompt": user or "", "system": bool(system)})
        try:
            resp = self._client.post(base, headers=headers, json=body)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise LLMError(f"Anthropic request failed: {e}") from e
        data = resp.json()
        try:
            # messages[0].content is a list of blocks; pick text fields
            content = data.get("content") or data.get("messages", [{}])[0].get("content", [])
            if isinstance(content, list) and content:
                blocks = [b.get("text", "") if isinstance(b, dict) else str(b) for b in content]
                text = "\n".join(blocks)
            else:
                text = json.dumps(data)
        except Exception:
            text = json.dumps(data)
        self._log("response", {"provider": "anthropic", "model": self.model, "response": text})
        return text
