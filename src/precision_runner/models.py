from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
from urllib.parse import urlparse

KST = timezone(timedelta(hours=9))


class RunMode(str, Enum):
    TEST = "TEST"
    LIVE = "LIVE"


class RunnerState(str, Enum):
    DRAFT = "DRAFT"
    # Transitional alias for the Architecture Spike. Enum iteration excludes aliases,
    # so the approved domain vocabulary remains DRAFT/TESTED/... while old runtime
    # references to RunnerState.READY keep working until the orchestrator slice.
    READY = "DRAFT"
    TESTED = "TESTED"
    ARMED = "ARMED"
    PREWARMING = "PREWARMING"
    RUNNING = "RUNNING"
    WAITING_MANUAL = "WAITING_MANUAL"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RunStage(str, Enum):
    PRECHECK = "PRECHECK"
    PREWARM = "PREWARM"
    DISPATCH = "DISPATCH"
    PARSE = "PARSE"
    NAVIGATE = "NAVIGATE"
    CONSENT = "CONSENT"
    HANDOFF = "HANDOFF"


class SideEffectStatus(str, Enum):
    NONE = "NONE"
    CONFIRMED = "CONFIRMED"
    AMBIGUOUS = "AMBIGUOUS"


class ErrorCode(str, Enum):
    CONFIG_INVALID = "CONFIG_INVALID"
    SESSION_INVALID = "SESSION_INVALID"
    PREFLIGHT_TRANSIENT = "PREFLIGHT_TRANSIENT"
    SERVER_REJECTION = "SERVER_REJECTION"
    RATE_LIMITED = "RATE_LIMITED"
    CONTRACT_MISMATCH = "CONTRACT_MISMATCH"
    TRANSPORT_AMBIGUOUS = "TRANSPORT_AMBIGUOUS"
    NAVIGATION_AFTER_SIDE_EFFECT = "NAVIGATION_AFTER_SIDE_EFFECT"
    LOCATOR_MISMATCH = "LOCATOR_MISMATCH"
    CLOCK_DISCONTINUITY = "CLOCK_DISCONTINUITY"
    DUPLICATE_ATTEMPT = "DUPLICATE_ATTEMPT"
    LOCAL_STORAGE_FAILURE = "LOCAL_STORAGE_FAILURE"
    BROWSER_DISCONNECTED = "BROWSER_DISCONNECTED"
    LATE_TARGET = "LATE_TARGET"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def _freeze(value: Any) -> Any:
    """Recursively freeze JSON-like values for immutable run snapshots/events."""
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, set):
        return frozenset(_freeze(v) for v in value)
    return copy.deepcopy(value)


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_thaw(v) for v in value]
    if isinstance(value, frozenset):
        return [_thaw(v) for v in value]
    return copy.deepcopy(value)


def _parse_aware_iso8601(text: str) -> datetime:
    raw = text.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError("target_time must be ISO-8601") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("target_time must be timezone-aware ISO-8601")
    return dt


@dataclass(frozen=True, slots=True)
class ManualBoundaryPolicy:
    auto_consent: bool = False
    open_payment_ui: bool = False
    final_authorization_manual: bool = True

    def __post_init__(self) -> None:
        if not self.final_authorization_manual:
            raise ValueError("final payment authorization must remain manual")
        if self.open_payment_ui and not self.auto_consent:
            raise ValueError("open_payment_ui requires auto_consent")

    def to_dict(self) -> dict[str, Any]:
        return {
            "auto_consent": self.auto_consent,
            "open_payment_ui": self.open_payment_ui,
            "final_authorization_manual": self.final_authorization_manual,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "ManualBoundaryPolicy":
        values = dict(data or {})
        return cls(
            auto_consent=bool(values.get("auto_consent", False)),
            open_payment_ui=bool(values.get("open_payment_ui", False)),
            final_authorization_manual=bool(values.get("final_authorization_manual", True)),
        )


@dataclass(slots=True)
class TaskDefinition:
    """Editable generic task definition.

    Site-specific product/request values belong only in adapter_variables. The task is
    intentionally mutable while DRAFT/TESTED; ARM creates an immutable snapshot.
    """

    name: str
    target_url: str
    target_time: str
    adapter_id: str
    adapter_version: str
    mode: RunMode = RunMode.TEST
    adapter_variables: dict[str, Any] = field(default_factory=dict)
    prewarm_lead_ms: int = 30_000
    max_lateness_ms: int = 2_000
    manual_boundary: ManualBoundaryPolicy = field(default_factory=ManualBoundaryPolicy)

    def __post_init__(self) -> None:
        if isinstance(self.mode, str):
            self.mode = RunMode(self.mode)
        if isinstance(self.manual_boundary, Mapping):
            self.manual_boundary = ManualBoundaryPolicy.from_dict(self.manual_boundary)
        self.adapter_variables = copy.deepcopy(dict(self.adapter_variables))

    def target_datetime(self) -> datetime:
        return _parse_aware_iso8601(self.target_time)

    def validate(self) -> list[str]:
        errors: list[str] = []
        parsed = urlparse(self.target_url)
        if parsed.scheme != "https" or not parsed.netloc:
            errors.append("target_url must be an https URL")
        if not self.name.strip():
            errors.append("name is required")
        if not self.adapter_id.strip():
            errors.append("adapter_id is required")
        if not self.adapter_version.strip():
            errors.append("adapter_version is required")
        if self.prewarm_lead_ms < 0:
            errors.append("prewarm_lead_ms must be non-negative")
        if self.max_lateness_ms < 0:
            errors.append("max_lateness_ms must be non-negative")
        try:
            self.target_datetime()
        except ValueError as exc:
            errors.append(str(exc))
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "target_url": self.target_url,
            "target_time": self.target_time,
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "mode": self.mode.value,
            "adapter_variables": copy.deepcopy(self.adapter_variables),
            "prewarm_lead_ms": self.prewarm_lead_ms,
            "max_lateness_ms": self.max_lateness_ms,
            "manual_boundary": self.manual_boundary.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TaskDefinition":
        values = dict(data)
        return cls(
            name=str(values.get("name", "")),
            target_url=str(values.get("target_url", "")),
            target_time=str(values.get("target_time", "")),
            adapter_id=str(values.get("adapter_id", "")),
            adapter_version=str(values.get("adapter_version", "")),
            mode=RunMode(values.get("mode", RunMode.TEST.value)),
            adapter_variables=copy.deepcopy(dict(values.get("adapter_variables", {}))),
            prewarm_lead_ms=int(values.get("prewarm_lead_ms", 30_000)),
            max_lateness_ms=int(values.get("max_lateness_ms", 2_000)),
            manual_boundary=ManualBoundaryPolicy.from_dict(values.get("manual_boundary")),
        )


@dataclass(frozen=True, slots=True)
class ArmedRunSnapshot:
    run_id: str
    mode: RunMode
    task_name: str
    target_url: str
    target_at: datetime
    adapter_id: str
    adapter_version: str
    adapter_variables: Mapping[str, Any]
    prewarm_lead_ms: int
    max_lateness_ms: int
    manual_boundary: ManualBoundaryPolicy
    armed_at: datetime
    contract_version: str = "1"

    def __post_init__(self) -> None:
        if not self.run_id.strip():
            raise ValueError("run_id is required")
        if self.target_at.tzinfo is None or self.target_at.utcoffset() is None:
            raise ValueError("target_at must be timezone-aware")
        if self.armed_at.tzinfo is None or self.armed_at.utcoffset() is None:
            raise ValueError("armed_at must be timezone-aware")
        if self.prewarm_lead_ms < 0:
            raise ValueError("prewarm_lead_ms must be non-negative")
        if self.max_lateness_ms < 0:
            raise ValueError("max_lateness_ms must be non-negative")
        object.__setattr__(self, "adapter_variables", _freeze(self.adapter_variables))

    @classmethod
    def from_task(
        cls,
        task: TaskDefinition,
        *,
        run_id: str,
        armed_at: datetime,
    ) -> "ArmedRunSnapshot":
        errors = task.validate()
        if errors:
            raise ValueError("; ".join(errors))
        return cls(
            run_id=run_id,
            mode=task.mode,
            task_name=task.name,
            target_url=task.target_url,
            target_at=task.target_datetime(),
            adapter_id=task.adapter_id,
            adapter_version=task.adapter_version,
            adapter_variables=task.adapter_variables,
            prewarm_lead_ms=task.prewarm_lead_ms,
            max_lateness_ms=task.max_lateness_ms,
            manual_boundary=task.manual_boundary,
            armed_at=armed_at,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "mode": self.mode.value,
            "task_name": self.task_name,
            "target_url": self.target_url,
            "target_at": self.target_at.isoformat(),
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "adapter_variables": _thaw(self.adapter_variables),
            "prewarm_lead_ms": self.prewarm_lead_ms,
            "max_lateness_ms": self.max_lateness_ms,
            "manual_boundary": self.manual_boundary.to_dict(),
            "armed_at": self.armed_at.isoformat(),
            "contract_version": self.contract_version,
        }


@dataclass(frozen=True, slots=True)
class ErrorInfo:
    code: ErrorCode
    stage: RunStage
    message: str
    side_effect: SideEffectStatus
    next_action: str
    run_id: str
    at: datetime
    http_status: int | None = None

    def __post_init__(self) -> None:
        if self.at.tzinfo is None or self.at.utcoffset() is None:
            raise ValueError("error timestamp must be timezone-aware")

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code.value,
            "stage": self.stage.value,
            "message": self.message,
            "side_effect": self.side_effect.value,
            "next_action": self.next_action,
            "http_status": self.http_status,
            "run_id": self.run_id,
            "at": self.at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class RunEvent:
    event_id: str
    run_id: str
    sequence: int
    at: datetime
    state: RunnerState
    stage: RunStage
    level: str
    code: str
    message: str
    side_effect: SideEffectStatus
    safe_detail: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.at.tzinfo is None or self.at.utcoffset() is None:
            raise ValueError("event timestamp must be timezone-aware")
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")
        object.__setattr__(self, "safe_detail", _freeze(self.safe_detail))

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "at": self.at.isoformat(),
            "state": self.state.value,
            "stage": self.stage.value,
            "level": self.level,
            "code": self.code,
            "message": self.message,
            "side_effect": self.side_effect.value,
            "safe_detail": _thaw(self.safe_detail),
        }


# ---------------------------------------------------------------------------
# Architecture Spike compatibility layer
# ---------------------------------------------------------------------------
# These two types keep the already-merged prototype import surface alive while
# R1 introduces the approved generic domain. They are not the new source of
# truth and are scheduled for migration/removal in later R4/R6/R7 slices.


@dataclass(slots=True)
class TaskConfig:
    name: str = "T1 Signature Edition"
    target_url: str = "https://t1.fan/shop/products/525"
    target_time: str = "2026-08-17T12:00:00+09:00"
    inventory_item_id: int = 3454
    quantity: int = 1
    amount: int = 500000
    currency_code: str = "KRW"
    shipping_type: str = "STANDARD_DELIVERY"
    shipping_type_verified: bool = False
    auto_consent: bool = False
    auto_open_payment: bool = False
    max_retries: int = 0
    retry_delay_ms: int = 250

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskConfig":
        aliases = {
            "targetUrl": "target_url",
            "targetTime": "target_time",
            "inventoryItemId": "inventory_item_id",
            "currencyCode": "currency_code",
            "shippingType": "shipping_type",
            "shippingTypeVerified": "shipping_type_verified",
            "autoConsent": "auto_consent",
            "autoOpenPayment": "auto_open_payment",
            "maxRetries": "max_retries",
            "retryDelayMs": "retry_delay_ms",
        }
        normalized = {aliases.get(k, k): v for k, v in data.items()}
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in normalized.items() if k in known})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def target_datetime(self) -> datetime:
        text = self.target_time.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=KST)
        return dt

    def validate(self, *, require_shipping_confirmation: bool = False) -> list[str]:
        errors: list[str] = []
        parsed = urlparse(self.target_url)
        if parsed.scheme != "https" or not parsed.netloc:
            errors.append("target_url must be an https URL")
        if self.inventory_item_id <= 0:
            errors.append("inventory_item_id must be positive")
        if self.quantity <= 0:
            errors.append("quantity must be positive")
        if self.amount <= 0:
            errors.append("amount must be positive")
        if not self.currency_code:
            errors.append("currency_code is required")
        if not self.shipping_type:
            errors.append("shipping_type is required")
        if self.max_retries < 0 or self.max_retries > 3:
            errors.append("max_retries must be between 0 and 3")
        if self.retry_delay_ms < 0 or self.retry_delay_ms > 5000:
            errors.append("retry_delay_ms must be between 0 and 5000")
        try:
            self.target_datetime()
        except ValueError:
            errors.append("target_time must be ISO-8601")
        if self.auto_open_payment and not self.auto_consent:
            errors.append("auto_open_payment requires auto_consent")
        if require_shipping_confirmation and not self.shipping_type_verified:
            errors.append("shipping_type_verified must be confirmed before live checkout")
        return errors


@dataclass(slots=True)
class Event:
    at: str
    level: str
    message: str
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
