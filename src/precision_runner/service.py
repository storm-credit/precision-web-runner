from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .browser_worker import BrowserWorker
from .models import Event, KST, RunnerState, TaskConfig
from .t1_adapter import AdapterError, T1Adapter
from .timing import wait_until

_ACTIVE_STATES = {
    RunnerState.ARMED,
    RunnerState.PREWARMING,
    RunnerState.RUNNING,
}


class RunnerService:
    def __init__(self, data_dir: Path | None = None, browser: BrowserWorker | None = None):
        self.data_dir = data_dir or (Path.home() / ".precision-web-runner")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.profile_dir = self.data_dir / "chrome-profile"
        self.task_path = self.data_dir / "task.json"
        self.log_path = self.data_dir / "runs.jsonl"
        self._lock = threading.RLock()
        self._execution_lock = threading.Lock()
        self._cancel = threading.Event()
        self._schedule_thread: threading.Thread | None = None
        self.browser = browser or BrowserWorker(self.profile_dir)
        self.adapter = T1Adapter()
        self.task = self._load_task()
        self.state = RunnerState.READY
        self.events: list[Event] = []
        self.last_checkout_number: str | None = None
        self.last_error: str | None = None
        self._event("info", "Runner ready")

    def close(self) -> None:
        self._cancel.set()
        self.browser.close()

    def _load_task(self) -> TaskConfig:
        if not self.task_path.exists():
            return TaskConfig()
        try:
            return TaskConfig.from_dict(json.loads(self.task_path.read_text(encoding="utf-8")))
        except Exception:
            return TaskConfig()

    def save_task(self, data: dict[str, Any]) -> dict[str, Any]:
        task = TaskConfig.from_dict(data)
        errors = task.validate(require_shipping_confirmation=False)
        if errors:
            raise ValueError("; ".join(errors))
        with self._lock:
            if self.state in _ACTIVE_STATES:
                raise RuntimeError("Cannot edit task while runner is armed or running")
            self.task = task
            self.task_path.write_text(json.dumps(task.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
            self._event("info", "Task saved")
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
                "lastCheckoutNumber": self.last_checkout_number,
                "lastError": self.last_error,
                "events": [e.to_dict() for e in self.events[-60:]],
            }

    def open_browser(self) -> dict[str, Any]:
        result = self.browser.submit("open", self.task.target_url, timeout=40)
        self._event("info", "Browser opened", {"url": result.get("url")})
        return result

    def preflight(self) -> dict[str, Any]:
        result = self.browser.submit("preflight", self.task, timeout=40)
        level = "info" if result.get("ok") else "warning"
        self._event(level, "Preflight completed", {"status": result.get("status")})
        return result

    def arm(self) -> dict[str, Any]:
        errors = self.adapter.validate_target(self.task)
        if errors:
            raise ValueError("; ".join(errors))
        target = self.task.target_datetime()
        if target <= datetime.now(target.tzinfo):
            raise ValueError("target time is in the past")
        with self._lock:
            if self.state in _ACTIVE_STATES:
                raise RuntimeError("runner is already armed or running")
            self._cancel = threading.Event()
            self.state = RunnerState.ARMED
            self.last_error = None
            self.last_checkout_number = None
            self._event("info", "Runner armed", {"target": target.isoformat()})
            self._schedule_thread = threading.Thread(target=self._scheduled_run, daemon=True, name="scheduled-run")
            self._schedule_thread.start()
        return self.status()

    def cancel(self) -> dict[str, Any]:
        self._cancel.set()
        with self._lock:
            if self.state in _ACTIVE_STATES:
                self.state = RunnerState.CANCELLED
                self._event("warning", "Runner cancelled")
        return self.status()

    def run_now(self) -> dict[str, Any]:
        errors = self.adapter.validate_target(self.task)
        if errors:
            raise ValueError("; ".join(errors))
        with self._lock:
            if self.state in _ACTIVE_STATES:
                raise RuntimeError("runner is already armed or running")
            self._cancel = threading.Event()
            self.last_error = None
            self.last_checkout_number = None
            self.state = RunnerState.RUNNING
            self._event("info", "Immediate checkout test accepted")
            thread = threading.Thread(target=self._execute_checkout_flow, daemon=True, name="run-now")
            thread.start()
        return self.status()

    def continue_manual(self, *, open_payment: bool) -> dict[str, Any]:
        with self._lock:
            if self.state != RunnerState.WAITING_MANUAL:
                raise RuntimeError("runner is not waiting at a manual checkpoint")
        if self.task.auto_consent:
            consent = self.browser.submit("consent", timeout=20)
            if not consent.get("ok"):
                raise RuntimeError(consent.get("reason", "consent failed"))
            self._event("info", "Agreement checkbox handled by configured consent")
        if open_payment:
            payment = self.browser.submit("open_payment", timeout=20)
            if not payment.get("ok"):
                raise RuntimeError(payment.get("reason", "payment button failed"))
            self._event("warning", "Payment window opened; payment authorization remains manual")
        return self.status()

    def _scheduled_run(self) -> None:
        target = self.task.target_datetime()
        prewarm_at = target - timedelta(seconds=30)
        if datetime.now(target.tzinfo) < prewarm_at:
            if not wait_until(prewarm_at, self._cancel):
                return
        if self._cancel.is_set():
            return

        with self._lock:
            self.state = RunnerState.PREWARMING
            self._event("info", "Prewarming browser")
        try:
            self.browser.submit("open", self.task.target_url, timeout=40)
            result = self.browser.submit("preflight", self.task, timeout=40)
            if not result.get("ok"):
                raise RuntimeError(f"preflight returned HTTP {result.get('status')}")
        except Exception as exc:
            self._fail(f"preflight failed: {exc}")
            return

        self._event("info", "Preflight passed", {"status": result.get("status")})
        if not wait_until(target, self._cancel):
            return
        if self._cancel.is_set():
            return
        self._execute_checkout_flow()

    def _execute_checkout_flow(self) -> None:
        if not self._execution_lock.acquire(blocking=False):
            self._fail("duplicate execution prevented")
            return
        try:
            with self._lock:
                self.state = RunnerState.RUNNING
                self._event("info", "Checkout dispatch started", {"dispatchAt": datetime.now(KST).isoformat()})

            checkout_number = self._create_checkout_with_retry()
            self.last_checkout_number = checkout_number
            self._event("info", "Checkout created", {"checkoutNumber": checkout_number})
            self.browser.submit("navigate_checkout", checkout_number, timeout=40)
            self._event("info", "Checkout page opened")

            if self.task.auto_consent:
                consent = self.browser.submit("consent", timeout=20)
                if not consent.get("ok"):
                    raise RuntimeError(consent.get("reason", "consent failed"))
                self._event("info", "Agreement checkbox handled by configured consent")

            if self.task.auto_open_payment:
                payment = self.browser.submit("open_payment", timeout=20)
                if not payment.get("ok"):
                    raise RuntimeError(payment.get("reason", "payment button failed"))
                self._event("warning", "Payment window opened; finish payment manually")

            with self._lock:
                self.state = RunnerState.WAITING_MANUAL
                if self.task.auto_open_payment:
                    self._event("warning", "Manual checkpoint: complete PG payment yourself")
                else:
                    self._event("warning", "Manual checkpoint reached on checkout page")
        except Exception as exc:
            self._fail(str(exc))
        finally:
            self._execution_lock.release()

    def _create_checkout_with_retry(self) -> str:
        attempts = self.task.max_retries + 1
        for index in range(attempts):
            if self._cancel.is_set():
                raise RuntimeError("cancelled")
            raw = self.browser.submit("checkout", self.task, timeout=30)
            transport_error = raw.get("transport_error")
            if transport_error:
                if index + 1 < attempts:
                    self._event("warning", "Transport error; bounded retry scheduled", {"attempt": index + 1})
                    time.sleep(self.task.retry_delay_ms / 1000)
                    continue
                raise RuntimeError(f"transport error: {transport_error}")

            result = self.adapter.parse_checkout(int(raw["status"]), str(raw["text"]))
            if result.checkout_number:
                return result.checkout_number
            if result.retryable and index + 1 < attempts:
                self._event("warning", "Retryable HTTP response; bounded retry scheduled", {"status": result.status, "attempt": index + 1})
                time.sleep(self.task.retry_delay_ms / 1000)
                continue
            raise RuntimeError(result.message)
        raise AdapterError("checkout retry loop exhausted")

    def _fail(self, message: str) -> None:
        with self._lock:
            self.state = RunnerState.FAILED
            self.last_error = message
            self._event("error", message)

    def _event(self, level: str, message: str, detail: dict[str, Any] | None = None) -> None:
        event = Event(at=datetime.now(KST).isoformat(), level=level, message=message, detail=detail or {})
        with self._lock:
            self.events.append(event)
            try:
                with self.log_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
            except OSError:
                pass
