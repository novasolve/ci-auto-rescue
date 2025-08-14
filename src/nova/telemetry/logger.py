from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from ..config import NovaSettings


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_within(base: Path, target: Path) -> bool:
    try:
        base_resolved = base.resolve()
        target_resolved = target.resolve()
        return str(target_resolved).startswith(str(base_resolved))
    except FileNotFoundError:
        return str(target.absolute()).startswith(str(base.absolute()))


def redact_secrets(payload: Any, secrets: Iterable[Optional[str]]) -> Any:
    secrets_list = [s for s in secrets if s]
    if not secrets_list:
        return payload

    def _redact(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: _redact(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_redact(v) for v in value]
        if isinstance(value, str):
            redacted = value
            for s in secrets_list:
                if s and s in redacted:
                    redacted = redacted.replace(s, "[REDACTED]")
            return redacted
        return value

    return _redact(payload)


class JSONLLogger:
    def __init__(self, settings: NovaSettings, enabled: bool = True) -> None:
        self.settings = settings
        self.enabled = enabled
        self._run_id: Optional[str] = None
        self._run_dir: Optional[Path] = None
        self._trace_file: Optional[Path] = None
        self._lock = threading.Lock()
        self._secrets = [
            settings.openai_api_key,
            settings.anthropic_api_key,
            settings.openswe_api_key,
        ]

    @property
    def run_id(self) -> Optional[str]:
        return self._run_id

    @property
    def run_dir(self) -> Optional[Path]:
        return self._run_dir

    def start_run(self, repo_path: Path | str) -> str:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-{uuid.uuid4().hex[:8]}"
        base_dir = Path(self.settings.telemetry_dir)
        run_dir = base_dir / run_id
        trace_file = run_dir / "trace.jsonl"

        self._run_id = run_id
        self._run_dir = run_dir
        self._trace_file = trace_file

        if self.enabled:
            run_dir.mkdir(parents=True, exist_ok=True)
            self._append_record({
                "ts": _utc_now_iso(),
                "event": "start",
                "repo_path": str(repo_path),
                "run_id": run_id,
                "telemetry_dir": str(run_dir),
                "pid": os.getpid(),
            })
        return run_id

    def log_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        if not self.enabled or not self._trace_file:
            return
        safe_payload = redact_secrets(payload, self._secrets)
        self._append_record({
            "ts": _utc_now_iso(),
            "event": event_type,
            "data": safe_payload,
        })

    def save_artifact(self, name: str, data: bytes | str) -> Optional[Path]:
        if not self.enabled or not self._run_dir:
            return None
        dest = self._run_dir / name
        if not _safe_within(self._run_dir, dest):
            raise ValueError("Artifact path escapes run directory")
        dest.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, bytes):
            dest.write_bytes(data)
        else:
            dest.write_text(data)
        self._append_record({
            "ts": _utc_now_iso(),
            "event": "artifact",
            "name": name,
            "path": str(dest),
            "size": dest.stat().st_size,
        })
        return dest
    
    def save_patch(self, step_number: int, patch_content: str) -> Optional[Path]:
        """Save a patch diff as step-N.patch artifact."""
        filename = f"patches/step-{step_number}.patch"
        return self.save_artifact(filename, patch_content)
    
    def save_test_report(self, step_number: int, report_content: str, report_type: str = "junit") -> Optional[Path]:
        """Save a test report as step-N.xml artifact."""
        ext = "xml" if report_type == "junit" else "json"
        filename = f"reports/step-{step_number}.{ext}"
        return self.save_artifact(filename, report_content)

    def end_run(self, success: bool, summary: Dict[str, Any] | None = None) -> None:
        if not self.enabled or not self._trace_file:
            return
        self._append_record({
            "ts": _utc_now_iso(),
            "event": "end",
            "success": bool(success),
            "summary": redact_secrets(summary or {}, self._secrets),
        })

    def _append_record(self, record: Dict[str, Any]) -> None:
        if not self._trace_file:
            return
        line = json.dumps(record, ensure_ascii=False)
        with self._lock:
            self._trace_file.parent.mkdir(parents=True, exist_ok=True)
            with self._trace_file.open("a", encoding="utf-8") as f:
                f.write(line + "\n")


__all__ = ["JSONLLogger", "redact_secrets"]
