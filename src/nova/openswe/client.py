from __future__ import annotations

import difflib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..settings import get_settings, NovaSettings
from ..telemetry import TelemetryRun


class OpenSWEError(Exception):
    pass


class NetworkNotAllowed(OpenSWEError):
    pass


def _check_allowlist(url: str, settings: NovaSettings) -> None:
    host = urlparse(url).netloc.split(":")[0]
    if host not in settings.NETWORK_ALLOWLIST:
        raise NetworkNotAllowed(f"Host not in allowlist: {host}")


@dataclass
class OpenSWERequest:
    objective: str
    function_name: Optional[str] = None
    context_code: Optional[str] = None
    file_path: Optional[str] = None
    additional_notes: Optional[str] = None


@dataclass
class OpenSWEResponse:
    code: str
    diff: Optional[str] = None
    notes: Optional[str] = None


class OpenSWEClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, telemetry: Optional[TelemetryRun] = None, timeout_s: int = 60) -> None:
        self.settings = get_settings()
        self.base_url = base_url or (self.settings.OPENSWE_BASE_URL or "")
        self.api_key = api_key or (self.settings.OPENSWE_API_KEY or "")
        self.telemetry = telemetry
        self.timeout_s = timeout_s
        self._client = httpx.Client(timeout=self.timeout_s)
        if not self.base_url:
            # Allow creating client without URL; calls will fail if used
            pass

    def _log(self, kind: str, payload: Dict[str, Any]) -> None:
        if self.telemetry:
            self.telemetry.log_event({"event": f"openswe_{kind}", **payload})

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    def generate(self, req: OpenSWERequest) -> OpenSWEResponse:
        if not self.base_url:
            raise OpenSWEError("OpenSWE base URL not configured")
        _check_allowlist(self.base_url, self.settings)
        url = self.base_url.rstrip("/") + "/generate"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        body = {
            "objective": req.objective,
            "function_name": req.function_name,
            "context_code": req.context_code,
            "file_path": req.file_path,
            "additional_notes": req.additional_notes,
        }
        self._log("request", {"endpoint": url, "objective": req.objective[:200]})
        try:
            resp = self._client.post(url, headers=headers, json=body)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise OpenSWEError(f"OpenSWE request failed: {e}") from e
        data = resp.json()
        code = data.get("code") or data.get("snippet") or ""
        diff = data.get("diff")
        notes = data.get("notes")
        self._log("response", {"endpoint": url, "received_code": bool(code), "has_diff": bool(diff)})
        return OpenSWEResponse(code=code, diff=diff, notes=notes)

    @staticmethod
    def to_unified_diff(file_path: str, original_text: str, updated_text: str) -> str:
        a = original_text.splitlines(keepends=True)
        b = updated_text.splitlines(keepends=True)
        diff = difflib.unified_diff(a, b, fromfile=f"a/{file_path}", tofile=f"b/{file_path}")
        return "".join(diff)
