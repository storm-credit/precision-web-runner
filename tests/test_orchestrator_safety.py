import inspect
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import precision_runner.service as service_module
from precision_runner.browser_bridge import BrowserResult, BrowserResultCategory
from precision_runner.models import RunMode, RunnerState, SideEffectStatus, TaskConfig
from precision_runner.service import RunnerService
from precision_runner.store import LocalStore


class FakeBrowser:
    def __init__(self):
        self.calls = []
        self.request_results = []
        self.navigate_results = []
        self.ensure_checked_result = BrowserResult(True, BrowserResultCategory.OK)
        self.click_result = BrowserResult(True, BrowserResultCategory.OK)

    def submit(self, action, *args, timeout=30.0):
        self.calls.append((action, args))
        if action == "open":
            spec = args[0]
            return BrowserResult(True, BrowserResultCategory.OK, final_url=spec.url)
        if action == "request":
            if not self.request_results:
                raise AssertionError("unexpected browser request")
            return self.request_results.pop(0)
        if action == "navigate":
            if self.navigate_results:
                return self.navigate_results.pop(0)
            spec, variables = args
            number = variables[spec.required_variable]
            return BrowserResult(
                True,
                BrowserResultCategory.OK,
                final_url=spec.origin + spec.path_template.replace("{" + spec.required_variable + "}", str(number)),
            )
        if action == "ensure_checked":
            return self.ensure_checked_result
        if action == "click_first":
            return self.click_result
        raise AssertionError(f"unexpected browser action {action}")

    def close(self):
        self.calls.append(("close", ()))


class OrchestratorSafetyTests(unittest.TestCase):
    def make_service(self, *, shipping_verified=True):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        browser = FakeBrowser()
        root = Path(tmp.name)
        service = RunnerService(data_dir=root, browser=browser, store=LocalStore(root))
        service.task = TaskConfig(
            target_time=(datetime.now().astimezone() + timedelta(hours=1)).isoformat(),
            shipping_type_verified=shipping_verified,
            auto_consent=False,
            auto_open_payment=False,
            max_retries=3,  # must be ignored by the forward orchestrator
        )
        self.addCleanup(service.close)
        return service, browser

    def preflight_pass(self, service, browser):
        browser.request_results.append(
            BrowserResult(
                True,
                BrowserResultCategory.OK,
                http_status=200,
                final_url="https://t1.fan/svc/shop/api/v1/carts/summary",
                safe_body_text='{"itemCount":0}',
            )
        )
        result = service.preflight()
        self.assertTrue(result["ok"])
        self.assertEqual(service.state, RunnerState.TESTED)

    def wait_terminal(self, service, *, timeout=1.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if service.state in {RunnerState.FAILED, RunnerState.WAITING_MANUAL, RunnerState.SUCCEEDED}:
                return
            time.sleep(0.01)
        self.fail(f"service did not reach terminal/checkpoint state; current={service.state}")

    def irreversible_request_calls(self, browser):
        calls = []
        for action, args in browser.calls:
            if action == "request" and getattr(args[0], "effect", None) is not None:
                if args[0].effect.value == "IRREVERSIBLE":
                    calls.append((action, args))
        return calls

    def test_live_arm_blocks_unknown_signature_shipping(self):
        service, browser = self.make_service(shipping_verified=False)
        self.preflight_pass(service, browser)
        with self.assertRaisesRegex(ValueError, "shippingType"):
            service.arm()
        self.assertIsNone(service.active_run_id)
        self.assertIsNone(service._schedule_thread)

    def test_irreversible_transport_error_is_ambiguous_and_never_replayed(self):
        service, browser = self.make_service()
        self.preflight_pass(service, browser)
        browser.request_results.append(
            BrowserResult(False, BrowserResultCategory.TRANSPORT_ERROR, reason="connection reset")
        )

        service.run_now()
        self.wait_terminal(service)

        self.assertEqual(service.state, RunnerState.FAILED)
        self.assertEqual(service.last_error_info.code.value, "TRANSPORT_AMBIGUOUS")
        self.assertEqual(service.last_error_info.side_effect, SideEffectStatus.AMBIGUOUS)
        self.assertEqual(len(self.irreversible_request_calls(browser)), 1)
        self.assertIsNotNone(service.store.load_active_run())

    def test_server_rejection_is_terminal_without_retry(self):
        for status, expected_code in ((403, "AUTHORIZATION"), (429, "RATE_LIMITED"), (500, "SERVER_REJECTION")):
            with self.subTest(status=status):
                service, browser = self.make_service()
                self.preflight_pass(service, browser)
                browser.request_results.append(
                    BrowserResult(
                        False,
                        BrowserResultCategory.HTTP_ERROR,
                        http_status=status,
                        final_url="https://t1.fan/svc/shop/api/v1/order/checkout",
                        safe_body_text="{}",
                    )
                )
                service.run_now()
                self.wait_terminal(service)
                self.assertEqual(service.last_error_info.code.value, expected_code)
                self.assertEqual(service.last_error_info.side_effect, SideEffectStatus.NONE)
                self.assertEqual(len(self.irreversible_request_calls(browser)), 1)
                self.assertIsNone(service.store.load_active_run())

    def test_success_without_checkout_number_is_ambiguous_contract_mismatch(self):
        service, browser = self.make_service()
        self.preflight_pass(service, browser)
        browser.request_results.append(
            BrowserResult(
                True,
                BrowserResultCategory.OK,
                http_status=200,
                final_url="https://t1.fan/svc/shop/api/v1/order/checkout",
                safe_body_text="{}",
            )
        )
        service.run_now()
        self.wait_terminal(service)
        self.assertEqual(service.last_error_info.code.value, "CHECKOUT_NUMBER_MISSING")
        self.assertEqual(service.last_error_info.side_effect, SideEffectStatus.AMBIGUOUS)
        self.assertEqual(len(self.irreversible_request_calls(browser)), 1)
        self.assertIsNotNone(service.store.load_active_run())

    def test_confirmed_checkout_navigation_failure_preserves_number_without_second_checkout(self):
        service, browser = self.make_service()
        self.preflight_pass(service, browser)
        browser.request_results.append(
            BrowserResult(
                True,
                BrowserResultCategory.OK,
                http_status=200,
                final_url="https://t1.fan/svc/shop/api/v1/order/checkout",
                safe_body_text='{"checkoutNumber":2438052376391680}',
            )
        )
        browser.navigate_results.append(
            BrowserResult(False, BrowserResultCategory.BROWSER_UNAVAILABLE, reason="page crashed")
        )
        service.run_now()
        self.wait_terminal(service)

        self.assertEqual(service.last_checkout_number, "2438052376391680")
        self.assertEqual(service.last_error_info.code.value, "NAVIGATION_AFTER_SIDE_EFFECT")
        self.assertEqual(service.last_error_info.side_effect, SideEffectStatus.CONFIRMED)
        self.assertEqual(len(self.irreversible_request_calls(browser)), 1)
        active = service.store.load_active_run()
        self.assertEqual(active.safe_variables["checkoutNumber"], "2438052376391680")

    def test_existing_confirmed_checkout_can_be_reopened_without_new_checkout(self):
        service, browser = self.make_service()
        self.preflight_pass(service, browser)
        browser.request_results.append(
            BrowserResult(
                True,
                BrowserResultCategory.OK,
                http_status=200,
                final_url="https://t1.fan/svc/shop/api/v1/order/checkout",
                safe_body_text='{"checkoutNumber":2438052376391680}',
            )
        )
        browser.navigate_results.append(
            BrowserResult(False, BrowserResultCategory.BROWSER_UNAVAILABLE, reason="page crashed")
        )
        service.run_now()
        self.wait_terminal(service)
        irreversible_before = len(self.irreversible_request_calls(browser))

        browser.navigate_results.append(
            BrowserResult(
                True,
                BrowserResultCategory.OK,
                final_url="https://t1.fan/shop/checkout/2438052376391680",
            )
        )
        result = service.open_existing_checkout()

        self.assertTrue(result["ok"])
        self.assertEqual(service.state, RunnerState.WAITING_MANUAL)
        self.assertEqual(len(self.irreversible_request_calls(browser)), irreversible_before)

    def test_successful_automation_stops_at_waiting_manual_not_paid(self):
        service, browser = self.make_service()
        self.preflight_pass(service, browser)
        browser.request_results.append(
            BrowserResult(
                True,
                BrowserResultCategory.OK,
                http_status=200,
                final_url="https://t1.fan/svc/shop/api/v1/order/checkout",
                safe_body_text='{"checkoutNumber":2438052376391680}',
            )
        )
        service.run_now()
        self.wait_terminal(service)
        self.assertEqual(service.state, RunnerState.WAITING_MANUAL)
        self.assertNotEqual(service.state, RunnerState.SUCCEEDED)
        self.assertEqual(service.active_snapshot.mode, RunMode.TEST)

    def test_duplicate_execution_lease_does_not_dispatch_or_fail_authoritative_run(self):
        service, browser = self.make_service()
        self.preflight_pass(service, browser)
        snapshot = service._new_snapshot(RunMode.TEST)
        service.store.create_active_run(snapshot, state=RunnerState.RUNNING)
        service.active_snapshot = snapshot
        service.active_run_id = snapshot.run_id
        service.state = RunnerState.RUNNING
        service._execution_lock.acquire()
        try:
            service._execute_checkout_flow()
        finally:
            service._execution_lock.release()
        self.assertEqual(service.state, RunnerState.RUNNING)
        self.assertEqual(len(self.irreversible_request_calls(browser)), 0)

    def test_service_source_has_no_t1_request_or_locator_literals_or_generic_retry_loop(self):
        source = inspect.getsource(service_module)
        for forbidden in (
            "/svc/shop/api/v1/order/checkout",
            "inventoryItemId",
            "shippingType",
            "주문 내용과 약관에 동의합니다",
            "_create_checkout_with_retry",
            "max_retries",
            "retry_delay_ms",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
