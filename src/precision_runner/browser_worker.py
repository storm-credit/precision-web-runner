"""Compatibility import name for the generic BrowserBridge.

R6 migrated RunnerService to AdapterPlan + BrowserResult directly, so the
site-specific legacy browser facade is no longer part of the execution path.
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
