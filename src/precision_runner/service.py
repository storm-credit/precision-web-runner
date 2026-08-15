from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from .adapter_contract import AdapterParseStatus, AdapterPlan, AdapterStep, StepEffect
from .browser_bridge import BrowserBridge, BrowserResult, BrowserResultCategory, OpenSpec
from .models import (
    ArmedRunSnapshot,
    ErrorCode,
    ErrorInfo,
    Event,
    KST,
    ManualBoundaryPolicy,
    RunMode,
    RunnerState,
    RunStage,
    SideEffectStatus,
    TaskConfig,
    TaskDefinition,
)
from .scheduler import ScheduleRequest, Scheduler, SchedulerLease, SchedulerSignalKind
from .store import LocalStore, StoreCorrupt, StoreError
from .t1_adapter import T1Adapter

_ACTIVE_STATES = {
    RunnerState.ARMED,
    RunnerState.PREWARMING,
    RunnerState.RUNNING,
}

_DEFAULT_PREWARM_LEAD_MS = 30_000
_DEFAULT_MAX_LATENESS_MS = 2_000


class RunnerService:
    """POC orchestrator.

    R6 makes the adapter and browser contracts authoritative for execution. The
    service owns state, one-run leasing, side-effect classification, persistence,
    and stop/recovery policy. It does not construct site request payloads or DOM
    locators itself.
    """

    def __init__(
        self,
        data_dir: Path | None = None,
        browser: Any | None = None,
        store: LocalStore | None = None,
        scheduler: Scheduler | None = None,
        adapter: Any | None = None,
    ):
        self.data_dir = data_dir or (Path.home() / ".precision-web-runner")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.profile_dir = self.data_dir / "chrome-profile"
        self.task_path = self.data_dir / "task.json"  # temporary dashboard compatibility until R8
        self.log_path = self.data_dir / "runs.jsonl"  # replaced by typed logger in R7

        self.adapter = adapter or T1Adapter()
        self.browser = browser or BrowserBridge(self.profile_dir)
        self.store = store or LocalStore(self.data_dir)
        self.scheduler = scheduler or Scheduler()

        self._lock = threading.RLock()
        self._execution_lock = threading.Lock()
        self._cancel = threading.Event()
        self._schedule_thread: threading.Thread | None = None
        self._schedule_lease: SchedulerLease | None = None

        self.task = self._load_task()
        self.state = RunnerState.DRAFT
        self.events: list[Event] = []
        self.last_checkout_number: str | None = None
        self.last_error: str | None = None
        self.last_error_info: ErrorInfo | None = None
        self.active_snapshot: ArmedRunSnapshot | None = None
        self.active_run_id: str | None = None
        self._recovery_blocked = False
        self._consent_handled = False

        self._restore_recovery_state()
        if self._recovery_blocked:
            self._event("error", self.last_error or "Runner recovery blocked")
        else:
            self._event("info", "Runner ready")

    def close(self) -> None:
        self._cancel.set()
        self.browser.close()

    def _restore_recovery_state(self) -> None:
        try:
            prior = self.store.load_active_run()
        except (StoreCorrupt, StoreError) as exc:
            self.state = RunnerState.FAILED
            self.last_error_info = self._error_info(
                ErrorCode.LOCAL_STORAGE_FAILURE,
                RunStage.PRECHECK,
                f"local run state cannot be trusted: {exc}",
                SideEffectStatus.AMBIGUOUS,
                "Inspect or repair the local run store before another run.",
                run_id="recovery-unknown",
            )
            self.last_error = f"{self.last_error_info.code.value}: {self.last_error_info.message}"
            self._recovery_blocked = True
            return

        if prior is None:
            self.state = RunnerState.DRAFT
            return

        self.active_snapshot = prior.snapshot
        self.active_run_id = prior.snapshot.run_id
        dynamic_name = self._navigation_variable_name(prior.snapshot)
        if dynamic_name and dynamic_name in prior.safe_variables:
            self.last_checkout_number = str(prior.safe_variables[dynamic_name])
        self.state = RunnerState.FAILED
        self.last_error_info = self._error_info(
            ErrorCode.RECOVERY_REQUIRED,
            prior.stage,
            f"prior active run was left in {prior.state.value}/{prior.stage.value}",
            prior.side_effect if prior.side_effect is not SideEffectStatus.NONE else SideEffectStatus.AMBIGUOUS,
            "Inspect the existing run before any new irreversible action.",
            run_id=prior.snapshot.run_id,
        )
        self.last_error = f"RECOVERY_REQUIRED: prior active run {prior.snapshot.run_id} requires manual inspection"
        self._recovery_blocked = True

    def _load_task(self) -> TaskConfig:
        if not self.task_path.exists():
            return TaskConfig()
        try:
            return TaskConfig.from_dict(json.loads(self.task_path.read_text(encoding="utf-8")))
        except Exception:
            # This file is only the old dashboard compatibility representation.
            # The versioned LocalStore is authoritative for run-safety state.
            return TaskConfig()

    def _task_definition(self, mode: RunMode) -> TaskDefinition:
        variables_builder = getattr(self.adapter, "legacy_variables", None)
        if variables_builder is None:
            raise RuntimeError("configured adapter cannot map the current POC task format")
        return TaskDefinition(
            name=self.task.name,
            target_url=self.task.target_url,
            target_time=self.task.target_datetime().isoformat(),
            adapter_id=str(self.adapter.id),
            adapter_version=str(self.adapter.version),
            mode=mode,
            adapter_variables=variables_builder(self.task),
            prewarm_lead_ms=_DEFAULT_PREWARM_LEAD_MS,
            max_lateness_ms=_DEFAULT_MAX_LATENESS_MS,
            manual_boundary=ManualBoundaryPolicy(
                auto_consent=self.task.auto_consent,
                open_payment_ui=self.task.auto_open_payment,
            ),
        )

    def _new_snapshot(self, mode: RunMode) -> ArmedRunSnapshot:
        return ArmedRunSnapshot.from_task(
            self._task_definition(mode),
            run_id=str(uuid.uuid4()),
            armed_at=datetime.now(KST),
        )

    def save_task(self, data: dict[str, Any]) -> dict[str, Any]:
        task = TaskConfig.from_dict(data)
        errors = task.validate(require_shipping_confirmation=False)
        if errors:
            raise ValueError("; ".join(errors))
        with self._lock:
            if self.state in _ACTIVE_STATES or self.active_run_id is not None:
                raise RuntimeError("Cannot edit task while a run is active or awaiting recovery")
            self.task = task
            self.task_path.write_text(json.dumps(task.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
            self.store.save_task(self._task_definition(RunMode.TEST))
            self.state = RunnerState.DRAFT
            self.last_error = None
            self.last_error_info = None
            self._event("info", "Task saved; validation state reset")
        return task.to_dict()

    def status(self) -> dict[str, Any]:
        with self._lock:
            target = self.task.target_datetime()
            now = datetime.now(KST)
            return {
                "state": self.state.value,
                "now": now.isoformat(),
                "target": target.isoformat(),
                "secondsRemaining": max(0.0, (target - now).total_seconds()),
                "task": self.task.to_dict(),
                "runId": self.active_run_id,
                "runMode": self.active_snapshot.mode.value if self.active_snapshot else None,
                "lastCheckoutNumber": self.last_checkout_number,
                "lastError": self.last_error,
                "lastErrorInfo": self.last_error_info.to_dict() if self.last_error_info else None,
                "events": [e.to_dict() for e in self.events[-60:]],
            }

    def open_browser(self) -> dict[str, Any]:
        spec = OpenSpec(self.task.target_url, tuple(self.adapter.supported_origins))
        result = self.browser.submit("open", spec, timeout=40)
        if not result.ok:
            raise RuntimeError(result.reason or result.category.value)
        self._event("info", "Browser opened", {"url": result.final_url})
        return {"url": result.final_url, "title": result.safe_data.get("title", "")}

    def preflight(self) -> dict[str, Any]:
        with self._lock:
            if self.active_run_id is not None:
                raise RuntimeError("cannot run editable-task preflight while a run is active")
        snapshot = self._new_snapshot(RunMode.TEST)
        ok, error, status = self._perform_preflight(snapshot)
        with self._lock:
            if ok:
                self.state = RunnerState.TESTED
                self.last_error = None
                self.last_error_info = None
                self._event("info", "Preflight completed", {"status": status})
            else:
                self.state = RunnerState.DRAFT
                self.last_error_info = error
                self.last_error = f"{error.code.value}: {error.message}" if error else "preflight failed"
                self._event("warning", self.last_error, {"status": status})
        return {"ok": ok, "status": status, "error": error.to_dict() if error else None}

    def _assert_recovery_clear(self) -> None:
        if self._recovery_blocked or self.active_run_id is not None:
            raise RuntimeError("recovery inspection is required before another run can be armed")

    def _require_tested(self) -> None:
        if self.state is not RunnerState.TESTED:
            raise RuntimeError("task must pass preflight/test before execution")

    def arm(self) -> dict[str, Any]:
        with self._lock:
            self._assert_recovery_clear()
            self._require_tested()

        snapshot = self._new_snapshot(RunMode.LIVE)
        self._validate_execution_snapshot(snapshot)
        schedule_lease = self.scheduler.arm(
            ScheduleRequest(
                run_id=snapshot.run_id,
                target_at=snapshot.target_at,
                prewarm_lead_ms=snapshot.prewarm_lead_ms,
                max_lateness_ms=snapshot.max_lateness_ms,
            )
        )

        with self._lock:
            self._assert_recovery_clear()
            self._require_tested()
            self.store.create_active_run(
                snapshot,
                state=RunnerState.ARMED,
                stage=RunStage.PRECHECK,
                side_effect=SideEffectStatus.NONE,
            )
            self.active_snapshot = snapshot
            self.active_run_id = snapshot.run_id
            self._schedule_lease = schedule_lease
            self._cancel = threading.Event()
            self.state = RunnerState.ARMED
            self.last_error = None
            self.last_error_info = None
            self.last_checkout_number = None
            self._consent_handled = False
            self._event(
                "info",
                "Runner armed",
                {
                    "target": snapshot.target_at.isoformat(),
                    "runId": snapshot.run_id,
                    "mode": snapshot.mode.value,
                    "maxLatenessMs": snapshot.max_lateness_ms,
                    "adapterVersion": snapshot.adapter_version,
                },
            )
            self._schedule_thread = threading.Thread(target=self._scheduled_run, daemon=True, name="scheduled-run")
            self._schedule_thread.start()
        return self.status()

    def cancel(self) -> dict[str, Any]:
        with self._lock:
            if self.state == RunnerState.RUNNING:
                raise RuntimeError("irreversible dispatch is in flight; cancel cannot claim to undo it")
            self._cancel.set()
            if self.state in {RunnerState.ARMED, RunnerState.PREWARMING}:
                run_id = self.active_run_id
                if run_id is None:
                    raise RuntimeError("active run identity is missing")
                stage = RunStage.PREWARM if self.state == RunnerState.PREWARMING else RunStage.PRECHECK
                self.store.complete_active_run(
                    run_id,
                    state=RunnerState.CANCELLED,
                    stage=stage,
                    side_effect=SideEffectStatus.NONE,
                )
                self.state = RunnerState.CANCELLED
                self.active_run_id = None
                self.active_snapshot = None
                self._schedule_lease = None
                self._event("warning", "Runner cancelled before irreversible dispatch")
        return self.status()

    def run_now(self) -> dict[str, Any]:
        with self._lock:
            self._assert_recovery_clear()
            self._require_tested()

        snapshot = self._new_snapshot(RunMode.TEST)
        self._validate_execution_snapshot(snapshot)

        with self._lock:
            self._assert_recovery_clear()
            self._require_tested()
            self.store.create_active_run(
                snapshot,
                state=RunnerState.RUNNING,
                stage=RunStage.DISPATCH,
                side_effect=SideEffectStatus.NONE,
            )
            self.active_snapshot = snapshot
            self.active_run_id = snapshot.run_id
            self._cancel = threading.Event()
            self.state = RunnerState.RUNNING
            self.last_error = None
            self.last_error_info = None
            self.last_checkout_number = None
            self._consent_handled = False
            self._event("info", "Immediate TEST checkout accepted", {"runId": snapshot.run_id, "mode": snapshot.mode.value})
            thread = threading.Thread(target=self._execute_checkout_flow, daemon=True, name="run-now")
            thread.start()
        return self.status()

    def continue_manual(self, *, open_payment: bool) -> dict[str, Any]:
        with self._lock:
            if self.state != RunnerState.WAITING_MANUAL or self.active_snapshot is None:
                raise RuntimeError("runner is not waiting at a manual checkpoint")
            snapshot = self.active_snapshot

        locators = self.adapter.locators(snapshot)
        if snapshot.manual_boundary.auto_consent and not self._consent_handled:
            consent = self.browser.submit("ensure_checked", locators.consent, timeout=20)
            if not consent.ok:
                raise RuntimeError(consent.reason or consent.category.value)
            self._consent_handled = True
            self._event("info", "Configured consent was handled at the manual checkpoint")
        if open_payment:
            payment = self.browser.submit("click_first", locators.payment, timeout=20)
            if not payment.ok:
                raise RuntimeError(payment.reason or payment.category.value)
            self._event("warning", "Payment UI opened; final authorization remains manual")
        return self.status()

    def open_existing_checkout(self) -> dict[str, Any]:
        with self._lock:
            if self.active_snapshot is None or not self.last_checkout_number:
                raise RuntimeError("no confirmed checkout is available for recovery")
            snapshot = self.active_snapshot
            number = self.last_checkout_number

        _, navigation = self._execution_steps(snapshot)
        result = self.browser.submit(
            "navigate",
            navigation.navigation,
            {navigation.navigation.required_variable: number},
            timeout=40,
        )
        if not result.ok:
            raise RuntimeError(result.reason or result.category.value)

        self._persist_active_state(
            state=RunnerState.WAITING_MANUAL,
            stage=RunStage.HANDOFF,
            side_effect=SideEffectStatus.CONFIRMED,
            safe_variables={navigation.navigation.required_variable: number},
        )
        with self._lock:
            self.state = RunnerState.WAITING_MANUAL
            self._recovery_blocked = False
            self.last_error = None
            self.last_error_info = None
            self._event("warning", "Existing confirmed checkout reopened; no new checkout was created")
        return {"ok": True, "url": result.final_url, "checkoutNumber": number}

    def _validate_execution_snapshot(self, snapshot: ArmedRunSnapshot) -> None:
        validation = self.adapter.validate(snapshot)
        if validation.issues:
            raise ValueError("; ".join(issue.message for issue in validation.issues))
        # Building the plan is also a live contract check. In particular, the
        # adapter may refuse an irreversible step with UNKNOWN evidence.
        self.adapter.build_execution(snapshot)

    def _perform_preflight(self, snapshot: ArmedRunSnapshot) -> tuple[bool, ErrorInfo | None, int]:
        plan = self.adapter.build_preflight(snapshot)
        request_step = next(step for step in plan.steps if step.request is not None)

        open_result = self.browser.submit(
            "open",
            OpenSpec(snapshot.target_url, tuple(self.adapter.supported_origins)),
            timeout=40,
        )
        if not open_result.ok:
            return False, self._browser_error(
                open_result,
                snapshot.run_id,
                RunStage.PRECHECK,
                irreversible=False,
            ), 0

        result = self.browser.submit("request", request_step.request, timeout=40)
        if result.category is BrowserResultCategory.TRANSPORT_ERROR:
            return False, self._error_info(
                ErrorCode.PREFLIGHT_TRANSIENT,
                RunStage.PRECHECK,
                result.reason or "preflight transport failure",
                SideEffectStatus.NONE,
                "Retry the safe preflight after checking the network.",
                snapshot.run_id,
            ), 0
        if result.http_status is None:
            return False, self._browser_error(
                result,
                snapshot.run_id,
                RunStage.PRECHECK,
                irreversible=False,
            ), 0

        parsed = self.adapter.parse_response(
            request_step.step_id,
            http_status=result.http_status,
            body_text=result.safe_body_text,
        )
        if parsed.status is AdapterParseStatus.PASS:
            return True, None, result.http_status
        code = ErrorCode.SESSION_INVALID if parsed.error_code in {"SESSION_INVALID", "AUTHENTICATION", "AUTHORIZATION"} else ErrorCode.PREFLIGHT_TRANSIENT
        return False, self._error_info(
            code,
            RunStage.PRECHECK,
            parsed.error_code or "preflight rejected",
            SideEffectStatus.NONE,
            "Log in/check the session, then run preflight again.",
            snapshot.run_id,
            result.http_status,
        ), result.http_status

    def _persist_active_state(
        self,
        *,
        state: RunnerState,
        stage: RunStage,
        side_effect: SideEffectStatus,
        error_code: str | None = None,
        safe_variables: Mapping[str, Any] | None = None,
    ) -> None:
        if self.active_run_id is None:
            raise StoreError("active run identity is missing")
        self.store.update_active_run(
            self.active_run_id,
            state=state,
            stage=stage,
            side_effect=side_effect,
            error_code=error_code,
            safe_variables=safe_variables,
        )

    def _scheduled_run(self) -> None:
        snapshot = self.active_snapshot
        lease = self._schedule_lease
        if snapshot is None or lease is None:
            self._set_failure(self._error_info(
                ErrorCode.LOCAL_STORAGE_FAILURE,
                RunStage.PRECHECK,
                "active scheduler snapshot/lease is missing",
                SideEffectStatus.NONE,
                "Re-arm after local state is repaired.",
                self.active_run_id or "unknown",
            ))
            return

        prewarm = lease.wait_for_prewarm(self._cancel)
        if prewarm.kind is SchedulerSignalKind.CANCELLED:
            return
        if prewarm.kind is SchedulerSignalKind.CLOCK_DISCONTINUITY:
            self._set_failure(self._error_info(
                ErrorCode.CLOCK_DISCONTINUITY,
                RunStage.PREWARM,
                f"clock/scheduler discontinuity before prewarm ({prewarm.clock_skew_ms:.0f} ms skew, {prewarm.wait_overshoot_ms:.0f} ms overshoot)",
                SideEffectStatus.NONE,
                "Rehearse again after fixing sleep/time stability.",
                snapshot.run_id,
            ))
            return

        try:
            self._persist_active_state(
                state=RunnerState.PREWARMING,
                stage=RunStage.PREWARM,
                side_effect=SideEffectStatus.NONE,
            )
        except StoreError as exc:
            self._set_failure(self._error_info(
                ErrorCode.LOCAL_STORAGE_FAILURE,
                RunStage.PREWARM,
                str(exc),
                SideEffectStatus.NONE,
                "Repair local storage before retrying.",
                snapshot.run_id,
            ))
            return

        with self._lock:
            self.state = RunnerState.PREWARMING
            self._event("info", "Prewarming browser", {"schedulerLatenessMs": round(prewarm.lateness_ms, 3)})

        preflight_ok, preflight_error, status = self._perform_preflight(snapshot)
        if not preflight_ok:
            assert preflight_error is not None
            self._set_failure(preflight_error)
            return
        self._event("info", "Preflight passed", {"status": status})

        target = lease.wait_for_target(self._cancel)
        if target.kind is SchedulerSignalKind.CANCELLED:
            return
        if target.kind is SchedulerSignalKind.CLOCK_DISCONTINUITY:
            self._set_failure(self._error_info(
                ErrorCode.CLOCK_DISCONTINUITY,
                RunStage.PREWARM,
                "clock/scheduler discontinuity before target",
                SideEffectStatus.NONE,
                "Do not catch up late; re-arm a future run after inspection.",
                snapshot.run_id,
            ))
            return
        if target.kind is SchedulerSignalKind.LATE:
            self._set_failure(self._error_info(
                ErrorCode.LATE_TARGET,
                RunStage.DISPATCH,
                f"target missed by {target.lateness_ms:.0f} ms",
                SideEffectStatus.NONE,
                "Do not dispatch late automatically.",
                snapshot.run_id,
            ))
            return
        if target.kind is not SchedulerSignalKind.TARGET_DUE:
            self._set_failure(self._error_info(
                ErrorCode.INTERNAL_ERROR,
                RunStage.DISPATCH,
                f"unexpected scheduler signal {target.kind.value}",
                SideEffectStatus.NONE,
                "Inspect the run before trying again.",
                snapshot.run_id,
            ))
            return

        self._event("info", "Scheduler target due", {
            "schedulerWakeAt": target.wall_at.isoformat(),
            "wakeLatenessMs": round(target.lateness_ms, 3),
        })
        self._execute_checkout_flow()

    def _execution_steps(self, snapshot: ArmedRunSnapshot) -> tuple[AdapterStep, AdapterStep]:
        plan: AdapterPlan = self.adapter.build_execution(snapshot)
        irreversible = next(
            (step for step in plan.steps if step.effect is StepEffect.IRREVERSIBLE and step.request is not None),
            None,
        )
        navigation = next((step for step in plan.steps if step.navigation is not None), None)
        if irreversible is None or navigation is None:
            raise RuntimeError("adapter execution plan lacks irreversible request/navigation steps")
        return irreversible, navigation

    def _navigation_variable_name(self, snapshot: ArmedRunSnapshot) -> str | None:
        try:
            _, navigation = self._execution_steps(snapshot)
        except Exception:
            return None
        assert navigation.navigation is not None
        return navigation.navigation.required_variable

    def _execute_checkout_flow(self) -> None:
        if not self._execution_lock.acquire(blocking=False):
            self._event("warning", "Duplicate execution signal blocked; authoritative run continues")
            return

        try:
            snapshot = self.active_snapshot
            if snapshot is None or self.active_run_id is None:
                self._set_failure(self._error_info(
                    ErrorCode.LOCAL_STORAGE_FAILURE,
                    RunStage.DISPATCH,
                    "active immutable snapshot is missing",
                    SideEffectStatus.NONE,
                    "Inspect local run state before another attempt.",
                    self.active_run_id or "unknown",
                ))
                return

            irreversible, navigation = self._execution_steps(snapshot)
            assert irreversible.request is not None
            assert navigation.navigation is not None

            try:
                self._persist_active_state(
                    state=RunnerState.RUNNING,
                    stage=RunStage.DISPATCH,
                    side_effect=SideEffectStatus.NONE,
                )
            except StoreError as exc:
                self._set_failure(self._error_info(
                    ErrorCode.LOCAL_STORAGE_FAILURE,
                    RunStage.DISPATCH,
                    str(exc),
                    SideEffectStatus.NONE,
                    "Repair local storage; irreversible request was not dispatched.",
                    snapshot.run_id,
                ))
                return

            with self._lock:
                self.state = RunnerState.RUNNING
                self._event("info", "Irreversible request dispatch started", {"dispatchAt": datetime.now(KST).isoformat()})

            # R6 invariant: exactly one dispatch attempt. There is deliberately no
            # generic retry loop around this irreversible request.
            browser_result: BrowserResult = self.browser.submit("request", irreversible.request, timeout=30)

            if browser_result.http_status is None:
                error = self._browser_error(
                    browser_result,
                    snapshot.run_id,
                    RunStage.DISPATCH,
                    irreversible=True,
                )
                self._set_failure(error)
                return

            parsed = self.adapter.parse_response(
                irreversible.step_id,
                http_status=browser_result.http_status,
                body_text=browser_result.safe_body_text,
            )

            if parsed.status is AdapterParseStatus.REJECTED:
                code = ErrorCode.RATE_LIMITED if parsed.error_code == "RATE_LIMITED" else ErrorCode.SERVER_REJECTION
                self._set_failure(self._error_info(
                    code,
                    RunStage.PARSE,
                    parsed.error_code or f"server rejected request with HTTP {browser_result.http_status}",
                    SideEffectStatus.NONE,
                    "Stop. Do not bypass or automatically replay the rejected action.",
                    snapshot.run_id,
                    browser_result.http_status,
                ))
                return

            if parsed.status in {AdapterParseStatus.CONTRACT_MISMATCH, AdapterParseStatus.AMBIGUOUS}:
                self._set_failure(self._error_info(
                    ErrorCode.CONTRACT_MISMATCH,
                    RunStage.PARSE,
                    parsed.error_code or "irreversible response contract mismatch",
                    SideEffectStatus.AMBIGUOUS,
                    "Inspect the site manually; do not replay the irreversible request.",
                    snapshot.run_id,
                    browser_result.http_status,
                ))
                return

            if parsed.status is not AdapterParseStatus.PASS or parsed.side_effect_status is not SideEffectStatus.CONFIRMED:
                self._set_failure(self._error_info(
                    ErrorCode.CONTRACT_MISMATCH,
                    RunStage.PARSE,
                    "adapter did not confirm the expected side effect",
                    SideEffectStatus.AMBIGUOUS,
                    "Inspect manually; do not replay.",
                    snapshot.run_id,
                    browser_result.http_status,
                ))
                return

            dynamic_name = navigation.navigation.required_variable
            dynamic_value = parsed.next_variables.get(dynamic_name)
            if dynamic_value is None:
                self._set_failure(self._error_info(
                    ErrorCode.CONTRACT_MISMATCH,
                    RunStage.PARSE,
                    f"adapter did not provide required dynamic variable {dynamic_name}",
                    SideEffectStatus.AMBIGUOUS,
                    "Inspect manually; do not replay.",
                    snapshot.run_id,
                    browser_result.http_status,
                ))
                return

            self.last_checkout_number = str(dynamic_value)
            safe_variables = dict(parsed.next_variables)
            self._persist_active_state(
                state=RunnerState.RUNNING,
                stage=RunStage.NAVIGATE,
                side_effect=SideEffectStatus.CONFIRMED,
                safe_variables=safe_variables,
            )
            self._event("info", "Irreversible step confirmed", {"dynamicVariable": dynamic_name})

            navigation_result = self.browser.submit(
                "navigate",
                navigation.navigation,
                safe_variables,
                timeout=40,
            )
            if not navigation_result.ok:
                self._set_failure(self._error_info(
                    ErrorCode.NAVIGATION_AFTER_SIDE_EFFECT,
                    RunStage.NAVIGATE,
                    navigation_result.reason or navigation_result.category.value,
                    SideEffectStatus.CONFIRMED,
                    "Reopen the existing confirmed checkout; do not create another checkout.",
                    snapshot.run_id,
                ))
                return

            locators = self.adapter.locators(snapshot)
            if snapshot.manual_boundary.auto_consent:
                consent = self.browser.submit("ensure_checked", locators.consent, timeout=20)
                if consent.ok:
                    self._consent_handled = True
                    self._event("info", "Configured consent handled")
                else:
                    self._event("warning", "Consent automation unavailable; handing off manually", {"reason": consent.reason or consent.category.value})

            if snapshot.manual_boundary.open_payment_ui and (not snapshot.manual_boundary.auto_consent or self._consent_handled):
                payment = self.browser.submit("click_first", locators.payment, timeout=20)
                if payment.ok:
                    self._event("warning", "Payment UI opened; final authorization remains manual")
                else:
                    self._event("warning", "Payment UI could not be opened automatically; handing off manually", {"reason": payment.reason or payment.category.value})

            self._persist_active_state(
                state=RunnerState.WAITING_MANUAL,
                stage=RunStage.HANDOFF,
                side_effect=SideEffectStatus.CONFIRMED,
                safe_variables=safe_variables,
            )
            with self._lock:
                self.state = RunnerState.WAITING_MANUAL
                self._recovery_blocked = False
                self._event("warning", "Manual payment checkpoint reached; runner will not authorize payment")
        except Exception as exc:
            snapshot = self.active_snapshot
            run_id = snapshot.run_id if snapshot else (self.active_run_id or "unknown")
            # An unexpected exception after RUNNING is conservatively ambiguous.
            effect = SideEffectStatus.AMBIGUOUS if self.state is RunnerState.RUNNING else SideEffectStatus.NONE
            self._set_failure(self._error_info(
                ErrorCode.INTERNAL_ERROR,
                RunStage.DISPATCH,
                str(exc),
                effect,
                "Inspect the current site state before any new attempt.",
                run_id,
            ))
        finally:
            self._execution_lock.release()

    def _browser_error(
        self,
        result: BrowserResult,
        run_id: str,
        stage: RunStage,
        *,
        irreversible: bool,
    ) -> ErrorInfo:
        if irreversible:
            return self._error_info(
                ErrorCode.TRANSPORT_AMBIGUOUS,
                stage,
                result.reason or result.category.value,
                SideEffectStatus.AMBIGUOUS,
                "Inspect the site manually; do not replay the irreversible request.",
                run_id,
                result.http_status,
            )
        code = ErrorCode.BROWSER_DISCONNECTED if result.category in {
            BrowserResultCategory.BROWSER_UNAVAILABLE,
            BrowserResultCategory.PROFILE_IN_USE,
        } else ErrorCode.INTERNAL_ERROR
        return self._error_info(
            code,
            stage,
            result.reason or result.category.value,
            SideEffectStatus.NONE,
            "Fix the browser/session condition and rerun the safe check.",
            run_id,
            result.http_status,
        )

    def _error_info(
        self,
        code: ErrorCode,
        stage: RunStage,
        message: str,
        side_effect: SideEffectStatus,
        next_action: str,
        run_id: str,
        http_status: int | None = None,
    ) -> ErrorInfo:
        return ErrorInfo(
            code=code,
            stage=stage,
            message=message,
            side_effect=side_effect,
            next_action=next_action,
            run_id=run_id,
            at=datetime.now(KST),
            http_status=http_status,
        )

    def _set_failure(self, error: ErrorInfo) -> None:
        with self._lock:
            self.state = RunnerState.FAILED
            self.last_error_info = error
            self.last_error = f"{error.code.value}: {error.message}"

            if self.active_run_id is not None:
                run_id = self.active_run_id
                if error.side_effect is SideEffectStatus.NONE:
                    try:
                        self.store.complete_active_run(
                            run_id,
                            state=RunnerState.FAILED,
                            stage=error.stage,
                            side_effect=error.side_effect,
                            error_code=error.code.value,
                        )
                    except StoreError:
                        self._recovery_blocked = True
                    else:
                        self.active_run_id = None
                        self.active_snapshot = None
                        self._schedule_lease = None
                else:
                    try:
                        self.store.update_active_run(
                            run_id,
                            state=RunnerState.FAILED,
                            stage=error.stage,
                            side_effect=error.side_effect,
                            error_code=error.code.value,
                        )
                    except StoreError:
                        pass
                    self._recovery_blocked = True

            self._event("error", self.last_error)

    def _event(self, level: str, message: str, detail: dict[str, Any] | None = None) -> None:
        # R7 replaces this compatibility logger with typed/redacted RunEvent persistence.
        event = Event(at=datetime.now(KST).isoformat(), level=level, message=message, detail=detail or {})
        with self._lock:
            self.events.append(event)
            try:
                with self.log_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
            except OSError:
                pass
