from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from .models import TaskConfig


class AdapterError(RuntimeError):
    pass


@dataclass(slots=True)
class CheckoutResult:
    status: int
    checkout_number: str | None
    retryable: bool
    message: str


class T1Adapter:
    name = "t1"
    checkout_path = "/svc/shop/api/v1/order/checkout"
    preflight_path = "/svc/shop/api/v1/carts/summary"
    agreement_text = "주문 내용과 약관에 동의합니다"

    def validate_target(self, task: TaskConfig) -> list[str]:
        errors = task.validate(require_shipping_confirmation=True)
        host = urlparse(task.target_url).hostname or ""
        if host.lower() != "t1.fan":
            errors.append("T1 adapter requires target host t1.fan")
        return errors

    @staticmethod
    def checkout_payload(task: TaskConfig) -> dict[str, Any]:
        return {
            "inventoryItemAndQuantities": [
                {
                    "inventoryItemId": task.inventory_item_id,
                    "quantity": task.quantity,
                    "unitPrice": {
                        "currencyCode": task.currency_code,
                        "amount": task.amount,
                    },
                    "shippingType": task.shipping_type,
                }
            ]
        }

    @staticmethod
    def request_headers() -> dict[str, str]:
        return {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "x-bmf-country": "KR",
            "x-bmf-currency": "KRW",
            "x-bmf-language": "ko",
            "x-bmf-shop-id": "1",
            "x-bmf-sid": "t1",
        }

    @staticmethod
    def parse_checkout(status: int, text: str) -> CheckoutResult:
        retryable = status >= 500 or status in (408, 429)
        if not 200 <= status < 300:
            return CheckoutResult(
                status=status,
                checkout_number=None,
                retryable=retryable,
                message=f"T1 checkout rejected with HTTP {status}",
            )
        try:
            body = json.loads(text)
        except json.JSONDecodeError as exc:
            raise AdapterError("checkout response was not valid JSON") from exc
        number = body.get("checkoutNumber")
        if number is None:
            raise AdapterError("checkout response did not contain checkoutNumber")
        return CheckoutResult(
            status=status,
            checkout_number=str(number),
            retryable=False,
            message="checkout created",
        )

    @staticmethod
    def checkout_url(checkout_number: str) -> str:
        return f"https://t1.fan/shop/checkout/{checkout_number}"
