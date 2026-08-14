from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from urllib.parse import urlparse

KST = timezone(timedelta(hours=9))


class RunnerState(str, Enum):
    READY = "READY"
    ARMED = "ARMED"
    PREWARMING = "PREWARMING"
    RUNNING = "RUNNING"
    WAITING_MANUAL = "WAITING_MANUAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


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
    max_retries: int = 1
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
