from __future__ import annotations

import queue
import threading
from concurrent.futures import Future
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from .models import TaskConfig
from .t1_adapter import T1Adapter


class BrowserUnavailable(RuntimeError):
    pass


class BrowserWorker:
    """Owns Playwright on one thread so browser objects never cross threads."""

    def __init__(self, profile_dir: Path):
        self.profile_dir = profile_dir
        self._queue: queue.Queue[tuple[Callable[..., Any] | None, tuple[Any, ...], Future[Any] | None]] = queue.Queue()
        self._thread = threading.Thread(target=self._loop, name="browser-worker", daemon=True)
        self._started = threading.Event()
        self._thread.start()
        self._started.wait(timeout=5)

    def submit(self, action: str, *args: Any, timeout: float = 30.0) -> Any:
        method = getattr(self, f"_action_{action}", None)
        if method is None:
            raise ValueError(f"unknown browser action: {action}")
        future: Future[Any] = Future()
        self._queue.put((method, args, future))
        return future.result(timeout=timeout)

    def close(self) -> None:
        self._queue.put((None, (), None))

    def _loop(self) -> None:
        self._playwright = None
        self._context = None
        self._page = None
        self._started.set()
        while True:
            method, args, future = self._queue.get()
            if method is None:
                self._shutdown()
                return
            try:
                result = method(*args)
            except Exception as exc:
                assert future is not None
                future.set_exception(exc)
            else:
                assert future is not None
                future.set_result(result)

    def _ensure_browser(self) -> None:
        if self._context is not None:
            return
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise BrowserUnavailable(
                'Playwright is not installed. Run: pip install -e ".[browser]"'
            ) from exc

        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self._playwright = sync_playwright().start()
        try:
            self._context = self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                channel="chrome",
                headless=False,
                viewport=None,
            )
        except Exception as exc:
            self._playwright.stop()
            self._playwright = None
            raise BrowserUnavailable(
                "Could not launch Google Chrome. Install Chrome and close any Precision Runner Chrome window, then retry."
            ) from exc
        self._page = self._context.pages[0] if self._context.pages else self._context.new_page()

    def _shutdown(self) -> None:
        try:
            if self._context is not None:
                self._context.close()
        finally:
            self._context = None
            self._page = None
            if self._playwright is not None:
                self._playwright.stop()
                self._playwright = None

    def _action_open(self, url: str) -> dict[str, Any]:
        self._ensure_browser()
        assert self._page is not None
        self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
        return {"url": self._page.url, "title": self._page.title()}

    def _action_preflight(self, task: TaskConfig) -> dict[str, Any]:
        self._ensure_browser()
        assert self._page is not None
        host = urlparse(self._page.url).hostname
        if host != "t1.fan":
            self._page.goto(task.target_url, wait_until="domcontentloaded", timeout=30000)
        result = self._page.evaluate(
            """async (path) => {
                const response = await fetch(path, {method: 'GET', credentials: 'same-origin', cache: 'no-store'});
                return {status: response.status, ok: response.ok, text: await response.text()};
            }""",
            T1Adapter.preflight_path,
        )
        return {
            "status": int(result["status"]),
            "ok": bool(result["ok"]),
            "url": self._page.url,
        }

    def _action_checkout(self, task: TaskConfig) -> dict[str, Any]:
        self._ensure_browser()
        assert self._page is not None
        host = urlparse(self._page.url).hostname
        if host != "t1.fan":
            self._page.goto(task.target_url, wait_until="domcontentloaded", timeout=30000)

        payload = T1Adapter.checkout_payload(task)
        headers = T1Adapter.request_headers()
        raw = self._page.evaluate(
            """async ({path, payload, headers}) => {
                try {
                    const response = await fetch(path, {
                        method: 'POST',
                        credentials: 'same-origin',
                        cache: 'no-store',
                        headers,
                        body: JSON.stringify(payload),
                    });
                    return {status: response.status, text: await response.text(), transportError: null};
                } catch (error) {
                    return {status: 0, text: '', transportError: String(error)};
                }
            }""",
            {"path": T1Adapter.checkout_path, "payload": payload, "headers": headers},
        )
        if raw.get("transportError"):
            return {"status": 0, "text": "", "transport_error": raw["transportError"]}
        return {"status": int(raw["status"]), "text": str(raw["text"]), "transport_error": None}

    def _action_navigate_checkout(self, checkout_number: str) -> dict[str, Any]:
        self._ensure_browser()
        assert self._page is not None
        url = T1Adapter.checkout_url(checkout_number)
        self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
        return {"url": self._page.url}

    def _action_consent(self) -> dict[str, Any]:
        self._ensure_browser()
        assert self._page is not None
        result = self._page.evaluate(
            """(agreementText) => {
                const label = [...document.querySelectorAll('label')].find(
                    el => (el.textContent || '').includes(agreementText)
                );
                if (!label) return {ok: false, reason: 'agreement label not found'};
                const box = label.querySelector('input[type="checkbox"]') || label.parentElement?.querySelector('input[type="checkbox"]');
                if (box && box.checked) return {ok: true, alreadyChecked: true};
                label.click();
                return {ok: true, alreadyChecked: false};
            }""",
            T1Adapter.agreement_text,
        )
        return dict(result)

    def _action_open_payment(self) -> dict[str, Any]:
        self._ensure_browser()
        assert self._page is not None
        result = self._page.evaluate(
            """() => {
                const buttons = [...document.querySelectorAll('button')];
                const button = buttons.find(b => (b.innerText || '').trim() === '결제하기') ||
                               buttons.find(b => (b.innerText || '').includes('결제하기'));
                if (!button) return {ok: false, reason: 'payment button not found'};
                if (button.disabled) return {ok: false, reason: 'payment button disabled'};
                button.click();
                return {ok: true};
            }"""
        )
        return dict(result)
