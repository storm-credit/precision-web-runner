from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from .models import (
    ArmedRunSnapshot,
    ManualBoundaryPolicy,
    RunMode,
    RunnerState,
    RunStage,
    SideEffectStatus,
    TaskDefinition,
)

SCHEMA_VERSION = 1
_TERMINAL_STATES = {RunnerState.SUCCEEDED, RunnerState.FAILED, RunnerState.CANCELLED}


class StoreError(RuntimeError):
    pass


class StoreCorrupt(StoreError):
    pass


def _parse_datetime(value: Any, *, field_name: str) -> datetime:
    try:
        dt = datetime.fromisoformat(str(value))
    except (TypeError, ValueError) as exc:
        raise StoreCorrupt(f"invalid {field_name}") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise StoreCorrupt(f"{field_name} must be timezone-aware")
    return dt


@dataclass(frozen=True, slots=True)
class ActiveRunRecord:
    snapshot: ArmedRunSnapshot
    state: RunnerState
    stage: RunStage
    side_effect: SideEffectStatus
    updated_at: datetime
    error_code: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "snapshot": self.snapshot.to_dict(),
            "state": self.state.value,
            "stage": self.stage.value,
            "side_effect": self.side_effect.value,
            "updated_at": self.updated_at.isoformat(),
            "error_code": self.error_code,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "ActiveRunRecord":
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise StoreCorrupt("unsupported active-run schema_version")
        raw_snapshot = payload.get("snapshot")
        if not isinstance(raw_snapshot, Mapping):
            raise StoreCorrupt("active-run snapshot is missing")
        try:
            snapshot = ArmedRunSnapshot(
                run_id=str(raw_snapshot["run_id"]),
                mode=RunMode(raw_snapshot["mode"]),
                task_name=str(raw_snapshot["task_name"]),
                target_url=str(raw_snapshot["target_url"]),
                target_at=_parse_datetime(raw_snapshot["target_at"], field_name="target_at"),
                adapter_id=str(raw_snapshot["adapter_id"]),
                adapter_version=str(raw_snapshot["adapter_version"]),
                adapter_variables=dict(raw_snapshot.get("adapter_variables", {})),
                prewarm_lead_ms=int(raw_snapshot["prewarm_lead_ms"]),
                max_lateness_ms=int(raw_snapshot["max_lateness_ms"]),
                manual_boundary=ManualBoundaryPolicy.from_dict(raw_snapshot.get("manual_boundary")),
                armed_at=_parse_datetime(raw_snapshot["armed_at"], field_name="armed_at"),
                contract_version=str(raw_snapshot.get("contract_version", "1")),
            )
            return cls(
                snapshot=snapshot,
                state=RunnerState(payload["state"]),
                stage=RunStage(payload["stage"]),
                side_effect=SideEffectStatus(payload.get("side_effect", SideEffectStatus.NONE.value)),
                updated_at=_parse_datetime(payload["updated_at"], field_name="updated_at"),
                error_code=(str(payload["error_code"]) if payload.get("error_code") is not None else None),
            )
        except (KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, StoreCorrupt):
                raise
            raise StoreCorrupt("invalid active-run record") from exc


class LocalStore:
    """Versioned local persistence for editable tasks and immutable armed runs.

    The active-run file is the safety boundary. It is written atomically before
    scheduler activation and is intentionally left in place for recovery review
    when an in-flight/ambiguous run cannot be proven safe to resume.
    """

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.task_path = self.root / "task-definition.json"
        self.active_run_path = self.root / "active-run.json"
        self.history_path = self.root / "run-history.jsonl"

    def save_task(self, task: TaskDefinition) -> None:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "task": task.to_dict(),
        }
        self._write_json(self.task_path, payload, label="task definition")

    def load_task(self) -> TaskDefinition | None:
        payload = self._read_json(self.task_path, label="task definition")
        if payload is None:
            return None
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise StoreCorrupt("unsupported task schema_version")
        raw_task = payload.get("task")
        if not isinstance(raw_task, Mapping):
            raise StoreCorrupt("task definition is missing")
        try:
            return TaskDefinition.from_dict(raw_task)
        except (TypeError, ValueError) as exc:
            raise StoreCorrupt("invalid task definition") from exc

    def create_active_run(
        self,
        snapshot: ArmedRunSnapshot,
        *,
        state: RunnerState = RunnerState.ARMED,
        stage: RunStage = RunStage.PRECHECK,
        side_effect: SideEffectStatus = SideEffectStatus.NONE,
    ) -> ActiveRunRecord:
        if self.active_run_path.exists():
            raise StoreError("active run already exists; recovery/inspection is required")
        record = ActiveRunRecord(
            snapshot=snapshot,
            state=state,
            stage=stage,
            side_effect=side_effect,
            updated_at=datetime.now(snapshot.armed_at.tzinfo),
        )
        self._write_json(self.active_run_path, record.to_payload(), label="active run")
        return record

    def load_active_run(self) -> ActiveRunRecord | None:
        payload = self._read_json(self.active_run_path, label="active run")
        if payload is None:
            return None
        return ActiveRunRecord.from_payload(payload)

    def update_active_run(
        self,
        run_id: str,
        *,
        state: RunnerState,
        stage: RunStage,
        side_effect: SideEffectStatus = SideEffectStatus.NONE,
        error_code: str | None = None,
    ) -> ActiveRunRecord:
        current = self.load_active_run()
        if current is None:
            raise StoreError("no active run to update")
        if current.snapshot.run_id != run_id:
            raise StoreError("active run id mismatch")
        record = ActiveRunRecord(
            snapshot=current.snapshot,
            state=state,
            stage=stage,
            side_effect=side_effect,
            updated_at=datetime.now(current.snapshot.armed_at.tzinfo),
            error_code=error_code,
        )
        self._write_json(self.active_run_path, record.to_payload(), label="active run")
        return record

    def complete_active_run(
        self,
        run_id: str,
        *,
        state: RunnerState,
        stage: RunStage,
        side_effect: SideEffectStatus,
        error_code: str | None = None,
    ) -> ActiveRunRecord:
        if state not in _TERMINAL_STATES:
            raise StoreError("complete_active_run requires a terminal state")
        current = self.load_active_run()
        if current is None:
            raise StoreError("no active run to complete")
        if current.snapshot.run_id != run_id:
            raise StoreError("active run id mismatch")
        record = ActiveRunRecord(
            snapshot=current.snapshot,
            state=state,
            stage=stage,
            side_effect=side_effect,
            updated_at=datetime.now(current.snapshot.armed_at.tzinfo),
            error_code=error_code,
        )
        self._append_history(record)
        try:
            self.active_run_path.unlink()
        except OSError as exc:
            raise StoreError("failed to clear completed active run") from exc
        return record

    def list_history(self) -> list[ActiveRunRecord]:
        if not self.history_path.exists():
            return []
        records: list[ActiveRunRecord] = []
        try:
            lines = self.history_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise StoreError("failed to read run history") from exc
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise StoreCorrupt(f"invalid run history at line {line_number}") from exc
            if not isinstance(payload, Mapping):
                raise StoreCorrupt(f"invalid run history at line {line_number}")
            records.append(ActiveRunRecord.from_payload(payload))
        return records

    def _read_json(self, path: Path, *, label: str) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise StoreError(f"failed to read {label}") from exc
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise StoreCorrupt(f"corrupt {label} store") from exc
        if not isinstance(payload, dict):
            raise StoreCorrupt(f"invalid {label} store")
        return payload

    def _write_json(self, path: Path, payload: Mapping[str, Any], *, label: str) -> None:
        try:
            self._atomic_write_json(path, payload)
        except OSError as exc:
            raise StoreError(f"failed to persist {label}") from exc

    def _atomic_write_json(self, path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
        temp_path = Path(temp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        except Exception:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise

    def _append_history(self, record: ActiveRunRecord) -> None:
        try:
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            with self.history_path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(record.to_payload(), ensure_ascii=False) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            raise StoreError("failed to persist run history") from exc
