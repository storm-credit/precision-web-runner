import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from precision_runner.models import ArmedRunSnapshot, ManualBoundaryPolicy, RunMode, RunnerState, RunStage, SideEffectStatus, TaskDefinition
from precision_runner.store import LocalStore


class StoreSafeVariableTests(unittest.TestCase):
    def snapshot(self):
        task = TaskDefinition(
            name="safe vars",
            target_url="https://example.com/product/1",
            target_time="2099-08-17T12:00:00+09:00",
            adapter_id="example",
            adapter_version="1",
            mode=RunMode.TEST,
            adapter_variables={"sku": "ABC"},
            manual_boundary=ManualBoundaryPolicy(),
        )
        return ArmedRunSnapshot.from_task(
            task,
            run_id="run-safe",
            armed_at=datetime.fromisoformat("2099-08-17T11:55:00+09:00"),
        )

    def test_safe_dynamic_variable_round_trips_with_active_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = LocalStore(Path(tmp))
            snapshot = self.snapshot()
            store.create_active_run(snapshot)
            store.update_active_run(
                snapshot.run_id,
                state=RunnerState.RUNNING,
                stage=RunStage.NAVIGATE,
                side_effect=SideEffectStatus.CONFIRMED,
                safe_variables={"checkoutNumber": "2438052376391680"},
            )
            loaded = store.load_active_run()
            self.assertEqual(loaded.safe_variables, {"checkoutNumber": "2438052376391680"})

    def test_updating_state_without_safe_variables_preserves_existing_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = LocalStore(Path(tmp))
            snapshot = self.snapshot()
            store.create_active_run(snapshot)
            store.update_active_run(
                snapshot.run_id,
                state=RunnerState.RUNNING,
                stage=RunStage.NAVIGATE,
                side_effect=SideEffectStatus.CONFIRMED,
                safe_variables={"checkoutNumber": "2438052376391680"},
            )
            store.update_active_run(
                snapshot.run_id,
                state=RunnerState.FAILED,
                stage=RunStage.NAVIGATE,
                side_effect=SideEffectStatus.CONFIRMED,
                error_code="NAVIGATION_AFTER_SIDE_EFFECT",
            )
            loaded = store.load_active_run()
            self.assertEqual(loaded.safe_variables["checkoutNumber"], "2438052376391680")


if __name__ == "__main__":
    unittest.main()
