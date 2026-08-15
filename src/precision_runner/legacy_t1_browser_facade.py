from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from .adapter_contract import LocatorKind, LocatorStrategy, NavigationSpec
from .browser_bridge import BrowserBridge, BrowserResultCategory, OpenSpec
from .models import ArmedRunSnapshot, KST, ManualBoundaryPolicy, RunMode, TaskConfig, TaskDefinition
from .t1_adapter import T1Adapter


class LegacyT1BrowserFacade:
    """Temporary R5 compatibility surface for the pre-R6 RunnerService.

    Site-specific translation is deliberately quarantined here so BrowserBridge
    itself is generic. R6 removes this facade when orchestration consumes
    AdapterPlan/BrowserResult directly.
    """

    def __init__(self, profile_dir: Path):
        self.bridge = BrowserBridge(profile_dir)
        self.adapter = T1Adapter()

    def close(self) -> None:
        self.bridge.close()

    def submit(self, action: str, *args: Any, timeout: float = 30.0) -> Any:
        method = getattr(self, f"_legacy_{action}", None)
        if method is None:
            raise ValueError(f"unknown legacy browser action: {action}")
        return method(*args, timeout=timeout)

    def _snapshot(self, task: TaskConfig, mode: RunMode = RunMode.TEST) -> ArmedRunSnapshot:
        definition = TaskDefinition(
            name=task.name,
            target_url=task.target_url,
            target_time=task.target_datetime().isoformat(),
            adapter_id=self.adapter.id,
            adapter_version=self.adapter.version,
            mode=mode,
            adapter_variables=self.adapter.legacy_variables(task),
            manual_boundary=ManualBoundaryPolicy(
                auto_consent=task.auto_consent,
                open_payment_ui=task.auto_open_payment,
            ),
        )
        return ArmedRunSnapshot.from_task(
            definition,
            run_id=f"legacy-browser-{uuid.uuid4()}",
            armed_at=datetime.now(KST),
        )

    def _legacy_open(self, url: str, *, timeout: float) -> dict[str, Any]:
        result = self.bridge.submit(
            "open",
            OpenSpec(url, self.adapter.supported_origins),
            timeout=timeout,
        )
        if not result.ok:
            raise RuntimeError(result.reason or result.category.value)
        return {"url": result.final_url, "title": result.safe_data.get("title", "")}

    def _ensure_target_open(self, task: TaskConfig, *, timeout: float) -> None:
        result = self.bridge.submit(
            "open",
            OpenSpec(task.target_url, self.adapter.supported_origins),
            timeout=timeout,
        )
        if not result.ok:
            raise RuntimeError(result.reason or result.category.value)

    def _legacy_preflight(self, task: TaskConfig, *, timeout: float) -> dict[str, Any]:
        self._ensure_target_open(task, timeout=timeout)
        plan = self.adapter.build_preflight(self._snapshot(task))
        request = plan.steps[0].request
        assert request is not None
        result = self.bridge.submit("request", request, timeout=timeout)
        return {
            "status": result.http_status or 0,
            "ok": result.ok,
            "url": result.final_url,
        }

    def _legacy_checkout(self, task: TaskConfig, *, timeout: float) -> dict[str, Any]:
        self._ensure_target_open(task, timeout=timeout)
        plan = self.adapter.build_execution(self._snapshot(task))
        request = plan.steps[0].request
        assert request is not None
        result = self.bridge.submit("request", request, timeout=timeout)
        if result.category is BrowserResultCategory.TRANSPORT_ERROR:
            return {"status": 0, "text": "", "transport_error": result.reason or "transport error"}
        return {
            "status": result.http_status or 0,
            "text": result.safe_body_text,
            "transport_error": None,
        }

    def _legacy_navigate_checkout(self, checkout_number: str, *, timeout: float) -> dict[str, Any]:
        spec = NavigationSpec(
            origin=self.adapter.supported_origins[0],
            path_template="/shop/checkout/{checkoutNumber}",
            required_variable="checkoutNumber",
        )
        result = self.bridge.submit(
            "navigate",
            spec,
            {"checkoutNumber": checkout_number},
            timeout=timeout,
        )
        if not result.ok:
            raise RuntimeError(result.reason or result.category.value)
        return {"url": result.final_url}

    def _legacy_consent(self, *, timeout: float) -> dict[str, Any]:
        strategies = (
            LocatorStrategy(LocatorKind.ROLE_NAME, self.adapter.agreement_text, role="checkbox"),
            LocatorStrategy(LocatorKind.TEXT, self.adapter.agreement_text),
        )
        result = self.bridge.submit("ensure_checked", strategies, timeout=timeout)
        return {
            "ok": result.ok,
            "reason": result.reason,
            "alreadyChecked": result.safe_data.get("alreadyChecked", False),
        }

    def _legacy_open_payment(self, *, timeout: float) -> dict[str, Any]:
        strategies = (
            LocatorStrategy(LocatorKind.ROLE_NAME, "결제하기", role="button"),
            LocatorStrategy(LocatorKind.TEXT, "결제하기"),
        )
        result = self.bridge.submit("click_first", strategies, timeout=timeout)
        return {"ok": result.ok, "reason": result.reason}
