"""Compatibility import surface for the generic BrowserBridge.

The pre-design prototype exposed `BrowserWorker`. R5 makes the browser layer
site-agnostic; callers may keep importing BrowserWorker while R6 migrates the
orchestrator naming. No site adapter is imported here.
"""

from .browser_bridge import (
    BrowserBridge,
    BrowserResult,
    BrowserResultCategory,
    BrowserUnavailable,
    OpenSpec,
    PlaywrightDriver,
)

BrowserWorker = BrowserBridge

__all__ = [
    "BrowserBridge",
    "BrowserWorker",
    "BrowserResult",
    "BrowserResultCategory",
    "BrowserUnavailable",
    "OpenSpec",
    "PlaywrightDriver",
]
