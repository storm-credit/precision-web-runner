import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from precision_runner.models import RunnerState, TaskConfig
from precision_runner.scheduler import SchedulerSignal, SchedulerSignalKind
from precision_runner.service import RunnerService
from precision_runner.store import LocalStore


class FakeBrowser:
    def __init__(self):
        self.calls = []

    def submit(self, action, *args, timeout=30.0):
        self.calls.append(action)
        return {"ok": True, "status": 200}

    def close(self):
        pass


class CancelledLease:
    def __init__(self, request):
        self.request = request

    def wait_for_prewarm(self, cancel):
        return SchedulerSignal(
            kind=SchedulerSignalKind.CANCELLED,
            run_id=self.request.run_id,
            wall_at=datetime.now().astimezone(),
            monotonic_at=time.monotonic(),
        )

    def wait_for_target(self, cancel):
        raise AssertionError("target should not be reached after cancelled prewarm")


class CapturingScheduler:
    def __init__(self):
        self.requests = []

    def arm(self, request):
        self.requests.append(request)
        return CancelledLease(request)


class ServiceSchedulerIntegrationTests(unittest.TestCase):
    def test_arm_builds_schedule_request_from_immutable_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            browser = FakeBrowser()
            scheduler = CapturingScheduler()
            store = LocalStore(Path(tmp))
            service = RunnerService(
                data_dir=Path(tmp),
                browser=browser,
                store=store,
                scheduler=scheduler,
            )
            service.task = TaskConfig(
                target_time=(datetime.now().astimezone() + timedelta(hours=1)).isoformat(),
                shipping_type_verified=True,
            )
            # R6 makes TESTED an explicit ARM prerequisite. This R3 regression
            # test focuses on snapshot -> scheduler request fidelity.
            service.state = RunnerState.TESTED

            service.arm()
            self.assertEqual(len(scheduler.requests), 1)
            request = scheduler.requests[0]
            snapshot = service.active_snapshot
            self.assertIsNotNone(snapshot)
            self.assertEqual(request.run_id, snapshot.run_id)
            self.assertEqual(request.target_at, snapshot.target_at)
            self.assertEqual(request.prewarm_lead_ms, snapshot.prewarm_lead_ms)
            self.assertEqual(request.max_lateness_ms, snapshot.max_lateness_ms)

            # The fake lease cancels the scheduler path before any browser work.
            service._schedule_thread.join(timeout=1)
            self.assertEqual(browser.calls, [])
            self.assertEqual(service.state, RunnerState.ARMED)
            service.cancel()


if __name__ == "__main__":
    unittest.main()
