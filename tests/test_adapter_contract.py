import unittest

from precision_runner.adapter_contract import (
    AdapterParseStatus,
    EvidenceStatus,
    LocatorKind,
    StepEffect,
)
from precision_runner.models import (
    ArmedRunSnapshot,
    ManualBoundaryPolicy,
    RunMode,
    SideEffectStatus,
    TaskDefinition,
)
from precision_runner.t1_adapter import T1Adapter


class AdapterContractTests(unittest.TestCase):
    def task(self, *, mode=RunMode.TEST, origin="https://t1.fan", shipping_evidence="VERIFIED"):
        return TaskDefinition(
            name="T1 adapter contract",
            target_url=f"{origin}/shop/products/525",
            target_time="2026-08-17T12:00:00+09:00",
            adapter_id="t1",
            adapter_version=T1Adapter.version,
            mode=mode,
            adapter_variables={
                "inventoryItemId": 3454,
                "quantity": 1,
                "amount": 500000,
                "currencyCode": "KRW",
                "shippingType": "STANDARD_DELIVERY",
                "evidence": {
                    "inventoryItemId": "VERIFIED",
                    "amount": "VERIFIED",
                    "shippingType": shipping_evidence,
                },
            },
            manual_boundary=ManualBoundaryPolicy(),
        )

    def snapshot(self, **kwargs):
        return ArmedRunSnapshot.from_task(
            self.task(**kwargs),
            run_id="run-r4",
            armed_at=self.task(**kwargs).target_datetime().replace(hour=11, minute=55),
        )

    def test_adapter_identity_and_origin_are_explicit(self):
        adapter = T1Adapter()
        self.assertEqual(adapter.id, "t1")
        self.assertTrue(adapter.version)
        self.assertEqual(adapter.supported_origins, ("https://t1.fan",))
        self.assertIn("same_origin_request", adapter.capabilities)
        self.assertNotIn("final_payment_authorization", adapter.capabilities)

    def test_variable_schema_marks_shipping_as_live_verified_requirement(self):
        schema = {item.key: item for item in T1Adapter().variable_schema()}
        self.assertEqual(schema["inventoryItemId"].type_name, "int")
        self.assertTrue(schema["shippingType"].required)
        self.assertTrue(schema["shippingType"].live_requires_verified)

    def test_wrong_origin_is_rejected(self):
        result = T1Adapter().validate(self.task(origin="https://example.com"))
        self.assertFalse(result.ok)
        self.assertIn("UNSUPPORTED_ORIGIN", {issue.code for issue in result.issues})

    def test_live_unknown_shipping_is_a_blocker(self):
        result = T1Adapter().validate(
            self.task(mode=RunMode.LIVE, shipping_evidence="UNKNOWN")
        )
        self.assertFalse(result.ok)
        issue = next(i for i in result.issues if i.code == "UNVERIFIED_SHIPPING_TYPE")
        self.assertTrue(issue.live_blocker)

    def test_execution_plan_requires_verified_shipping_even_in_test_mode(self):
        snapshot = self.snapshot(mode=RunMode.TEST, shipping_evidence="UNKNOWN")
        with self.assertRaisesRegex(ValueError, "shippingType"):
            T1Adapter().build_execution(snapshot)

    def test_direct_checkout_plan_matches_observed_shape_without_cart_only_field(self):
        snapshot = self.snapshot(mode=RunMode.TEST, shipping_evidence="VERIFIED")
        plan = T1Adapter().build_execution(snapshot)
        checkout = plan.steps[0]
        self.assertEqual(checkout.step_id, "create_checkout")
        self.assertEqual(checkout.effect, StepEffect.IRREVERSIBLE)
        self.assertEqual(checkout.request.origin, "https://t1.fan")
        self.assertEqual(checkout.request.method, "POST")
        self.assertEqual(checkout.request.path, "/svc/shop/api/v1/order/checkout")
        item = checkout.request.body["inventoryItemAndQuantities"][0]
        self.assertEqual(item["inventoryItemId"], 3454)
        self.assertEqual(item["unitPrice"], {"currencyCode": "KRW", "amount": 500000})
        self.assertEqual(item["shippingType"], "STANDARD_DELIVERY")
        self.assertNotIn("paymentOptionId", item)

    def test_preflight_plan_is_side_effect_free(self):
        plan = T1Adapter().build_preflight(self.snapshot(shipping_evidence="VERIFIED"))
        self.assertTrue(plan.steps)
        self.assertTrue(all(step.effect is StepEffect.NONE for step in plan.steps))
        self.assertEqual(plan.steps[0].request.method, "GET")

    def test_success_parser_extracts_only_current_response_checkout_number(self):
        result = T1Adapter().parse_response(
            "create_checkout",
            http_status=200,
            body_text='{"checkoutNumber":2438052376391680}',
        )
        self.assertEqual(result.status, AdapterParseStatus.PASS)
        self.assertEqual(result.safe_data["checkoutNumber"], "2438052376391680")
        self.assertEqual(result.next_variables["checkoutNumber"], "2438052376391680")
        self.assertEqual(result.side_effect_status, SideEffectStatus.CONFIRMED)

    def test_missing_checkout_number_is_contract_mismatch_and_ambiguous(self):
        result = T1Adapter().parse_response(
            "create_checkout",
            http_status=200,
            body_text="{}",
        )
        self.assertEqual(result.status, AdapterParseStatus.CONTRACT_MISMATCH)
        self.assertEqual(result.error_code, "CHECKOUT_NUMBER_MISSING")
        self.assertEqual(result.side_effect_status, SideEffectStatus.AMBIGUOUS)
        self.assertEqual(dict(result.next_variables), {})

    def test_rejections_are_semantic_and_never_marked_retryable(self):
        cases = {
            401: "AUTHENTICATION",
            403: "AUTHORIZATION",
            429: "RATE_LIMITED",
            500: "SERVER_REJECTION",
        }
        adapter = T1Adapter()
        for status, code in cases.items():
            with self.subTest(status=status):
                result = adapter.parse_response("create_checkout", http_status=status, body_text="{}")
                self.assertEqual(result.status, AdapterParseStatus.REJECTED)
                self.assertEqual(result.error_code, code)
                self.assertEqual(result.side_effect_status, SideEffectStatus.NONE)
                self.assertFalse(hasattr(result, "retryable"))

    def test_checkout_navigation_requires_explicit_dynamic_number(self):
        adapter = T1Adapter()
        with self.assertRaisesRegex(ValueError, "checkoutNumber"):
            adapter.checkout_path_for("")
        self.assertEqual(
            adapter.checkout_path_for("2438052376391680"),
            "/shop/checkout/2438052376391680",
        )

    def test_locators_prioritize_semantics_not_generated_css_hashes(self):
        locators = T1Adapter().locators(self.snapshot(shipping_evidence="VERIFIED"))
        self.assertIn(locators.consent[0].kind, {LocatorKind.ROLE_NAME, LocatorKind.TEXT})
        self.assertIn(locators.payment[0].kind, {LocatorKind.ROLE_NAME, LocatorKind.TEXT})
        self.assertFalse(any("PaymentButtonSection_" in (item.value or "") for item in locators.consent + locators.payment))

    def test_manual_checkpoint_keeps_final_authorization_manual(self):
        checkpoint = T1Adapter().manual_checkpoint(self.snapshot(shipping_evidence="VERIFIED"))
        self.assertTrue(checkpoint.final_authorization_manual)
        self.assertFalse(checkpoint.allows_card_entry)
        self.assertFalse(checkpoint.allows_otp_or_3ds)

    def test_evidence_enum_is_closed(self):
        self.assertEqual(
            {item.value for item in EvidenceStatus},
            {"VERIFIED", "INFERRED", "UNKNOWN"},
        )


if __name__ == "__main__":
    unittest.main()
