from __future__ import annotations

import time
from typing import Any, Dict, Iterable, Optional
from urllib.parse import urlparse

import httpx

from ..config import NovaSettings


def _host_from_url(url: str) -> str:
    p = urlparse(url)
    if not p.scheme or not p.netloc:
        raise ValueError(f"URL must be absolute: {url}")
    # Strip port if present
    host = p.hostname or p.netloc
    return host


class AllowedHTTPClient:
    """httpx client wrapper enforcing an allow-list of domains with retries."""

    def __init__(
        self,
        settings: NovaSettings,
        timeout: Optional[float] = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.settings = settings
        self._timeout = timeout
        self._session = httpx.Client(timeout=timeout)
        # Build effective allow-list; include OpenSWE base host if configured
        allowed = set(settings.allowed_domains)
        if settings.openswe_base_url:
            try:
                allowed.add(_host_from_url(settings.openswe_base_url))
            except Exception:
                pass
        self._allowed_hosts = allowed
        self._default_headers = headers or {}

    def _ensure_allowed(self, url: str) -> None:
        host = _host_from_url(url)
        if host not in self._allowed_hosts:
            raise PermissionError(f"Outbound HTTP to host '{host}' is not allowed")

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        retries: int = 3,
        backoff_base: float = 0.5,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        self._ensure_allowed(url)
        hdrs = dict(self._default_headers)
        if headers:
            hdrs.update(headers)

        last_exc: Optional[Exception] = None
        for attempt in range(retries + 1):
            try:
                resp = self._session.request(
                    method,
                    url,
                    headers=hdrs,
                    params=params,
                    json=json,
                    data=data,
                    timeout=timeout or self._timeout,
                )
                if resp.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                    delay = backoff_base * (2 ** attempt)
                    time.sleep(delay)
                    continue
                return resp
            except (httpx.TransportError, httpx.TimeoutException) as e:
                last_exc = e
                if attempt >= retries:
                    raise
                delay = backoff_base * (2 ** attempt)
                time.sleep(delay)
        # Should not reach here; raise last exception if present
        if last_exc:
            raise last_exc
        raise RuntimeError("HTTP request failed without exception")

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", url, **kwargs)

    def close(self) -> None:
        try:
            self._session.close()
        except Exception:
            pass

    def __enter__(self) -> "AllowedHTTPClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()


__all__ = ["AllowedHTTPClient"]
