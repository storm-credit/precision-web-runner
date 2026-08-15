from __future__ import annotations

import json
import queue
import threading
from concurrent.futures import Future
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol
from urllib.parse import quote, urlparse

from .adapter_contract import LocatorKind, LocatorStrategy, NavigationSpec, RequestSpec


class BrowserResultCategory(str, Enum):
    OK = "OK"
    HTTP_ERROR = "HTTP_ERROR"
    TRANSPORT_ERROR = "TRANSPORT_ERROR"
    ORIGIN_BLOCKED = "ORIGIN_BLOCKED"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    LOCATOR_NOT_FOUND = "LOCATOR_NOT_FOUND"
    LOCATOR_AMBIGUOUS = "LOCATOR_AMBIGUOUS"
    DISABLED = "DISABLED"
    PROFILE_IN_USE = "PROFILE_IN_USE"
    BROWSER_UNAVAILABLE = "BROWSER_UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class OpenSpec:
    url: str
    allowed_origins: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BrowserResult:
    ok: bool
    category: BrowserResultCategory
    http_status: int | None = None
    final_url: str | None = None
    safe_body_text: str = ""
    body_truncated: bool = False
    reason: str | None = None
    safe_data: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "safe_data", MappingProxyType(dict(self.safe_data)))


class BrowserUnavailable(RuntimeError):
    def __init__(self, message: str, category: BrowserResultCategory = BrowserResultCategory.BROWSER_UNAVAILABLE):
        super().__init__(message)
        self.category = category


class BrowserDriver(Protocol):
    @property
    def current_url(self) -> str: ...

    def open(self, url: str) -> Mapping[str, Any]: ...

    def request(self, spec: RequestSpec) -> Mapping[str, Any]: ...

    def navigate(self, url: str) -> Mapping[str, Any]: ...

    def locator_state(self, strategy: LocatorStrategy) -> Mapping[str, Any]: ...

    def click(self, strategy: LocatorStrategy) -> None: ...

    def close(self) -> None: ...


def _origin(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return ""
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"


class PlaywrightDriver:
    """Lazy Playwright driver owned by one BrowserBridge worker thread."""

    def __init__(self, profile_dir: Path):
        self.profile_dir = profile_dir
        self._playwright = None
        self._context = None
        self._page = None

    @property
    def current_url(self) -> str:
        self._ensure()
        assert self._page is not None
        return self._page.url

    @staticmethod
    def classify_launch_error(message: str) -> BrowserResultCategory:
        lowered = message.lower()
        profile_markers = (
            "processsingleton",
            "singletonlock",
            "user data directory is already in use",
            "profile is in use",
        )
        if any(marker in lowered for marker in profile_markers):
            return BrowserResultCategory.PROFILE_IN_USE
        return BrowserResultCategory.BROWSER_UNAVAILABLE

    def _ensure(self) -> None:
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
            category = self.classify_launch_error(str(exc))
            try:
                self._playwright.stop()
            finally:
                self._playwright = None
            if category is BrowserResultCategory.PROFILE_IN_USE:
                raise BrowserUnavailable(
                    "Precision Runner Chrome profile is already in use by another process.",
                    category,
                ) from exc
            raise BrowserUnavailable(
                "Could not launch Google Chrome. Install Chrome and verify the dedicated profile is available.",
                category,
            ) from exc
        self._page = self._context.pages[0] if self._context.pages else self._context.new_page()

    def open(self, url: str) -> Mapping[str, Any]:
        self._ensure()
        assert self._page is not None
        self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
        return {"url": self._page.url, "title": self._page.title()}

    def request(self, spec: RequestSpec) -> Mapping[str, Any]:
        self._ensure()
        assert self._page is not None
        payload = {
            "path": spec.path,
            "method": spec.method,
            "headers": dict(spec.headers),
            "body": dict(spec.body) if spec.body is not None else None,
            "credentialMode": spec.credential_mode,
        }
        return self._page.evaluate(
            """async ({path, method, headers, body, credentialMode}) => {
                try {
                    const response = await fetch(path, {
                        method,
                        credentials: credentialMode,
                        cache: 'no-store',
                        headers,
                        body: body === null || method === 'GET' || method === 'HEAD'
                            ? undefined
                            : JSON.stringify(body),
                    });
                    return {
                        status: response.status,
                        text: await response.text(),
                        url: response.url,
                        transportError: null,
                    };
                } catch (error) {
                    return {status: 0, text: '', url: '', transportError: String(error)};
                }
            }""",
            payload,
        )

    def navigate(self, url: str) -> Mapping[str, Any]:
        self._ensure()
        assert self._page is not None
        self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
        return {"url": self._page.url}

    def _locator(self, strategy: LocatorStrategy):
        self._ensure()
        assert self._page is not None
        if strategy.kind is LocatorKind.ROLE_NAME:
            if not strategy.role:
                raise ValueError("ROLE_NAME locator requires role")
            return self._page.get_by_role(strategy.role, name=strategy.value, exact=True)
        if strategy.kind is LocatorKind.TEXT:
            return self._page.get_by_text(strategy.value, exact=True)
        if strategy.kind is LocatorKind.DATA_ATTRIBUTE:
            return self._page.locator(f"[{strategy.value}]")
        if strategy.kind is LocatorKind.STRUCTURAL:
            return self._page.locator(strategy.value)
        raise ValueError(f"unsupported locator kind: {strategy.kind}")

    def locator_state(self, strategy: LocatorStrategy) -> Mapping[str, Any]:
        locator = self._locator(strategy)
        count = locator.count()
        result: dict[str, Any] = {"count": count}
        if count == 1:
            try:
                result["disabled"] = locator.is_disabled()
            except Exception:
                result["disabled"] = False
            try:
                result["checked"] = locator.is_checked()
            except Exception:
                result["checked"] = None
        return result

    def click(self, strategy: LocatorStrategy) -> None:
        self._locator(strategy).click()

    def close(self) -> None:
        try:
            if self._context is not None:
                self._context.close()
        finally:
            self._context = None
            self._page = None
            if self._playwright is not None:
                self._playwright.stop()
                self._playwright = None


class BrowserBridge:
    """Generic single-thread browser execution bridge.

    The bridge knows browser policy and generic command types only. It never
    imports a site adapter, never exports cookies, and never accepts arbitrary
    JavaScript from stored/user recipes.
    """

    _FORBIDDEN_HEADERS = {"cookie", "set-cookie", "authorization", "proxy-authorization"}

    def __init__(
        self,
        profile_dir: Path,
        *,
        driver: BrowserDriver | None = None,
        max_body_chars: int = 16_384,
    ):
        if max_body_chars <= 0:
            raise ValueError("max_body_chars must be positive")
        self.profile_dir = profile_dir
        self.max_body_chars = max_body_chars
        self._driver: BrowserDriver = driver or PlaywrightDriver(profile_dir)
        self._queue: queue.Queue[tuple[Callable[..., Any] | None, tuple[Any, ...], Future[Any] | None]] = queue.Queue()
        self._thread = threading.Thread(target=self._loop, name="browser-bridge", daemon=True)
        self._started = threading.Event()
        self._closed = False
        self._thread.start()
        self._started.wait(timeout=5)

    def submit(self, action: str, *args: Any, timeout: float = 30.0) -> BrowserResult:
        method = getattr(self, f"_action_{action}", None)
        if method is None:
            raise ValueError(f"unknown browser action: {action}")
        future: Future[BrowserResult] = Future()
        self._queue.put((method, args, future))
        return future.result(timeout=timeout)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._queue.put((None, (), None))
        self._thread.join(timeout=5)

    def _loop(self) -> None:
        self._started.set()
        while True:
            method, args, future = self._queue.get()
            if method is None:
                try:
                    self._driver.close()
                finally:
                    return
            try:
                result = method(*args)
            except BrowserUnavailable as exc:
                result = BrowserResult(False, exc.category, reason=str(exc))
            except Exception as exc:
                result = BrowserResult(False, BrowserResultCategory.BROWSER_UNAVAILABLE, reason=str(exc))
            assert future is not None
            future.set_result(result)

    @staticmethod
    def _normalize_origins(origins: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(origin.rstrip("/").lower() for origin in origins)

    def _action_open(self, spec: OpenSpec) -> BrowserResult:
        origin = _origin(spec.url)
        allowed = self._normalize_origins(spec.allowed_origins)
        if not origin or origin not in allowed:
            return BrowserResult(False, BrowserResultCategory.ORIGIN_BLOCKED, reason="open origin is not allow-listed")
        raw = self._driver.open(spec.url)
        final_url = str(raw.get("url", ""))
        if _origin(final_url) != origin:
            return BrowserResult(False, BrowserResultCategory.ORIGIN_BLOCKED, final_url=final_url, reason="navigation left allowed origin")
        return BrowserResult(True, BrowserResultCategory.OK, final_url=final_url, safe_data={"title": str(raw.get("title", ""))[:512]})

    def _request_policy_error(self, spec: RequestSpec) -> str | None:
        if _origin(spec.origin) != spec.origin.rstrip("/").lower():
            return "request origin must be an exact http(s) origin"
        parsed_path = urlparse(spec.path)
        if not spec.path.startswith("/") or parsed_path.scheme or parsed_path.netloc:
            return "request path must be relative to the declared origin"
        if spec.credential_mode != "same-origin":
            return "credential_mode must be same-origin"
        forbidden = {name.lower() for name in spec.headers} & self._FORBIDDEN_HEADERS
        if forbidden:
            return f"forbidden secret header: {sorted(forbidden)[0]}"
        return None

    def _action_request(self, spec: RequestSpec) -> BrowserResult:
        policy_error = self._request_policy_error(spec)
        if policy_error:
            return BrowserResult(False, BrowserResultCategory.POLICY_BLOCKED, reason=policy_error)
        current_origin = _origin(self._driver.current_url)
        if current_origin != spec.origin:
            return BrowserResult(False, BrowserResultCategory.ORIGIN_BLOCKED, final_url=self._driver.current_url, reason="browser page is not on request origin")

        raw = self._driver.request(spec)
        transport_error = raw.get("transportError") or raw.get("transport_error")
        if transport_error:
            return BrowserResult(False, BrowserResultCategory.TRANSPORT_ERROR, reason=str(transport_error))

        status = int(raw.get("status", 0))
        final_url = str(raw.get("url", self._driver.current_url))
        if final_url and _origin(final_url) != spec.origin:
            return BrowserResult(False, BrowserResultCategory.ORIGIN_BLOCKED, http_status=status, final_url=final_url, reason="response left declared origin")

        text = str(raw.get("text", ""))
        truncated = len(text) > self.max_body_chars
        bounded = text[: self.max_body_chars]
        ok = 200 <= status < 300
        return BrowserResult(
            ok=ok,
            category=BrowserResultCategory.OK if ok else BrowserResultCategory.HTTP_ERROR,
            http_status=status,
            final_url=final_url,
            safe_body_text=bounded,
            body_truncated=truncated,
        )

    def _action_navigate(self, spec: NavigationSpec, variables: Mapping[str, Any]) -> BrowserResult:
        origin = spec.origin.rstrip("/").lower()
        if _origin(origin) != origin:
            return BrowserResult(False, BrowserResultCategory.POLICY_BLOCKED, reason="navigation origin must be exact")
        if not spec.path_template.startswith("/"):
            return BrowserResult(False, BrowserResultCategory.POLICY_BLOCKED, reason="navigation path must be relative")
        if spec.required_variable not in variables:
            return BrowserResult(False, BrowserResultCategory.POLICY_BLOCKED, reason=f"missing navigation variable {spec.required_variable}")
        placeholder = "{" + spec.required_variable + "}"
        if placeholder not in spec.path_template:
            return BrowserResult(False, BrowserResultCategory.POLICY_BLOCKED, reason="navigation template is missing required placeholder")
        value = str(variables[spec.required_variable]).strip()
        if not value:
            return BrowserResult(False, BrowserResultCategory.POLICY_BLOCKED, reason="navigation variable is empty")
        path = spec.path_template.replace(placeholder, quote(value, safe=""))
        if "{" in path or "}" in path:
            return BrowserResult(False, BrowserResultCategory.POLICY_BLOCKED, reason="unresolved navigation placeholder")
        url = origin + path
        raw = self._driver.navigate(url)
        final_url = str(raw.get("url", ""))
        if _origin(final_url) != origin:
            return BrowserResult(False, BrowserResultCategory.ORIGIN_BLOCKED, final_url=final_url, reason="navigation left declared origin")
        return BrowserResult(True, BrowserResultCategory.OK, final_url=final_url)

    def _find_unique(self, strategies: tuple[LocatorStrategy, ...]) -> tuple[LocatorStrategy | None, BrowserResultCategory]:
        saw_ambiguous = False
        for strategy in strategies:
            state = self._driver.locator_state(strategy)
            count = int(state.get("count", 0))
            if count == 1:
                return strategy, BrowserResultCategory.OK
            if count > 1:
                saw_ambiguous = True
        return None, BrowserResultCategory.LOCATOR_AMBIGUOUS if saw_ambiguous else BrowserResultCategory.LOCATOR_NOT_FOUND

    def _action_click_first(self, strategies: tuple[LocatorStrategy, ...]) -> BrowserResult:
        strategy, category = self._find_unique(strategies)
        if strategy is None:
            return BrowserResult(False, category, reason="no unique semantic locator")
        state = self._driver.locator_state(strategy)
        if bool(state.get("disabled", False)):
            return BrowserResult(False, BrowserResultCategory.DISABLED, reason="target element is disabled")
        self._driver.click(strategy)
        return BrowserResult(True, BrowserResultCategory.OK, safe_data={"locatorKind": strategy.kind.value})

    def _action_ensure_checked(self, strategies: tuple[LocatorStrategy, ...]) -> BrowserResult:
        strategy, category = self._find_unique(strategies)
        if strategy is None:
            return BrowserResult(False, category, reason="no unique semantic consent locator")
        state = self._driver.locator_state(strategy)
        if bool(state.get("disabled", False)):
            return BrowserResult(False, BrowserResultCategory.DISABLED, reason="consent element is disabled")
        if state.get("checked") is True:
            return BrowserResult(True, BrowserResultCategory.OK, safe_data={"alreadyChecked": True, "locatorKind": strategy.kind.value})
        self._driver.click(strategy)
        return BrowserResult(True, BrowserResultCategory.OK, safe_data={"alreadyChecked": False, "locatorKind": strategy.kind.value})
