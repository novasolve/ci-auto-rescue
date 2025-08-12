from __future__ import annotations

from typing import Optional, Any, Dict, List

from ..config import NovaSettings
from ..tools.http import AllowedHTTPClient


class NotConfiguredError(RuntimeError):
    pass


class LLMClient:
    """Minimal LLM adapter using OpenAI Chat Completions over HTTP.

    Uses AllowedHTTPClient to enforce outbound network allow-list. If
    OPENAI_API_KEY is not configured, raise NotConfiguredError.
    """

    def __init__(self, settings: NovaSettings, http: Optional[AllowedHTTPClient] = None) -> None:
        self.settings = settings
        self.http = http or AllowedHTTPClient(settings)

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        if not self.settings.openai_api_key:
            raise NotConfiguredError("OPENAI_API_KEY is not configured")

        model_name = model or self.settings.default_llm_model
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model_name,
            "messages": messages,
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
        }
        resp = self.http.post(url, json=body, headers=headers, retries=2, timeout=60.0)
        if resp.status_code != 200:
            # Try to extract error message
            try:
                data = resp.json()
                err = data.get("error", {}).get("message") if isinstance(data, dict) else None
            except Exception:
                err = None
            msg = f"OpenAI API error {resp.status_code}: {err or resp.text[:200]}"
            if resp.status_code in (401, 403):
                raise NotConfiguredError(msg)
            raise RuntimeError(msg)

        data: Dict[str, Any] = resp.json()
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("OpenAI API returned no choices")
        first = choices[0]
        message = (first.get("message") or {})
        content = message.get("content")
        if not content:
            # Some models might stream tool calls; keep simple for now
            raise RuntimeError("OpenAI API returned empty content")
        return str(content)


__all__ = ["LLMClient", "NotConfiguredError"]
