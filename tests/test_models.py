import unittest
from datetime import timedelta

from precision_runner.models import KST, TaskConfig


class TaskConfigTests(unittest.TestCase):
    def test_naive_time_is_interpreted_as_kst(self):
        task = TaskConfig(target_time="2026-08-17T12:00:00")
        self.assertEqual(task.target_datetime().utcoffset(), timedelta(hours=9))

    def test_shipping_confirmation_blocks_live_arm(self):
        task = TaskConfig(shipping_type_verified=False)
        errors = task.validate(require_shipping_confirmation=True)
        self.assertIn("shipping_type_verified must be confirmed before live checkout", errors)

    def test_auto_payment_requires_pre_authorized_consent(self):
        task = TaskConfig(auto_open_payment=True, auto_consent=False)
        self.assertIn("auto_open_payment requires auto_consent", task.validate())

    def test_aliases_are_accepted(self):
        task = TaskConfig.from_dict({"inventoryItemId": 99, "targetTime": "2026-08-17T12:00:00+09:00"})
        self.assertEqual(task.inventory_item_id, 99)
        self.assertEqual(task.target_datetime().tzinfo, KST)


if __name__ == "__main__":
    unittest.main()
