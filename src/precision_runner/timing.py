from __future__ import annotations

import threading
import time
from datetime import datetime


def seconds_until(target: datetime, now: datetime | None = None) -> float:
    if target.tzinfo is None:
        raise ValueError("target must be timezone-aware")
    current = now or datetime.now(target.tzinfo)
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return (target - current).total_seconds()


def wait_until(target: datetime, cancel: threading.Event) -> bool:
    """Wait outside the browser using a monotonic deadline.

    Returns False if cancelled, True when the target is reached.
    """
    delay = max(0.0, seconds_until(target))
    deadline = time.monotonic() + delay

    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return True
        if cancel.is_set():
            return False

        if remaining > 2.0:
            sleep_for = min(1.0, remaining - 1.0)
        elif remaining > 0.2:
            sleep_for = min(0.05, remaining / 2)
        else:
            sleep_for = min(0.005, remaining)

        if cancel.wait(max(0.001, sleep_for)):
            return False
