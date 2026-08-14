import threading
import time
import unittest
from datetime import datetime, timedelta, timezone

from precision_runner.timing import seconds_until, wait_until


class TimingTests(unittest.TestCase):
    def test_seconds_until(self):
        tz = timezone.utc
        now = datetime(2026, 1, 1, tzinfo=tz)
        target = now + timedelta(seconds=2.5)
        self.assertAlmostEqual(seconds_until(target, now), 2.5)

    def test_wait_until_reaches_target(self):
        cancel = threading.Event()
        start = time.monotonic()
        target = datetime.now(timezone.utc) + timedelta(milliseconds=40)
        self.assertTrue(wait_until(target, cancel))
        self.assertGreaterEqual(time.monotonic() - start, 0.03)

    def test_wait_until_can_cancel(self):
        cancel = threading.Event()
        cancel.set()
        target = datetime.now(timezone.utc) + timedelta(seconds=1)
        self.assertFalse(wait_until(target, cancel))


if __name__ == "__main__":
    unittest.main()
