import unittest

from precision_runner.adapter_contract import EvidenceStatus
from precision_runner.models import TaskConfig
from precision_runner.t1_adapter import T1Adapter


class T1EvidenceContractTests(unittest.TestCase):
    def test_signature_inventory_and_amount_are_observed_but_shipping_is_unknown(self):
        task = TaskConfig(
            inventory_item_id=3454,
            amount=500000,
            shipping_type="STANDARD_DELIVERY",
            shipping_type_verified=False,
        )
        variables = T1Adapter.legacy_variables(task)
        evidence = variables["evidence"]

        self.assertEqual(evidence["inventoryItemId"], EvidenceStatus.VERIFIED.value)
        self.assertEqual(evidence["amount"], EvidenceStatus.VERIFIED.value)
        self.assertEqual(evidence["shippingType"], EvidenceStatus.UNKNOWN.value)

    def test_shipping_is_verified_only_after_explicit_confirmation(self):
        task = TaskConfig(
            inventory_item_id=3229,
            amount=49000,
            shipping_type="STANDARD_DELIVERY",
            shipping_type_verified=True,
        )
        variables = T1Adapter.legacy_variables(task)
        self.assertEqual(variables["evidence"]["shippingType"], EvidenceStatus.VERIFIED.value)

    def test_unobserved_item_price_pair_is_inferred_not_verified(self):
        task = TaskConfig(
            inventory_item_id=999999,
            amount=12345,
            shipping_type="SOMETHING",
            shipping_type_verified=False,
        )
        variables = T1Adapter.legacy_variables(task)
        self.assertEqual(variables["evidence"]["inventoryItemId"], EvidenceStatus.INFERRED.value)
        self.assertEqual(variables["evidence"]["amount"], EvidenceStatus.INFERRED.value)
        self.assertEqual(variables["evidence"]["shippingType"], EvidenceStatus.UNKNOWN.value)

    def test_cart_payment_option_is_not_an_adapter_execution_variable(self):
        schema_keys = {item.key for item in T1Adapter().variable_schema()}
        self.assertNotIn("paymentOptionId", schema_keys)


if __name__ == "__main__":
    unittest.main()
