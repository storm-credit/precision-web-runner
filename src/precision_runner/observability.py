from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .models import RunnerState, RunStage, SideEffectStatus


_ALLOWED_DETAIL_KEYS = {
    "targetAt",
    "armedAt",
    "prewarmScheduledAt",
    "prewarmStartedAt",
    "preflightCompletedAt",
    "schedulerWakeAt",
    "requestStartedAt",
    "responseReceivedAt",
    "checkoutParsedAt",
    "checkoutPageReadyAt",
    "manualCheckpointAt",
    "wakeLatenessMs",
    "schedulerLatenessMs",
    "dispatchLatenessMs",
    "responseLatencyMs",
    "navigationLatencyMs",
    "maxLatenessMs",
    "httpStatus",
    "responseBytes",
    "method",
    "endpoint",
    "adapterClassification",
    "adapterVersion",
    "mode",
    "checkoutNumber",
    "dynamicVariable",
    "target",
    "reason",
    "locatorKind",
    "alreadyChecked",
}

_DENIED_KEY_PARTS = {
    "cookie",
    "authorization",
    "csrf",
    "nonce",
    "token",
    "session",
    "email",
    "phone",
    "mobile",
    "address",
    "card",
    "otp",
    "password",
    "body",
    "html",
}

_EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?82[- ]?)?0?1[016789][- ]?\d{3,4}[- ]?\d{4}(?!\d)")
_SECRET_ASSIGN_RE = re.compile(
    r"(?i)\b(authorization|cookie|set-cookie|token|session(?:id)?|csrf|nonce|password|otp)\s*[:=]\s*[^\s,;]+(?:\s+[^\s,;]+)?"
)
_CARD_LIKE_RE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")


@dataclass(frozen=True, slots=True)
class RunEvent:
    event_id: str
    run_id: str
    sequence: int
    at: datetime
    state: RunnerState
    stage: RunStage
    step_id: str | None
    level: str
    code: str
    message: str
    side_effect: SideEffectStatus
    safe_detail: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValueError("event_id is required")
        if not self.run_id:
            raise ValueError("run_id is required")
        if self.sequence <= 0:
            raise ValueError("sequence must be positive")
        if self.at.tzinfo is None or self.at.utcoffset() is None:
            raise ValueError("event timestamp must be timezone-aware")
        object.__setattr__(self, "safe_detail", MappingProxyType(dict(self.safe_detail)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "at": self.at.isoformat(),
            "state": self.state.value,
            "stage": self.stage.value,
            "step_id": self.step_id,
            "level": self.level,
            "code": self.code,
            "message": self.message,
            "side_effect": self.side_effect.value,
            "safe_detail": dict(self.safe_detail),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RunEvent":
        at = datetime.fromisoformat(str(data["at"]))
        detail = data.get("safe_detail", {})
        if not isinstance(detail, Mapping):
            detail = {}
        return cls(
            event_id=str(data["event_id"]),
            run_id=str(data["run_id"]),
            sequence=int(data["sequence"]),
            at=at,
            state=RunnerState(data["state"]),
            stage=RunStage(data["stage"]),
            step_id=(str(data["step_id"]) if data.get("step_id") is not None else None),
            level=str(data["level"]),
            code=str(data["code"]),
            message=str(data["message"]),
            side_effect=SideEffectStatus(data["side_effect"]),
            safe_detail=dict(detail),
        )


class EventLogger:
    """Allow-list first local event persistence.

    Arbitrary detail dictionaries are accepted at the call boundary for ease of
    instrumentation, but only known safe keys survive. Secret/PII keys and raw
    request/response/body fields are discarded before a RunEvent is created and
    before any disk write. String values/messages receive a second pattern-based
    scrub as defense in depth.
    """

    def __init__(
        self,
        path: Path,
        *,
        max_records: int = 500,
        max_file_bytes: int = 512_000,
        max_detail_value_chars: int = 512,
        max_message_chars: int = 1_024,
    ):
        if max_records <= 0 or max_file_bytes <= 0 or max_detail_value_chars <= 0 or max_message_chars <= 0:
            raise ValueError("event logger limits must be positive")
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.max_records = max_records
        self.max_file_bytes = max_file_bytes
        self.max_detail_value_chars = max_detail_value_chars
        self.max_message_chars = max_message_chars
        self._lock = threading.RLock()
        self._sequences: dict[str, int] = {}
        self._bootstrap_sequences()

    def emit(
        self,
        *,
        run_id: str,
        state: RunnerState,
        stage: RunStage,
        level: str,
        code: str,
        message: str,
        side_effect: SideEffectStatus,
        safe_detail: Mapping[str, Any] | None = None,
        step_id: str | None = None,
        at: datetime | None = None,
    ) -> RunEvent:
        timestamp = at or datetime.now().astimezone()
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("event timestamp must be timezone-aware")
        clean_detail = self._sanitize_detail(safe_detail or {})
        clean_message = self._sanitize_string(str(message), self.max_message_chars)
        clean_code = re.sub(r"[^A-Z0-9_.-]", "_", str(code).upper())[:96] or "EVENT"
        clean_step = None if step_id is None else re.sub(r"[^A-Za-z0-9_.-]", "_", str(step_id))[:96]

        with self._lock:
            sequence = self._sequences.get(run_id, 0) + 1
            event = RunEvent(
                event_id=str(uuid.uuid4()),
                run_id=run_id,
                sequence=sequence,
                at=timestamp,
                state=state,
                stage=stage,
                step_id=clean_step,
                level=str(level)[:16],
                code=clean_code,
                message=clean_message,
                side_effect=side_effect,
                safe_detail=clean_detail,
            )
            self._append_and_bound(event)
            self._sequences[run_id] = sequence
            return event

    def read_recent(self, limit: int = 100) -> list[RunEvent]:
        if limit <= 0 or not self.path.exists():
            return []
        with self._lock:
            lines = self._read_valid_lines()
        events: list[RunEvent] = []
        for line in lines[-limit:]:
            try:
                payload = json.loads(line)
                events.append(RunEvent.from_dict(payload))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
        return events

    def _sanitize_detail(self, detail: Mapping[str, Any]) -> dict[str, Any]:
        clean: dict[str, Any] = {}
        for raw_key, value in detail.items():
            key = str(raw_key)
            lowered = key.lower().replace("_", "").replace("-", "")
            if any(part in lowered for part in _DENIED_KEY_PARTS):
                continue
            if key not in _ALLOWED_DETAIL_KEYS:
                continue
            safe = self._sanitize_value(key, value)
            if safe is not None:
                clean[key] = safe
        return clean

    def _sanitize_value(self, key: str, value: Any) -> Any:
        if value is None or isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value
        if key == "checkoutNumber":
            text = str(value).strip()
            if text.isdigit() and 1 <= len(text) <= 32:
                return text
            return None
        if isinstance(value, str):
            return self._sanitize_string(value, self.max_detail_value_chars)
        # Nested structures are intentionally rejected from persisted detail.
        # Flat allow-listed telemetry is easier to audit and safer to share.
        return None

    def _sanitize_string(self, value: str, limit: int) -> str:
        text = value
        text = _SECRET_ASSIGN_RE.sub("[REDACTED_SECRET]", text)
        text = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
        text = _PHONE_RE.sub("[REDACTED_PHONE]", text)
        text = _CARD_LIKE_RE.sub("[REDACTED_NUMBER]", text)
        if len(text) > limit:
            marker = "…[TRUNCATED]"
            text = text[: max(0, limit - len(marker))] + marker
        return text

    def _append_and_bound(self, event: RunEvent) -> None:
        payload = json.dumps(event.to_dict(), ensure_ascii=False, separators=(",", ":"))
        lines = self._read_valid_lines()
        lines.append(payload)
        if len(lines) > self.max_records:
            lines = lines[-self.max_records :]

        encoded = [line.encode("utf-8") + b"\n" for line in lines]
        total = sum(len(chunk) for chunk in encoded)
        while len(encoded) > 1 and total > self.max_file_bytes:
            total -= len(encoded[0])
            encoded.pop(0)
        # A single event should normally fit because fields are bounded. If a
        # future schema grows beyond the file limit, fail closed rather than
        # persisting an unbounded record.
        if encoded and len(encoded[-1]) > self.max_file_bytes:
            raise ValueError("single event exceeds max_file_bytes")
        self._atomic_write(b"".join(encoded))

    def _read_valid_lines(self) -> list[str]:
        if not self.path.exists():
            return []
        try:
            raw = self.path.read_text(encoding="utf-8")
        except OSError:
            return []
        lines: list[str] = []
        for line in raw.splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                if isinstance(payload, dict):
                    lines.append(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
            except json.JSONDecodeError:
                continue
        return lines

    def _atomic_write(self, data: bytes) -> None:
        fd, temp_name = tempfile.mkstemp(prefix=f".{self.path.name}.", suffix=".tmp", dir=str(self.path.parent))
        temp_path = Path(temp_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.path)
        except Exception:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise

    def _bootstrap_sequences(self) -> None:
        for event in self.read_recent(self.max_records):
            self._sequences[event.run_id] = max(self._sequences.get(event.run_id, 0), event.sequence)
