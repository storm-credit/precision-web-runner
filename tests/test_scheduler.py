import threading
import unittest
from datetime import datetime, timedelta, timezone

from precision_runner.scheduler import (
    ScheduleRequest,
    Scheduler,
    SchedulerSignalKind,
)


class FakeClock:
    def __init__(self, wall: datetime, monotonic: float = 100.0):
        self.wall = wall
        self.mono = monotonic
        self.wait_calls = []
        self.wall_extra_per_wait = 0.0
        self.monotonic_extra_per_wait = 0.0

    def wall_now(self):
        return self.wall

    def monotonic(self):
        return self.mono

    def wait(self, cancel, seconds):
        self.wait_calls.append(seconds)
        if cancel.is_set():
            return True
        advance = max(0.0, seconds)
        self.mono += advance + self.monotonic_extra_per_wait
        self.wall += timedelta(seconds=advance + self.wall_extra_per_wait)
        self.wall_extra_per_wait = 0.0
        self.monotonic_extra_per_wait = 0.0
        return cancel.is_set()

    def jump_wall(self, seconds):
        self.wall += timedelta(seconds=seconds)

    def jump_monotonic(self, seconds):
        self.mono += seconds


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.tz = timezone(timedelta(hours=9))
        self.start = datetime(2026, 8, 17, 11, 59, 0, tzinfo=self.tz)

    def request(self, *, target_seconds=60, prewarm_ms=30_000, late_ms=1500):
        return ScheduleRequest(
            run_id="run-1",
            target_at=self.start + timedelta(seconds=target_seconds),
            prewarm_lead_ms=prewarm_ms,
            max_lateness_ms=late_ms,
        )

    def test_arm_rejects_target_already_past(self):
        clock = FakeClock(self.start)
        scheduler = Scheduler(clock=clock)
        with self.assertRaisesRegex(ValueError, "future"):
            scheduler.arm(
                ScheduleRequest(
                    run_id="run-past",
                    target_at=self.start - timedelta(milliseconds=1),
                    prewarm_lead_ms=30_000,
                    max_lateness_ms=1000,
                )
            )

    def test_prewarmp_and_target_are_emitted_at_monotonic_deadlines(self):
        clock = FakeClock(self.start)
        lease = Scheduler(clock=clock).arm(self.request())
        cancel = threading.Event()

        prewarm = lease.wait_for_prewarm(cancel)
        self.assertEqual(prewarm.kind, SchedulerSignalKind.PREWARM_DUE)
        self.assertGreaterEqual(clock.monotonic(), lease.prewarm_deadline)
        self.assertLess(clock.monotonic(), lease.target_deadline)

        target = lease.wait_for_target(cancel)
        self.assertEqual(target.kind, SchedulerSignalKind.TARGET_DUE)
        self.assertGreaterEqual(clock.monotonic(), lease.target_deadline)
        self.assertGreaterEqual(target.lateness_ms, 0)
        self.assertLessEqual(target.lateness_ms, 1)

    def test_each_due_signal_is_logically_emitted_once(self):
        clock = FakeClock(self.start)
        lease = Scheduler(clock=clock).arm(self.request())
        cancel = threading.Event()

        first_prewarm = lease.wait_for_prewarm(cancel)
        second_prewarm = lease.wait_for_prewarm(cancel)
        self.assertIs(first_prewarm, second_prewarm)

        first_target = lease.wait_for_target(cancel)
        second_target = lease.wait_for_target(cancel)
        self.assertIs(first_target, second_target)

    def test_cancel_before_target_returns_cancelled_without_advancing_to_target(self):
        clock = FakeClock(self.start)
        lease = Scheduler(clock=clock).arm(self.request())
        cancel = threading.Event()
        cancel.set()

        signal = lease.wait_for_target(cancel)
        self.assertEqual(signal.kind, SchedulerSignalKind.CANCELLED)
        self.assertLess(clock.monotonic(), lease.target_deadline)

    def test_late_signal_when_scheduler_wakes_beyond_max_lateness(self):
        clock = FakeClock(self.start)
        lease = Scheduler(clock=clock).arm(self.request(late_ms=500))
        cancel = threading.Event()

        # Simulate oversleep/CPU stall using monotonic time. Keep wall in step so
        # this is lateness rather than a wall-clock discontinuity.
        clock.jump_monotonic(61.0)
        clock.jump_wall(61.0)
        signal = lease.wait_for_target(cancel)

        self.assertEqual(signal.kind, SchedulerSignalKind.LATE)
        self.assertGreater(signal.lateness_ms, 500)

    def test_wall_clock_jump_is_clock_discontinuity(self):
        clock = FakeClock(self.start)
        lease = Scheduler(clock=clock, clock_discontinuity_tolerance_ms=500).arm(self.request())
        cancel = threading.Event()

        clock.jump_wall(5.0)
        signal = lease.wait_for_prewarm(cancel)

        self.assertEqual(signal.kind, SchedulerSignalKind.CLOCK_DISCONTINUITY)
        self.assertGreater(abs(signal.clock_skew_ms), 500)

    def test_monotonic_jump_without_wall_progress_is_clock_discontinuity(self):
        clock = FakeClock(self.start)
        lease = Scheduler(clock=clock, clock_discontinuity_tolerance_ms=500).arm(self.request())
        cancel = threading.Event()

        clock.jump_monotonic(5.0)
        signal = lease.wait_for_prewarm(cancel)

        self.assertEqual(signal.kind, SchedulerSignalKind.CLOCK_DISCONTINUITY)
        self.assertGreater(abs(signal.clock_skew_ms), 500)

    def test_prewarm_due_immediately_when_armed_inside_prewarm_window(self):
        clock = FakeClock(self.start)
        lease = Scheduler(clock=clock).arm(self.request(target_seconds=10, prewarm_ms=30_000))
        cancel = threading.Event()

        before = clock.monotonic()
        signal = lease.wait_for_prewarm(cancel)
        self.assertEqual(signal.kind, SchedulerSignalKind.PREWARM_DUE)
        self.assertEqual(clock.monotonic(), before)

    def test_target_signal_never_occurs_before_target_deadline(self):
        clock = FakeClock(self.start)
        lease = Scheduler(clock=clock).arm(self.request(target_seconds=2, prewarm_ms=0))
        cancel = threading.Event()

        signal = lease.wait_for_target(cancel)
        self.assertEqual(signal.kind, SchedulerSignalKind.TARGET_DUE)
        self.assertGreaterEqual(signal.monotonic_at, lease.target_deadline)
        self.assertTrue(clock.wait_calls)


if __name__ == "__main__":
    unittest.main()
