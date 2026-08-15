from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlparse

from .adapter_contract import (
    AdapterParseStatus,
    AdapterPlan,
    AdapterStep,
    AdapterStepResult,
    AdapterVariableSpec,
    EvidenceStatus,
    LocatorKind,
    LocatorSet,
    LocatorStrategy,
    ManualCheckpointSpec,
    NavigationSpec,
    RequestSpec,
    StepEffect,
    ValidationIssue,
    ValidationResult,
)
from .models import ArmedRunSnapshot, RunMode, SideEffectStatus, TaskConfig, TaskDefinition


class AdapterError(RuntimeError):
    pass


@dataclass(slots=True)
class CheckoutResult:
    """Architecture Spike compatibility result.

    New orchestration should use AdapterStepResult. This stays temporarily so
    pre-R4 BrowserWorker/RunnerService imports keep working until R5/R6.
    """

    status: int
    checkout_number: str | None
    retryable: bool
    message: str


class T1Adapter:
    id = "t1"
    name = id  # Architecture Spike compatibility alias.
    version = "1.0.0"
    supported_origins = ("https://t1.fan",)
    supported_url_prefixes = ("/shop/products/",)
    capabilities = (
        "same_origin_request",
        "semantic_locators",
        "dynamic_checkout_navigation",
        "manual_payment_handoff",
    )

    checkout_path = "/svc/shop/api/v1/order/checkout"
    preflight_path = "/svc/shop/api/v1/carts/summary"
    agreement_text = "주문 내용과 약관에 동의합니다"

    _OBSERVED_ITEM_PRICE_PAIRS = {
        (3454, 500000),  # Signature item observation (cart/product facts)
        (3229, 49000),   # normal direct-checkout observation
    }

    def variable_schema(self) -> tuple[AdapterVariableSpec, ...]:
        return (
            AdapterVariableSpec("inventoryItemId", "int", help_text="T1 inventory item identifier"),
            AdapterVariableSpec("quantity", "int", help_text="requested quantity"),
            AdapterVariableSpec("amount", "int", help_text="observed unit amount in KRW"),
            AdapterVariableSpec("currencyCode", "str", help_text="unit-price currency"),
            AdapterVariableSpec(
                "shippingType",
                "str",
                live_requires_verified=True,
                help_text="must be independently verified for the exact live product",
            ),
        )

    @staticmethod
    def _origin(url: str) -> str:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return ""
        return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"

    @staticmethod
    def _evidence_status(variables: Mapping[str, Any], key: str) -> EvidenceStatus:
        evidence = variables.get("evidence", {})
        if not isinstance(evidence, Mapping):
            return EvidenceStatus.UNKNOWN
        raw = evidence.get(key, EvidenceStatus.UNKNOWN.value)
        try:
            return EvidenceStatus(str(raw))
        except ValueError:
            return EvidenceStatus.UNKNOWN

    @staticmethod
    def _variables(source: TaskDefinition | ArmedRunSnapshot) -> Mapping[str, Any]:
        return source.adapter_variables

    def validate(self, source: TaskDefinition | ArmedRunSnapshot) -> ValidationResult:
        issues: list[ValidationIssue] = []
        origin = self._origin(source.target_url)
        parsed = urlparse(source.target_url)

        if origin not in self.supported_origins:
            issues.append(
                ValidationIssue(
                    code="UNSUPPORTED_ORIGIN",
                    message="T1 adapter requires exact origin https://t1.fan",
                    live_blocker=True,
                )
            )
        if not any(parsed.path.startswith(prefix) for prefix in self.supported_url_prefixes):
            issues.append(
                ValidationIssue(
                    code="UNSUPPORTED_TARGET_PATH",
                    message="T1 adapter requires a supported product URL",
                    live_blocker=True,
                )
            )
        if source.adapter_id != self.id:
            issues.append(
                ValidationIssue(
                    code="ADAPTER_ID_MISMATCH",
                    message=f"expected adapter_id={self.id}",
                    live_blocker=True,
                )
            )
        if source.adapter_version != self.version:
            issues.append(
                ValidationIssue(
                    code="ADAPTER_VERSION_MISMATCH",
                    message=f"expected adapter_version={self.version}",
                    live_blocker=True,
                )
            )

        variables = self._variables(source)
        for spec in self.variable_schema():
            value = variables.get(spec.key)
            if spec.required and (value is None or value == ""):
                issues.append(
                    ValidationIssue(
                        code=f"MISSING_{spec.key.upper()}",
                        message=f"{spec.key} is required",
                        live_blocker=True,
                    )
                )

        inventory = variables.get("inventoryItemId")
        quantity = variables.get("quantity")
        amount = variables.get("amount")
        currency = variables.get("currencyCode")
        shipping = variables.get("shippingType")
        if not isinstance(inventory, int) or isinstance(inventory, bool) or inventory <= 0:
            issues.append(ValidationIssue("INVALID_INVENTORY_ITEM_ID", "inventoryItemId must be positive int", True))
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
            issues.append(ValidationIssue("INVALID_QUANTITY", "quantity must be positive int", True))
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            issues.append(ValidationIssue("INVALID_AMOUNT", "amount must be positive int", True))
        if not isinstance(currency, str) or currency != "KRW":
            issues.append(ValidationIssue("INVALID_CURRENCY", "currencyCode must be KRW for observed T1 POC", True))
        if not isinstance(shipping, str) or not shipping.strip():
            issues.append(ValidationIssue("INVALID_SHIPPING_TYPE", "shippingType must be non-empty", True))

        mode = source.mode
        shipping_evidence = self._evidence_status(variables, "shippingType")
        if mode is RunMode.LIVE and shipping_evidence is not EvidenceStatus.VERIFIED:
            issues.append(
                ValidationIssue(
                    code="UNVERIFIED_SHIPPING_TYPE",
                    message="shippingType is not VERIFIED for this live task",
                    live_blocker=True,
                )
            )
        return ValidationResult(tuple(issues))

    def build_preflight(self, snapshot: ArmedRunSnapshot) -> AdapterPlan:
        origin_issues = [
            issue
            for issue in self.validate(snapshot).issues
            if issue.code in {"UNSUPPORTED_ORIGIN", "UNSUPPORTED_TARGET_PATH", "ADAPTER_ID_MISMATCH", "ADAPTER_VERSION_MISMATCH"}
        ]
        if origin_issues:
            raise ValueError("; ".join(issue.message for issue in origin_issues))
        request = RequestSpec(
            origin="https://t1.fan",
            method="GET",
            path=self.preflight_path,
            effect=StepEffect.NONE,
            headers={},
            body=None,
            credential_mode="same-origin",
        )
        return AdapterPlan((AdapterStep("session_preflight", StepEffect.NONE, request=request),))

    def build_execution(self, snapshot: ArmedRunSnapshot) -> AdapterPlan:
        validation = self.validate(snapshot)
        if validation.issues:
            raise ValueError("; ".join(issue.message for issue in validation.issues))
        variables = self._variables(snapshot)
        if self._evidence_status(variables, "shippingType") is not EvidenceStatus.VERIFIED:
            # Even TEST can create a real checkout. Do not dispatch an irreversible
            # request with an unknown shipping contract merely because mode=TEST.
            raise ValueError("shippingType must be VERIFIED before checkout execution")

        body = {
            "inventoryItemAndQuantities": [
                {
                    "inventoryItemId": int(variables["inventoryItemId"]),
                    "quantity": int(variables["quantity"]),
                    "unitPrice": {
                        "currencyCode": str(variables["currencyCode"]),
                        "amount": int(variables["amount"]),
                    },
                    "shippingType": str(variables["shippingType"]),
                }
            ]
        }
        request = RequestSpec(
            origin="https://t1.fan",
            method="POST",
            path=self.checkout_path,
            effect=StepEffect.IRREVERSIBLE,
            headers=self.request_headers(),
            body=body,
            credential_mode="same-origin",
        )
        navigation = NavigationSpec(
            origin="https://t1.fan",
            path_template="/shop/checkout/{checkoutNumber}",
            required_variable="checkoutNumber",
            effect=StepEffect.NONE,
        )
        return AdapterPlan(
            (
                AdapterStep("create_checkout", StepEffect.IRREVERSIBLE, request=request),
                AdapterStep("navigate_checkout", StepEffect.NONE, navigation=navigation),
            )
        )

    def parse_response(self, step_id: str, *, http_status: int, body_text: str) -> AdapterStepResult:
        if step_id == "session_preflight":
            if 200 <= http_status < 300:
                return AdapterStepResult(status=AdapterParseStatus.PASS)
            error_code = "SESSION_INVALID" if http_status in {401, 403} else "PREFLIGHT_REJECTED"
            return AdapterStepResult(
                status=AdapterParseStatus.REJECTED,
                error_code=error_code,
                side_effect_status=SideEffectStatus.NONE,
            )

        if step_id != "create_checkout":
            raise AdapterError(f"unknown adapter parse step: {step_id}")

        if not 200 <= http_status < 300:
            if http_status == 401:
                code = "AUTHENTICATION"
            elif http_status == 403:
                code = "AUTHORIZATION"
            elif http_status == 429:
                code = "RATE_LIMITED"
            else:
                code = "SERVER_REJECTION"
            return AdapterStepResult(
                status=AdapterParseStatus.REJECTED,
                error_code=code,
                side_effect_status=SideEffectStatus.NONE,
            )

        try:
            body = json.loads(body_text)
        except json.JSONDecodeError:
            return AdapterStepResult(
                status=AdapterParseStatus.CONTRACT_MISMATCH,
                error_code="CHECKOUT_RESPONSE_NOT_JSON",
                side_effect_status=SideEffectStatus.AMBIGUOUS,
            )
        if not isinstance(body, Mapping):
            return AdapterStepResult(
                status=AdapterParseStatus.CONTRACT_MISMATCH,
                error_code="CHECKOUT_RESPONSE_NOT_OBJECT",
                side_effect_status=SideEffectStatus.AMBIGUOUS,
            )
        number = body.get("checkoutNumber")
        if isinstance(number, bool) or number is None or not str(number).isdigit():
            return AdapterStepResult(
                status=AdapterParseStatus.CONTRACT_MISMATCH,
                error_code="CHECKOUT_NUMBER_MISSING",
                side_effect_status=SideEffectStatus.AMBIGUOUS,
            )
        checkout_number = str(number)
        return AdapterStepResult(
            status=AdapterParseStatus.PASS,
            safe_data={"checkoutNumber": checkout_number},
            next_variables={"checkoutNumber": checkout_number},
            side_effect_status=SideEffectStatus.CONFIRMED,
        )

    def locators(self, snapshot: ArmedRunSnapshot) -> LocatorSet:
        # Strongest first: role/name or exact visible meaning. Generated CSS
        # module hashes are intentionally absent from the contract.
        return LocatorSet(
            consent=(
                LocatorStrategy(LocatorKind.TEXT, self.agreement_text),
                LocatorStrategy(LocatorKind.ROLE_NAME, self.agreement_text, role="checkbox"),
            ),
            payment=(
                LocatorStrategy(LocatorKind.ROLE_NAME, "결제하기", role="button"),
                LocatorStrategy(LocatorKind.TEXT, "결제하기"),
            ),
        )

    def manual_checkpoint(self, snapshot: ArmedRunSnapshot) -> ManualCheckpointSpec:
        return ManualCheckpointSpec(
            final_authorization_manual=True,
            allows_open_payment_ui=True,
            allows_card_entry=False,
            allows_otp_or_3ds=False,
        )

    @classmethod
    def checkout_path_for(cls, checkout_number: str) -> str:
        number = str(checkout_number).strip()
        if not number or not number.isdigit():
            raise ValueError("checkoutNumber must be a current-run numeric value")
        return f"/shop/checkout/{number}"

    @classmethod
    def legacy_variables(cls, task: TaskConfig) -> dict[str, Any]:
        pair_evidence = (
            EvidenceStatus.VERIFIED
            if (task.inventory_item_id, task.amount) in cls._OBSERVED_ITEM_PRICE_PAIRS
            else EvidenceStatus.INFERRED
        )
        shipping_evidence = EvidenceStatus.VERIFIED if task.shipping_type_verified else EvidenceStatus.UNKNOWN
        return {
            "inventoryItemId": task.inventory_item_id,
            "quantity": task.quantity,
            "amount": task.amount,
            "currencyCode": task.currency_code,
            "shippingType": task.shipping_type,
            "evidence": {
                "inventoryItemId": pair_evidence.value,
                "amount": pair_evidence.value,
                "shippingType": shipping_evidence.value,
            },
        }

    # ------------------------------------------------------------------
    # Architecture Spike compatibility surface, removed in later slices.
    # ------------------------------------------------------------------

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

    @classmethod
    def parse_checkout(cls, status: int, text: str) -> CheckoutResult:
        parsed = cls().parse_response("create_checkout", http_status=status, body_text=text)
        if parsed.status is AdapterParseStatus.PASS:
            return CheckoutResult(
                status=status,
                checkout_number=str(parsed.safe_data["checkoutNumber"]),
                retryable=False,
                message="checkout created",
            )
        if parsed.status is AdapterParseStatus.CONTRACT_MISMATCH:
            raise AdapterError(parsed.error_code or "checkout contract mismatch")
        return CheckoutResult(
            status=status,
            checkout_number=None,
            retryable=False,
            message=f"T1 checkout rejected with HTTP {status}",
        )

    @classmethod
    def checkout_url(cls, checkout_number: str) -> str:
        return f"https://t1.fan{cls.checkout_path_for(checkout_number)}"
