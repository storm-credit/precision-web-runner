import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime
from pathlib import Path

from precision_runner.models import (
    ArmedRunSnapshot,
    ManualBoundaryPolicy,
    RunMode,
    RunnerState,
    RunStage,
    SideEffectStatus,
    TaskDefinition,
)
from precision_runner.store import LocalStore, StoreCorrupt, StoreError


class LocalStoreTests(unittest.TestCase):
    def make_task(self, *, name="task-v1"):
        return TaskDefinition(
            name=name,
            target_url="https://example.com/product/1",
            target_time="2026-08-17T12:00:00+09:00",
            adapter_id="example",
            adapter_version="1",
            mode=RunMode.LIVE,
            adapter_variables={"sku": "ABC", "nested": {"shipping": "STANDARD"}},
            prewarm_lead_ms=30_000,
            max_lateness_ms=1_500,
            manual_boundary=ManualBoundaryPolicy(),
        )

    def make_snapshot(self, task=None, *, run_id="run-1"):
        return ArmedRunSnapshot.from_task(
            task or self.make_task(),
            run_id=run_id,
            armed_at=datetime.fromisoformat("2026-08-17T11:55:00+09:00"),
        )

    def test_editable_task_and_active_snapshot_are_stored_separately(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = LocalStore(Path(tmp))
            task = self.make_task(name="before")
            store.save_task(task)
            snapshot = self.make_snapshot(task)
            store.create_active_run(snapshot)

            task.name = "after"
            task.adapter_variables["sku"] = "CHANGED"
            store.save_task(task)

            loaded_task = store.load_task()
            active = store.load_active_run()
            self.assertEqual(loaded_task.name, "after")
            self.assertEqual(active.snapshot.task_name, "before")
            self.assertEqual(active.snapshot.adapter_variables["sku"], "ABC")

    def test_active_snapshot_round_trip_remains_deeply_immutable(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = LocalStore(Path(tmp))
            store.create_active_run(self.make_snapshot())
            active = store.load_active_run()

            with self.assertRaises(FrozenInstanceError):
                active.snapshot.run_id = "changed"  # type: ignore[misc]
            with self.assertRaises(TypeError):
                active.snapshot.adapter_variables["sku"] = "changed"  # type: ignore[index]
            self.assertEqual(active.snapshot.adapter_variables["nested"]["shipping"], "STANDARD")

    def test_atomic_write_failure_is_visible(self):
        class FailingStore(LocalStore):
            def _atomic_write_json(self, path, payload):
                raise OSError("disk full")

        with tempfile.TemporaryDirectory() as tmp:
            store = FailingStore(Path(tmp))
            with self.assertRaises(StoreError):
                store.create_active_run(self.make_snapshot())
            self.assertFalse(store.active_run_path.exists())

    def test_corrupt_active_store_is_not_silently_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = LocalStore(Path(tmp))
            store.active_run_path.write_text("{not-json", encoding="utf-8")
            with self.assertRaises(StoreCorrupt):
                store.load_active_run()

    def test_running_or_ambiguous_record_survives_for_recovery_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = LocalStore(Path(tmp))
            snapshot = self.make_snapshot()
            store.create_active_run(snapshot)
            store.update_active_run(
                snapshot.run_id,
                state=RunnerState.RUNNING,
                stage=RunStage.DISPATCH,
                side_effect=SideEffectStatus.AMBIGUOUS,
            )

            active = store.load_active_run()
            self.assertEqual(active.state, RunnerState.RUNNING)
            self.assertEqual(active.side_effect, SideEffectStatus.AMBIGUOUS)
            self.assertEqual(active.snapshot.run_id, "run-1")

    def test_terminal_cancelled_record_moves_to_history_and_is_not_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = LocalStore(Path(tmp))
            snapshot = self.make_snapshot()
            store.create_active_run(snapshot)
            store.complete_active_run(
                snapshot.run_id,
                state=RunnerState.CANCELLED,
                stage=RunStage.PRECHECK,
                side_effect=SideEffectStatus.NONE,
            )

            self.assertIsNone(store.load_active_run())
            history = store.list_history()
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0].state, RunnerState.CANCELLED)
            self.assertEqual(history[0].snapshot.run_id, "run-1")

    def test_store_files_are_versioned(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = LocalStore(Path(tmp))
            store.save_task(self.make_task())
            store.create_active_run(self.make_snapshot())

            task_payload = json.loads(store.task_path.read_text(encoding="utf-8"))
            run_payload = json.loads(store.active_run_path.read_text(encoding="utf-8"))
            self.assertEqual(task_payload["schema_version"], 1)
            self.assertEqual(run_payload["schema_version"], 1)


if __name__ == "__main__":
    unittest.main()
