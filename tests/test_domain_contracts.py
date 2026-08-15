import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime

from precision_runner.models import (
    ArmedRunSnapshot,
    ErrorCode,
    ErrorInfo,
    ManualBoundaryPolicy,
    RunEvent,
    RunMode,
    RunnerState,
    RunStage,
    SideEffectStatus,
    TaskDefinition,
)


class DomainContractTests(unittest.TestCase):
    def make_task(self, *, mode=RunMode.TEST):
        return TaskDefinition(
            name="adapter contract test",
            target_url="https://example.com/product/1",
            target_time="2026-08-17T12:00:00+09:00",
            adapter_id="example",
            adapter_version="1.2.3",
            mode=mode,
            adapter_variables={
                "sku": "ABC-1",
                "quantity": 1,
                "options": {"shipping": "STANDARD"},
                "tags": ["one", "two"],
            },
            prewarm_lead_ms=30_000,
            max_lateness_ms=1_500,
            manual_boundary=ManualBoundaryPolicy(
                auto_consent=False,
                open_payment_ui=False,
            ),
        )

    def test_snapshot_is_deeply_immutable(self):
        task = self.make_task(mode=RunMode.LIVE)
        snapshot = ArmedRunSnapshot.from_task(
            task,
            run_id="run-001",
            armed_at=datetime.fromisoformat("2026-08-17T11:55:00+09:00"),
        )

        with self.assertRaises(FrozenInstanceError):
            snapshot.run_id = "changed"  # type: ignore[misc]
        with self.assertRaises(TypeError):
            snapshot.adapter_variables["sku"] = "changed"  # type: ignore[index]
        self.assertEqual(snapshot.adapter_variables["tags"], ("one", "two"))

    def test_editing_task_after_arm_does_not_change_snapshot(self):
        task = self.make_task()
        snapshot = ArmedRunSnapshot.from_task(
            task,
            run_id="run-002",
            armed_at=datetime.fromisoformat("2026-08-17T11:55:00+09:00"),
        )

        task.name = "edited"
        task.adapter_variables["sku"] = "NEW"
        task.adapter_variables["options"]["shipping"] = "EXPRESS"
        task.adapter_variables["tags"].append("three")

        self.assertEqual(snapshot.task_name, "adapter contract test")
        self.assertEqual(snapshot.adapter_variables["sku"], "ABC-1")
        self.assertEqual(snapshot.adapter_variables["options"]["shipping"], "STANDARD")
        self.assertEqual(snapshot.adapter_variables["tags"], ("one", "two"))

    def test_test_and_live_modes_round_trip_distinctly(self):
        for mode in (RunMode.TEST, RunMode.LIVE):
            task = self.make_task(mode=mode)
            encoded = task.to_dict()
            self.assertEqual(encoded["mode"], mode.value)
            restored = TaskDefinition.from_dict(encoded)
            self.assertEqual(restored.mode, mode)

    def test_state_enum_contains_approved_design_vocabulary(self):
        self.assertEqual(
            {state.value for state in RunnerState},
            {
                "DRAFT",
                "TESTED",
                "ARMED",
                "PREWARMING",
                "RUNNING",
                "WAITING_MANUAL",
                "SUCCEEDED",
                "FAILED",
                "CANCELLED",
            },
        )

    def test_adapter_variables_are_not_generic_top_level_fields(self):
        task = self.make_task()
        self.assertEqual(task.adapter_variables["sku"], "ABC-1")
        self.assertNotIn("inventory_item_id", TaskDefinition.__dataclass_fields__)
        self.assertNotIn("shipping_type", TaskDefinition.__dataclass_fields__)
        self.assertNotIn("amount", TaskDefinition.__dataclass_fields__)
        self.assertNotIn("max_retries", TaskDefinition.__dataclass_fields__)

    def test_generic_task_requires_timezone_aware_iso_time(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            TaskDefinition(
                name="bad",
                target_url="https://example.com",
                target_time="2026-08-17T12:00:00",
                adapter_id="example",
                adapter_version="1",
            ).target_datetime()

        with self.assertRaisesRegex(ValueError, "ISO-8601"):
            TaskDefinition(
                name="bad",
                target_url="https://example.com",
                target_time="not-a-time",
                adapter_id="example",
                adapter_version="1",
            ).target_datetime()

    def test_error_info_has_stable_side_effect_aware_shape(self):
        error = ErrorInfo(
            code=ErrorCode.TRANSPORT_AMBIGUOUS,
            stage=RunStage.DISPATCH,
            message="response outcome unknown",
            side_effect=SideEffectStatus.AMBIGUOUS,
            next_action="Inspect the existing checkout manually; do not replay.",
            run_id="run-003",
            at=datetime.fromisoformat("2026-08-17T12:00:01+09:00"),
        )
        encoded = error.to_dict()
        self.assertEqual(encoded["code"], "TRANSPORT_AMBIGUOUS")
        self.assertEqual(encoded["stage"], "DISPATCH")
        self.assertEqual(encoded["side_effect"], "AMBIGUOUS")

    def test_run_event_is_typed_and_immutable(self):
        event = RunEvent(
            event_id="evt-1",
            run_id="run-004",
            sequence=1,
            at=datetime.fromisoformat("2026-08-17T11:59:59+09:00"),
            state=RunnerState.ARMED,
            stage=RunStage.PRECHECK,
            level="info",
            code="RUN_ARMED",
            message="armed",
            side_effect=SideEffectStatus.NONE,
            safe_detail={"target": "2026-08-17T12:00:00+09:00"},
        )
        self.assertEqual(event.to_dict()["state"], "ARMED")
        with self.assertRaises(FrozenInstanceError):
            event.sequence = 2  # type: ignore[misc]
        with self.assertRaises(TypeError):
            event.safe_detail["secret"] = "x"  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()
