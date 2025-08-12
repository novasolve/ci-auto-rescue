from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from ..config import NovaSettings
from .http import AllowedHTTPClient


class OpenSWERequest(BaseModel):
    function_name: Optional[str] = Field(default=None)
    objective: str
    context_code: Optional[str] = Field(default=None)
    file_path: Optional[str] = Field(default=None)
    test_names: Optional[List[str]] = Field(default=None)


class OpenSWEResponse(BaseModel):
    code: Optional[str] = Field(default=None)
    diff: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)


class OpenSWEError(RuntimeError):
    pass


class OpenSWENotConfigured(OpenSWEError):
    pass


def call_openswe(
    req: OpenSWERequest,
    settings: NovaSettings,
    http: AllowedHTTPClient,
    *,
    timeout: float = 60.0,
    retries: int = 3,
) -> OpenSWEResponse:
    """Call the OpenSWE service with allow-list enforcement and retries.

    The settings.openswe_base_url is treated as a full endpoint URL. The request
    body mirrors OpenSWERequest. Authorization uses openswe_api_key when present
    via a Bearer token.
    """
    if not settings.openswe_base_url:
        raise OpenSWENotConfigured("OPENSWE_BASE_URL is not configured")

    url = settings.openswe_base_url.rstrip("/")
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if settings.openswe_api_key:
        headers["Authorization"] = f"Bearer {settings.openswe_api_key}"

    resp = http.post(
        url,
        json=req.model_dump(exclude_none=True),
        headers=headers,
        retries=retries,
        timeout=timeout,
    )

    if resp.status_code != 200:
        # Limit error body size
        text = resp.text
        if len(text) > 500:
            text = text[:500] + "..."
        raise OpenSWEError(f"OpenSWE HTTP {resp.status_code}: {text}")

    try:
        data = resp.json()
    except Exception as e:
        raise OpenSWEError("Invalid JSON from OpenSWE") from e

    try:
        return OpenSWEResponse.model_validate(data)  # type: ignore[attr-defined]
    except Exception:
        # Fallback for older pydantic usage
        return OpenSWEResponse(**{k: data.get(k) for k in ("code", "diff", "notes")})


__all__ = [
    "OpenSWERequest",
    "OpenSWEResponse",
    "OpenSWEError",
    "OpenSWENotConfigured",
    "call_openswe",
]
