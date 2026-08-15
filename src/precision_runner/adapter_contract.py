from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .models import SideEffectStatus


class EvidenceStatus(str, Enum):
    VERIFIED = "VERIFIED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"


class StepEffect(str, Enum):
    NONE = "NONE"
    IRREVERSIBLE = "IRREVERSIBLE"


class AdapterParseStatus(str, Enum):
    PASS = "PASS"
    REJECTED = "REJECTED"
    CONTRACT_MISMATCH = "CONTRACT_MISMATCH"
    AMBIGUOUS = "AMBIGUOUS"


class LocatorKind(str, Enum):
    ROLE_NAME = "ROLE_NAME"
    TEXT = "TEXT"
    DATA_ATTRIBUTE = "DATA_ATTRIBUTE"
    STRUCTURAL = "STRUCTURAL"


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return copy.deepcopy(value)


@dataclass(frozen=True, slots=True)
class AdapterVariableSpec:
    key: str
    type_name: str
    required: bool = True
    live_requires_verified: bool = False
    sensitive: bool = False
    help_text: str = ""


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    message: str
    live_blocker: bool = False


@dataclass(frozen=True, slots=True)
class ValidationResult:
    issues: tuple[ValidationIssue, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.issues

    @property
    def live_blockers(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.live_blocker)


@dataclass(frozen=True, slots=True)
class RequestSpec:
    origin: str
    method: str
    path: str
    effect: StepEffect
    headers: Mapping[str, str] = field(default_factory=dict)
    body: Mapping[str, Any] | None = None
    credential_mode: str = "same-origin"

    def __post_init__(self) -> None:
        object.__setattr__(self, "headers", _freeze(self.headers))
        if self.body is not None:
            object.__setattr__(self, "body", _freeze(self.body))


@dataclass(frozen=True, slots=True)
class NavigationSpec:
    origin: str
    path_template: str
    required_variable: str
    effect: StepEffect = StepEffect.NONE


@dataclass(frozen=True, slots=True)
class AdapterStep:
    step_id: str
    effect: StepEffect
    request: RequestSpec | None = None
    navigation: NavigationSpec | None = None

    def __post_init__(self) -> None:
        if (self.request is None) == (self.navigation is None):
            raise ValueError("adapter step must define exactly one request or navigation")
        if self.request is not None and self.request.effect is not self.effect:
            raise ValueError("request effect must match adapter step effect")
        if self.navigation is not None and self.navigation.effect is not self.effect:
            raise ValueError("navigation effect must match adapter step effect")


@dataclass(frozen=True, slots=True)
class AdapterPlan:
    steps: tuple[AdapterStep, ...]

    def __post_init__(self) -> None:
        if not self.steps:
            raise ValueError("adapter plan requires at least one step")
        ids = [step.step_id for step in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("adapter step ids must be unique")


@dataclass(frozen=True, slots=True)
class AdapterStepResult:
    status: AdapterParseStatus
    safe_data: Mapping[str, Any] = field(default_factory=dict)
    next_variables: Mapping[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    side_effect_status: SideEffectStatus = SideEffectStatus.NONE

    def __post_init__(self) -> None:
        object.__setattr__(self, "safe_data", _freeze(self.safe_data))
        object.__setattr__(self, "next_variables", _freeze(self.next_variables))


@dataclass(frozen=True, slots=True)
class LocatorStrategy:
    kind: LocatorKind
    value: str
    role: str | None = None


@dataclass(frozen=True, slots=True)
class LocatorSet:
    consent: tuple[LocatorStrategy, ...]
    payment: tuple[LocatorStrategy, ...]


@dataclass(frozen=True, slots=True)
class ManualCheckpointSpec:
    final_authorization_manual: bool = True
    allows_open_payment_ui: bool = True
    allows_card_entry: bool = False
    allows_otp_or_3ds: bool = False

    def __post_init__(self) -> None:
        if not self.final_authorization_manual:
            raise ValueError("final authorization must remain manual")
        if self.allows_card_entry or self.allows_otp_or_3ds:
            raise ValueError("payment credentials/OTP/3DS are outside adapter capabilities")
