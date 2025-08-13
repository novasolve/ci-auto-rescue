from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..settings import get_settings


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _short_id(ts: str) -> str:
    # Simple short id based on timestamp for local uniqueness
    return ts.replace(":", "").replace("-", "").replace("T", "").replace("Z", "")[-8:]


class TelemetryRun:
    """Local telemetry and artifact management.

    Writes to .nova/runs/{timestamp_shortid}/ with subdirs for artifacts.
    """

    def __init__(self, run_id: Optional[str] = None, enabled: Optional[bool] = None) -> None:
        self.settings = get_settings()
        self.enabled = self.settings.TELEMETRY_ENABLED if enabled is None else enabled
        ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        short = _short_id(ts)
        self.run_id = run_id or f"{ts}_{short}"
        self.root_dir = Path(self.settings.ARTIFACTS_ROOT) / "runs" / self.run_id
        self.trace_path = self.root_dir / "trace.jsonl"
        self.meta_path = self.root_dir / "metadata.json"
        self.diffs_dir = self.root_dir / "diffs"
        self.test_reports_dir = self.root_dir / "test_reports"
        self.prompts_dir = self.root_dir / "prompts"
        self._started = False

    def start_run(self, meta: Dict[str, Any]) -> None:
        if not self.enabled:
            return
        for d in [self.root_dir, self.diffs_dir, self.test_reports_dir, self.prompts_dir]:
            d.mkdir(parents=True, exist_ok=True)
        meta_sanitized = self._redact(meta)
        start = {"event": "run_started", "ts": _now(), "meta": meta_sanitized}
        self.meta_path.write_text(json.dumps(start, indent=2))
        # Ensure trace file exists
        self.trace_path.touch(exist_ok=True)
        self._started = True

    def log_event(self, event: Dict[str, Any]) -> None:
        if not self.enabled:
            return
        payload = {"ts": _now(), **self._redact(event)}
        with self.trace_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def save_artifact(self, rel_path: Union[str, Path], data: Union[str, bytes]) -> Path:
        path = self.root_dir / Path(rel_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, bytes):
            path.write_bytes(data)
        else:
            path.write_text(data)
        return path

    def end_run(self, success: bool, summary: Dict[str, Any]) -> None:
        if not self.enabled:
            return
        end = {
            "event": "run_finished",
            "ts": _now(),
            "success": success,
            "summary": self._redact(summary),
        }
        if self.meta_path.exists():
            try:
                meta = json.loads(self.meta_path.read_text())
            except Exception:
                meta = {}
        else:
            meta = {}
        meta.update(end)
        self.meta_path.write_text(json.dumps(meta, indent=2))

    def _redact(self, obj: Any) -> Any:
        """Redact secrets and large blobs from event payloads."""
        try:
            if isinstance(obj, dict):
                redacted: Dict[str, Any] = {}
                for k, v in obj.items():
                    lk = k.lower()
                    if any(s in lk for s in ("api_key", "apikey", "token", "password", "secret")):
                        redacted[k] = "***REDACTED***"
                    elif lk in {"prompt", "code", "diff", "response"}:
                        redacted[k] = self._truncate(v)
                    else:
                        redacted[k] = self._redact(v)
                return redacted
            if isinstance(obj, list):
                return [self._redact(i) for i in obj]
            return obj
        except Exception:
            return "<redaction_error>"

    @staticmethod
    def _truncate(v: Any, max_len: int = 5000) -> Any:
        try:
            s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
            if len(s) > max_len:
                return s[: max_len - 20] + "...<truncated>"
            return s
        except Exception:
            return "<unserializable>"


__all__ = ["TelemetryRun"]
