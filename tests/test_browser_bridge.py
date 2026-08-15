import inspect
import tempfile
import unittest
from pathlib import Path

import precision_runner.browser_bridge as browser_bridge_module
import precision_runner.browser_worker as browser_worker_module
from precision_runner.adapter_contract import (
    LocatorKind,
    LocatorStrategy,
    NavigationSpec,
    RequestSpec,
    StepEffect,
)
from precision_runner.browser_bridge import (
    BrowserBridge,
    BrowserResultCategory,
    OpenSpec,
    PlaywrightDriver,
)


class FakeDriver:
    def __init__(self, *, current_url="https://t1.fan/shop/products/525"):
        self.current_url = current_url
        self.calls = []
        self.request_result = {
            "status": 200,
            "text": "{}",
            "url": current_url,
        }
        self.locator_results = {}

    def open(self, url):
        self.calls.append(("open", url))
        self.current_url = url
        return {"url": url, "title": "fake"}

    def request(self, spec):
        self.calls.append(("request", spec))
        return dict(self.request_result)

    def navigate(self, url):
        self.calls.append(("navigate", url))
        self.current_url = url
        return {"url": url}

    def locator_state(self, strategy):
        self.calls.append(("locator_state", strategy))
        return dict(self.locator_results.get(strategy.value, {"count": 0}))

    def click(self, strategy):
        self.calls.append(("click", strategy))
        state = self.locator_results.get(strategy.value, {})
        if state.get("raise"):
            raise RuntimeError(state["raise"])
        return None

    def close(self):
        self.calls.append(("close",))


class BrowserBridgeTests(unittest.TestCase):
    def make_bridge(self, driver=None, *, max_body_chars=64):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        bridge = BrowserBridge(
            Path(self.tmp.name) / "profile",
            driver=driver or FakeDriver(),
            max_body_chars=max_body_chars,
        )
        self.addCleanup(bridge.close)
        return bridge

    def request_spec(self, **overrides):
        values = dict(
            origin="https://t1.fan",
            method="POST",
            path="/svc/shop/api/v1/order/checkout",
            effect=StepEffect.IRREVERSIBLE,
            headers={"Content-Type": "application/json"},
            body={"x": 1},
            credential_mode="same-origin",
        )
        values.update(overrides)
        return RequestSpec(**values)

    def test_browser_modules_do_not_import_t1_adapter(self):
        self.assertNotIn("T1Adapter", inspect.getsource(browser_bridge_module))
        self.assertNotIn("T1Adapter", inspect.getsource(browser_worker_module))

    def test_open_requires_exact_allowed_origin(self):
        driver = FakeDriver()
        bridge = self.make_bridge(driver)

        ok = bridge.submit(
            "open",
            OpenSpec("https://t1.fan/shop/products/525", ("https://t1.fan",)),
        )
        self.assertTrue(ok.ok)
        self.assertEqual(ok.category, BrowserResultCategory.OK)

        blocked = bridge.submit(
            "open",
            OpenSpec("https://evil.example/path", ("https://t1.fan",)),
        )
        self.assertFalse(blocked.ok)
        self.assertEqual(blocked.category, BrowserResultCategory.ORIGIN_BLOCKED)
        self.assertEqual([c for c in driver.calls if c[0] == "open"], [("open", "https://t1.fan/shop/products/525")])

    def test_same_origin_request_refuses_when_page_is_on_another_origin(self):
        driver = FakeDriver(current_url="https://example.com/")
        bridge = self.make_bridge(driver)
        result = bridge.submit("request", self.request_spec())
        self.assertFalse(result.ok)
        self.assertEqual(result.category, BrowserResultCategory.ORIGIN_BLOCKED)
        self.assertFalse(any(call[0] == "request" for call in driver.calls))

    def test_request_rejects_absolute_path_or_secret_headers(self):
        bridge = self.make_bridge(FakeDriver())

        absolute = bridge.submit(
            "request",
            self.request_spec(path="https://evil.example/steal"),
        )
        self.assertEqual(absolute.category, BrowserResultCategory.POLICY_BLOCKED)

        for header in ("Cookie", "Authorization", "Set-Cookie"):
            with self.subTest(header=header):
                result = bridge.submit(
                    "request",
                    self.request_spec(headers={header: "secret"}),
                )
                self.assertEqual(result.category, BrowserResultCategory.POLICY_BLOCKED)

    def test_request_requires_same_origin_credentials(self):
        bridge = self.make_bridge(FakeDriver())
        result = bridge.submit(
            "request",
            self.request_spec(credential_mode="include"),
        )
        self.assertEqual(result.category, BrowserResultCategory.POLICY_BLOCKED)

    def test_response_body_is_bounded_before_return(self):
        driver = FakeDriver()
        driver.request_result = {
            "status": 200,
            "text": "x" * 100,
            "url": "https://t1.fan/svc/shop/api/v1/order/checkout",
        }
        bridge = self.make_bridge(driver, max_body_chars=16)
        result = bridge.submit("request", self.request_spec())
        self.assertTrue(result.ok)
        self.assertEqual(len(result.safe_body_text), 16)
        self.assertTrue(result.body_truncated)

    def test_cross_origin_response_redirect_is_blocked(self):
        driver = FakeDriver()
        driver.request_result = {
            "status": 302,
            "text": "redirected",
            "url": "https://evil.example/collect",
        }
        bridge = self.make_bridge(driver)
        result = bridge.submit("request", self.request_spec())
        self.assertFalse(result.ok)
        self.assertEqual(result.category, BrowserResultCategory.ORIGIN_BLOCKED)

    def test_navigation_uses_declared_origin_and_current_run_variable(self):
        driver = FakeDriver()
        bridge = self.make_bridge(driver)
        spec = NavigationSpec(
            origin="https://t1.fan",
            path_template="/shop/checkout/{checkoutNumber}",
            required_variable="checkoutNumber",
        )
        result = bridge.submit(
            "navigate",
            spec,
            {"checkoutNumber": "2438052376391680"},
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.final_url, "https://t1.fan/shop/checkout/2438052376391680")

        missing = bridge.submit("navigate", spec, {})
        self.assertEqual(missing.category, BrowserResultCategory.POLICY_BLOCKED)

    def test_semantic_locator_click_uses_passed_strategy_only(self):
        driver = FakeDriver()
        semantic = LocatorStrategy(LocatorKind.ROLE_NAME, "결제하기", role="button")
        driver.locator_results[semantic.value] = {"count": 1, "disabled": False, "checked": None}
        bridge = self.make_bridge(driver)

        result = bridge.submit("click_first", (semantic,))
        self.assertTrue(result.ok)
        self.assertIn(("click", semantic), driver.calls)

    def test_ambiguous_locator_does_not_guess_click(self):
        driver = FakeDriver()
        strategy = LocatorStrategy(LocatorKind.TEXT, "결제하기")
        driver.locator_results[strategy.value] = {"count": 2, "disabled": False}
        bridge = self.make_bridge(driver)

        result = bridge.submit("click_first", (strategy,))
        self.assertFalse(result.ok)
        self.assertEqual(result.category, BrowserResultCategory.LOCATOR_AMBIGUOUS)
        self.assertFalse(any(call[0] == "click" for call in driver.calls))

    def test_profile_lock_error_is_distinguished(self):
        self.assertEqual(
            PlaywrightDriver.classify_launch_error(
                "Failed to create a ProcessSingleton for your profile. user data directory is already in use"
            ),
            BrowserResultCategory.PROFILE_IN_USE,
        )
        self.assertEqual(
            PlaywrightDriver.classify_launch_error("chrome executable missing"),
            BrowserResultCategory.BROWSER_UNAVAILABLE,
        )


if __name__ == "__main__":
    unittest.main()
