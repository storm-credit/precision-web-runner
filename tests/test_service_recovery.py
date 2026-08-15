import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from precision_runner.models import (
    ArmedRunSnapshot,
    ManualBoundaryPolicy,
    RunMode,
    RunnerState,
    RunStage,
    SideEffectStatus,
    TaskConfig,
    TaskDefinition,
)
from precision_runner.service import RunnerService
from precision_runner.store import LocalStore, StoreError


class FakeBrowser:
    def __init__(self):
        self.calls = []

    def submit(self, action, *args, timeout=30.0):
        self.calls.append((action, args, timeout))
        return {"ok": True, "status": 200}

    def close(self):
        self.calls.append(("close", (), 0))


class FailingCreateStore:
    def load_active_run(self):
        return None

    def create_active_run(self, snapshot, **kwargs):
        raise StoreError("disk full")

    def complete_active_run(self, *args, **kwargs):
        raise AssertionError("should not complete a run that was never persisted")


class RunnerServiceRecoveryTests(unittest.TestCase):
    def live_task_config(self):
        future = datetime.now().astimezone() + timedelta(hours=1)
        return TaskConfig(
            target_time=future.isoformat(),
            shipping_type_verified=True,
            auto_consent=False,
            auto_open_payment=False,
        )

    def generic_snapshot(self, *, run_id="recovery-run"):
        task = TaskDefinition(
            name="recovery test",
            target_url="https://example.com/product/1",
            target_time="2099-08-17T12:00:00+09:00",
            adapter_id="example",
            adapter_version="1",
            mode=RunMode.LIVE,
            adapter_variables={"sku": "ABC"},
            manual_boundary=ManualBoundaryPolicy(),
        )
        return ArmedRunSnapshot.from_task(
            task,
            run_id=run_id,
            armed_at=datetime.fromisoformat("2099-08-17T11:55:00+09:00"),
        )

    def test_storage_failure_blocks_arm_before_scheduler_or_browser_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            browser = FakeBrowser()
            service = RunnerService(
                data_dir=Path(tmp),
                browser=browser,
                store=FailingCreateStore(),
            )
            service.task = self.live_task_config()
            # R6 makes TESTED an explicit ARM prerequisite. This R2 regression
            # test is about persistence ordering, not preflight behavior.
            service.state = RunnerState.TESTED

            with self.assertRaises(StoreError):
                service.arm()

            self.assertEqual(service.state, RunnerState.TESTED)
            self.assertIsNone(service._schedule_thread)
            self.assertEqual(browser.calls, [])

    def test_restart_from_running_ambiguous_state_fails_closed_without_browser_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = LocalStore(root)
            snapshot = self.generic_snapshot()
            store.create_active_run(snapshot)
            store.update_active_run(
                snapshot.run_id,
                state=RunnerState.RUNNING,
                stage=RunStage.DISPATCH,
                side_effect=SideEffectStatus.AMBIGUOUS,
            )
            browser = FakeBrowser()

            service = RunnerService(data_dir=root, browser=browser, store=store)

            self.assertEqual(service.state, RunnerState.FAILED)
            self.assertIn("RECOVERY_REQUIRED", service.last_error)
            self.assertEqual(service.active_run_id, snapshot.run_id)
            self.assertEqual(browser.calls, [])
            with self.assertRaisesRegex(RuntimeError, "recovery"):
                service.arm()

    def test_restart_from_cancelled_history_does_not_resume_old_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = LocalStore(root)
            snapshot = self.generic_snapshot()
            store.create_active_run(snapshot)
            store.complete_active_run(
                snapshot.run_id,
                state=RunnerState.CANCELLED,
                stage=RunStage.PRECHECK,
                side_effect=SideEffectStatus.NONE,
            )
            browser = FakeBrowser()

            service = RunnerService(data_dir=root, browser=browser, store=store)

            self.assertEqual(service.state, RunnerState.DRAFT)
            self.assertIsNone(service.active_run_id)
            self.assertIsNone(service.last_error)
            self.assertEqual(browser.calls, [])

    def test_successful_arm_persists_snapshot_before_schedule_thread_starts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            browser = FakeBrowser()
            store = LocalStore(root)
            service = RunnerService(data_dir=root, browser=browser, store=store)
            service.task = self.live_task_config()
            service.state = RunnerState.TESTED

            service.arm()

            active = store.load_active_run()
            self.assertIsNotNone(active)
            self.assertEqual(active.state, RunnerState.ARMED)
            self.assertEqual(active.snapshot.run_id, service.active_run_id)
            self.assertEqual(active.snapshot.mode, RunMode.LIVE)
            self.assertIsNotNone(service._schedule_thread)
            service.cancel()


if __name__ == "__main__":
    unittest.main()
