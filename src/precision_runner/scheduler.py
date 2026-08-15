from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol


class SchedulerSignalKind(str, Enum):
    PREWARM_DUE = "PREWARM_DUE"
    TARGET_DUE = "TARGET_DUE"
    CANCELLED = "CANCELLED"
    LATE = "LATE"
    CLOCK_DISCONTINUITY = "CLOCK_DISCONTINUITY"


@dataclass(frozen=True, slots=True)
class ScheduleRequest:
    run_id: str
    target_at: datetime
    prewarm_lead_ms: int
    max_lateness_ms: int

    def validate(self) -> None:
        if not self.run_id.strip():
            raise ValueError("run_id is required")
        if self.target_at.tzinfo is None or self.target_at.utcoffset() is None:
            raise ValueError("target_at must be timezone-aware")
        if self.prewarm_lead_ms < 0:
            raise ValueError("prewarm_lead_ms must be non-negative")
        if self.max_lateness_ms < 0:
            raise ValueError("max_lateness_ms must be non-negative")


@dataclass(frozen=True, slots=True)
class SchedulerSignal:
    kind: SchedulerSignalKind
    run_id: str
    wall_at: datetime
    monotonic_at: float
    lateness_ms: float = 0.0
    clock_skew_ms: float = 0.0
    wait_overshoot_ms: float = 0.0


class Clock(Protocol):
    def wall_now(self) -> datetime: ...

    def monotonic(self) -> float: ...

    def wait(self, cancel: threading.Event, seconds: float) -> bool: ...


class SystemClock:
    def wall_now(self) -> datetime:
        return datetime.now().astimezone()

    def monotonic(self) -> float:
        return time.monotonic()

    def wait(self, cancel: threading.Event, seconds: float) -> bool:
        return cancel.wait(max(0.0, seconds))


class Scheduler:
    """Creates one monotonic scheduler lease from one wall-clock target.

    Target permission time is never shifted earlier. The wall clock is sampled
    only to convert the configured target into a monotonic deadline and to
    detect later discontinuity. A severe wait overshoot is also treated as a
    discontinuity so a suspend/stall is not missed merely because wall and
    monotonic clocks advanced together.
    """

    def __init__(
        self,
        *,
        clock: Clock | None = None,
        clock_discontinuity_tolerance_ms: int = 1_000,
        wait_discontinuity_tolerance_ms: int = 1_000,
    ):
        if clock_discontinuity_tolerance_ms < 0:
            raise ValueError("clock_discontinuity_tolerance_ms must be non-negative")
        if wait_discontinuity_tolerance_ms < 0:
            raise ValueError("wait_discontinuity_tolerance_ms must be non-negative")
        self.clock = clock or SystemClock()
        self.clock_discontinuity_tolerance_ms = clock_discontinuity_tolerance_ms
        self.wait_discontinuity_tolerance_ms = wait_discontinuity_tolerance_ms

    def arm(self, request: ScheduleRequest) -> "SchedulerLease":
        request.validate()
        wall_at_arm = self.clock.wall_now()
        if wall_at_arm.tzinfo is None or wall_at_arm.utcoffset() is None:
            raise ValueError("clock wall time must be timezone-aware")
        delay = (request.target_at - wall_at_arm).total_seconds()
        if delay <= 0:
            raise ValueError("target_at must be in the future when scheduler is armed")

        monotonic_at_arm = self.clock.monotonic()
        target_deadline = monotonic_at_arm + delay
        prewarm_deadline = max(
            monotonic_at_arm,
            target_deadline - (request.prewarm_lead_ms / 1000.0),
        )
        return SchedulerLease(
            request=request,
            clock=self.clock,
            wall_at_arm=wall_at_arm,
            monotonic_at_arm=monotonic_at_arm,
            prewarm_deadline=prewarm_deadline,
            target_deadline=target_deadline,
            clock_discontinuity_tolerance_ms=self.clock_discontinuity_tolerance_ms,
            wait_discontinuity_tolerance_ms=self.wait_discontinuity_tolerance_ms,
        )


class SchedulerLease:
    def __init__(
        self,
        *,
        request: ScheduleRequest,
        clock: Clock,
        wall_at_arm: datetime,
        monotonic_at_arm: float,
        prewarm_deadline: float,
        target_deadline: float,
        clock_discontinuity_tolerance_ms: int,
        wait_discontinuity_tolerance_ms: int,
    ):
        self.request = request
        self.clock = clock
        self.wall_at_arm = wall_at_arm
        self.monotonic_at_arm = monotonic_at_arm
        self.prewarm_deadline = prewarm_deadline
        self.target_deadline = target_deadline
        self.clock_discontinuity_tolerance_ms = clock_discontinuity_tolerance_ms
        self.wait_discontinuity_tolerance_ms = wait_discontinuity_tolerance_ms
        self._prewarm_signal: SchedulerSignal | None = None
        self._target_signal: SchedulerSignal | None = None
        self._lock = threading.Lock()

    def wait_for_prewarm(self, cancel: threading.Event) -> SchedulerSignal:
        with self._lock:
            if self._prewarm_signal is not None:
                return self._prewarm_signal
            signal = self._wait_for_deadline(
                deadline=self.prewarm_deadline,
                due_kind=SchedulerSignalKind.PREWARM_DUE,
                cancel=cancel,
                max_lateness_ms=None,
            )
            self._prewarm_signal = signal
            return signal

    def wait_for_target(self, cancel: threading.Event) -> SchedulerSignal:
        with self._lock:
            if self._target_signal is not None:
                return self._target_signal
            signal = self._wait_for_deadline(
                deadline=self.target_deadline,
                due_kind=SchedulerSignalKind.TARGET_DUE,
                cancel=cancel,
                max_lateness_ms=self.request.max_lateness_ms,
            )
            self._target_signal = signal
            return signal

    def _wait_for_deadline(
        self,
        *,
        deadline: float,
        due_kind: SchedulerSignalKind,
        cancel: threading.Event,
        max_lateness_ms: int | None,
    ) -> SchedulerSignal:
        while True:
            if cancel.is_set():
                return self._signal(SchedulerSignalKind.CANCELLED, deadline)

            discontinuity = self._clock_discontinuity_signal(deadline)
            if discontinuity is not None:
                return discontinuity

            now_mono = self.clock.monotonic()
            remaining = deadline - now_mono
            if remaining <= 0:
                break

            if remaining > 2.0:
                sleep_for = min(0.5, remaining - 1.0)
            elif remaining > 0.2:
                sleep_for = min(0.05, remaining / 2.0)
            else:
                sleep_for = min(0.005, remaining)
            sleep_for = max(0.001, sleep_for)

            before_wait = self.clock.monotonic()
            if self.clock.wait(cancel, sleep_for):
                return self._signal(SchedulerSignalKind.CANCELLED, deadline)
            after_wait = self.clock.monotonic()
            wait_overshoot_ms = max(0.0, (after_wait - before_wait - sleep_for) * 1000.0)
            if wait_overshoot_ms > self.wait_discontinuity_tolerance_ms:
                return self._discontinuity_signal(
                    deadline,
                    wait_overshoot_ms=wait_overshoot_ms,
                )

        discontinuity = self._clock_discontinuity_signal(deadline)
        if discontinuity is not None:
            return discontinuity

        signal = self._signal(due_kind, deadline)
        if (
            due_kind is SchedulerSignalKind.TARGET_DUE
            and max_lateness_ms is not None
            and signal.lateness_ms > max_lateness_ms
        ):
            return SchedulerSignal(
                kind=SchedulerSignalKind.LATE,
                run_id=signal.run_id,
                wall_at=signal.wall_at,
                monotonic_at=signal.monotonic_at,
                lateness_ms=signal.lateness_ms,
                clock_skew_ms=signal.clock_skew_ms,
                wait_overshoot_ms=signal.wait_overshoot_ms,
            )
        return signal

    def _clock_discontinuity_signal(self, deadline: float) -> SchedulerSignal | None:
        now_wall = self.clock.wall_now()
        now_mono = self.clock.monotonic()
        wall_elapsed = (now_wall - self.wall_at_arm).total_seconds()
        mono_elapsed = now_mono - self.monotonic_at_arm
        skew_ms = (wall_elapsed - mono_elapsed) * 1000.0
        if abs(skew_ms) <= self.clock_discontinuity_tolerance_ms:
            return None
        return SchedulerSignal(
            kind=SchedulerSignalKind.CLOCK_DISCONTINUITY,
            run_id=self.request.run_id,
            wall_at=now_wall,
            monotonic_at=now_mono,
            lateness_ms=max(0.0, (now_mono - deadline) * 1000.0),
            clock_skew_ms=skew_ms,
        )

    def _discontinuity_signal(
        self,
        deadline: float,
        *,
        wait_overshoot_ms: float,
    ) -> SchedulerSignal:
        now_mono = self.clock.monotonic()
        now_wall = self.clock.wall_now()
        wall_elapsed = (now_wall - self.wall_at_arm).total_seconds()
        mono_elapsed = now_mono - self.monotonic_at_arm
        return SchedulerSignal(
            kind=SchedulerSignalKind.CLOCK_DISCONTINUITY,
            run_id=self.request.run_id,
            wall_at=now_wall,
            monotonic_at=now_mono,
            lateness_ms=max(0.0, (now_mono - deadline) * 1000.0),
            clock_skew_ms=(wall_elapsed - mono_elapsed) * 1000.0,
            wait_overshoot_ms=wait_overshoot_ms,
        )

    def _signal(self, kind: SchedulerSignalKind, deadline: float) -> SchedulerSignal:
        now_mono = self.clock.monotonic()
        now_wall = self.clock.wall_now()
        wall_elapsed = (now_wall - self.wall_at_arm).total_seconds()
        mono_elapsed = now_mono - self.monotonic_at_arm
        return SchedulerSignal(
            kind=kind,
            run_id=self.request.run_id,
            wall_at=now_wall,
            monotonic_at=now_mono,
            lateness_ms=max(0.0, (now_mono - deadline) * 1000.0),
            clock_skew_ms=(wall_elapsed - mono_elapsed) * 1000.0,
        )
