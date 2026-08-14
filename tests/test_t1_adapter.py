import unittest

from precision_runner.models import TaskConfig
from precision_runner.t1_adapter import AdapterError, T1Adapter


class T1AdapterTests(unittest.TestCase):
    def test_payload_matches_observed_contract(self):
        task = TaskConfig(inventory_item_id=3229, amount=49000, shipping_type="STANDARD_DELIVERY")
        payload = T1Adapter.checkout_payload(task)
        item = payload["inventoryItemAndQuantities"][0]
        self.assertEqual(item["inventoryItemId"], 3229)
        self.assertEqual(item["unitPrice"]["amount"], 49000)
        self.assertEqual(item["shippingType"], "STANDARD_DELIVERY")

    def test_checkout_number_is_extracted(self):
        result = T1Adapter.parse_checkout(200, '{"checkoutNumber":2438052376391680}')
        self.assertEqual(result.checkout_number, "2438052376391680")

    def test_403_is_not_retried(self):
        result = T1Adapter.parse_checkout(403, '{"message":"forbidden"}')
        self.assertFalse(result.retryable)
        self.assertIsNone(result.checkout_number)

    def test_500_fails_closed_without_retry(self):
        result = T1Adapter.parse_checkout(500, '{}')
        self.assertFalse(result.retryable)
        self.assertIsNone(result.checkout_number)

    def test_missing_checkout_number_fails_closed(self):
        with self.assertRaises(AdapterError):
            T1Adapter.parse_checkout(200, '{}')


if __name__ == "__main__":
    unittest.main()
