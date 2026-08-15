import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from precision_runner.models import RunnerState, RunStage, SideEffectStatus
from precision_runner.observability import EventLogger


class ObservabilityTests(unittest.TestCase):
    def make_logger(self, **kwargs):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "events.jsonl"
        return EventLogger(path, **kwargs), path

    def emit(self, logger, *, run_id="run-1", state=RunnerState.ARMED, code="RUN_ARMED", detail=None, message="armed"):
        return logger.emit(
            run_id=run_id,
            state=state,
            stage=RunStage.PRECHECK,
            level="info",
            code=code,
            message=message,
            side_effect=SideEffectStatus.NONE,
            safe_detail=detail or {},
            at=datetime(2026, 8, 17, 11, 55, tzinfo=timezone(timedelta(hours=9))),
        )

    def test_secret_and_pii_keys_never_persist(self):
        logger, path = self.make_logger()
        self.emit(
            logger,
            detail={
                "targetAt": "2026-08-17T12:00:00+09:00",
                "Cookie": "session=COOKIE_SECRET",
                "Authorization": "Bearer AUTH_SECRET",
                "token": "TOKEN_SECRET",
                "sessionId": "SESSION_SECRET",
                "csrf": "CSRF_SECRET",
                "nonce": "NONCE_SECRET",
                "email": "person@example.com",
                "phone": "010-1234-5678",
                "address": "Seoul secret address",
                "card": "4111 1111 1111 1111",
                "otp": "123456",
                "password": "PW_SECRET",
                "nested": {"Authorization": "NESTED_SECRET"},
            },
        )
        raw = path.read_text(encoding="utf-8")
        for forbidden in (
            "COOKIE_SECRET",
            "AUTH_SECRET",
            "TOKEN_SECRET",
            "SESSION_SECRET",
            "CSRF_SECRET",
            "NONCE_SECRET",
            "person@example.com",
            "010-1234-5678",
            "Seoul secret address",
            "4111 1111 1111 1111",
            "PW_SECRET",
            "NESTED_SECRET",
        ):
            self.assertNotIn(forbidden, raw)
        payload = json.loads(raw)
        self.assertEqual(payload["safe_detail"], {"targetAt": "2026-08-17T12:00:00+09:00"})

    def test_raw_request_response_body_fields_are_not_persisted(self):
        logger, path = self.make_logger()
        self.emit(
            logger,
            detail={
                "httpStatus": 200,
                "safe_body_text": "RAW_BODY_SECRET",
                "responseBody": "RAW_RESPONSE_SECRET",
                "body": "RAW_REQUEST_SECRET",
                "html": "RAW_HTML_SECRET",
            },
        )
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw)
        self.assertEqual(payload["safe_detail"]["httpStatus"], 200)
        for forbidden in ("RAW_BODY_SECRET", "RAW_RESPONSE_SECRET", "RAW_REQUEST_SECRET", "RAW_HTML_SECRET"):
            self.assertNotIn(forbidden, raw)

    def test_event_shape_round_trips_state_stage_code_side_effect_and_step(self):
        logger, _ = self.make_logger()
        event = logger.emit(
            run_id="run-shape",
            state=RunnerState.RUNNING,
            stage=RunStage.DISPATCH,
            step_id="create_checkout",
            level="warning",
            code="REQUEST_STARTED",
            message="request started",
            side_effect=SideEffectStatus.AMBIGUOUS,
            safe_detail={"method": "POST", "endpoint": "create_checkout"},
            at=datetime.now().astimezone(),
        )
        loaded = logger.read_recent(1)[0]
        self.assertEqual(loaded.event_id, event.event_id)
        self.assertEqual(loaded.run_id, "run-shape")
        self.assertEqual(loaded.state, RunnerState.RUNNING)
        self.assertEqual(loaded.stage, RunStage.DISPATCH)
        self.assertEqual(loaded.step_id, "create_checkout")
        self.assertEqual(loaded.code, "REQUEST_STARTED")
        self.assertEqual(loaded.side_effect, SideEffectStatus.AMBIGUOUS)

    def test_sequence_is_monotonic_per_run_and_event_ids_are_unique(self):
        logger, _ = self.make_logger()
        a1 = self.emit(logger, run_id="A")
        b1 = self.emit(logger, run_id="B")
        a2 = self.emit(logger, run_id="A")
        self.assertEqual((a1.sequence, a2.sequence), (1, 2))
        self.assertEqual(b1.sequence, 1)
        self.assertEqual(len({a1.event_id, a2.event_id, b1.event_id}), 3)

    def test_safe_timing_metrics_and_checkout_number_are_preserved(self):
        logger, _ = self.make_logger()
        event = self.emit(
            logger,
            detail={
                "targetAt": "2026-08-17T12:00:00+09:00",
                "requestStartedAt": "2026-08-17T12:00:00.012+09:00",
                "responseReceivedAt": "2026-08-17T12:00:00.120+09:00",
                "wakeLatenessMs": 4.25,
                "dispatchLatenessMs": 12.0,
                "responseLatencyMs": 108.0,
                "checkoutNumber": "2438052376391680",
            },
        )
        self.assertEqual(event.safe_detail["wakeLatenessMs"], 4.25)
        self.assertEqual(event.safe_detail["checkoutNumber"], "2438052376391680")

    def test_sensitive_patterns_in_message_are_redacted(self):
        logger, path = self.make_logger()
        self.emit(
            logger,
            message="Authorization: Bearer TOPSECRET email=user@example.com phone=010-5555-1234",
        )
        raw = path.read_text(encoding="utf-8")
        self.assertNotIn("TOPSECRET", raw)
        self.assertNotIn("user@example.com", raw)
        self.assertNotIn("010-5555-1234", raw)
        self.assertIn("REDACTED", raw)

    def test_detail_values_are_bounded(self):
        logger, _ = self.make_logger(max_detail_value_chars=24)
        event = self.emit(logger, detail={"reason": "x" * 200})
        self.assertLessEqual(len(event.safe_detail["reason"]), 24)

    def test_retention_keeps_only_recent_records(self):
        logger, _ = self.make_logger(max_records=3, max_file_bytes=100_000)
        for index in range(6):
            self.emit(logger, code=f"E{index}", message=f"event {index}")
        events = logger.read_recent(10)
        self.assertEqual(len(events), 3)
        self.assertEqual([event.code for event in events], ["E3", "E4", "E5"])

    def test_file_byte_limit_is_bounded(self):
        # The cap must be large enough for one typed event. The test verifies
        # retention/trimming, not an impossible cap smaller than the schema.
        max_bytes = 2_048
        logger, path = self.make_logger(max_records=100, max_file_bytes=max_bytes, max_detail_value_chars=80)
        for index in range(20):
            self.emit(logger, code=f"E{index}", detail={"reason": "x" * 80})
        self.assertLessEqual(path.stat().st_size, max_bytes)
        self.assertGreater(len(logger.read_recent(100)), 0)

    def test_recent_events_reconstruct_state_path_without_secret_fields(self):
        logger, _ = self.make_logger()
        path = [
            (RunnerState.ARMED, RunStage.PRECHECK, "RUN_ARMED"),
            (RunnerState.PREWARMING, RunStage.PREWARM, "PREWARM_STARTED"),
            (RunnerState.RUNNING, RunStage.DISPATCH, "REQUEST_STARTED"),
            (RunnerState.WAITING_MANUAL, RunStage.HANDOFF, "MANUAL_CHECKPOINT_REACHED"),
        ]
        for state, stage, code in path:
            logger.emit(
                run_id="run-path",
                state=state,
                stage=stage,
                level="info",
                code=code,
                message=code,
                side_effect=SideEffectStatus.NONE,
                safe_detail={"Cookie": "SECRET", "targetAt": "2026-08-17T12:00:00+09:00"},
                at=datetime.now().astimezone(),
            )
        events = logger.read_recent(10)
        self.assertEqual([event.state for event in events], [item[0] for item in path])
        self.assertTrue(all("Cookie" not in event.safe_detail for event in events))


if __name__ == "__main__":
    unittest.main()
