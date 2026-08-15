"""Browser compatibility surface during R5/R6 migration.

`BrowserBridge` is the new generic browser contract. The old `RunnerService`
still imports `BrowserWorker`, so R5 points that name at a quarantined legacy
facade. R6 removes the facade when orchestration consumes AdapterPlan directly.

No site adapter is imported by this browser module itself.
"""

from .browser_bridge import (
    BrowserBridge,
    BrowserResult,
    BrowserResultCategory,
    BrowserUnavailable,
    OpenSpec,
    PlaywrightDriver,
)
from .legacy_t1_browser_facade import LegacyT1BrowserFacade

BrowserWorker = LegacyT1BrowserFacade

__all__ = [
    "BrowserBridge",
    "BrowserWorker",
    "BrowserResult",
    "BrowserResultCategory",
    "BrowserUnavailable",
    "OpenSpec",
    "PlaywrightDriver",
]
