# R5 Generic BrowserBridge + Typed BrowserResult Review

## Verdict

**R5 SLICE: PASS.**

This approves the browser execution boundary only. R6 still owns orchestration, semantic error/retry policy, and removal of the temporary legacy facade.

## Gap coverage

- G09 generic BrowserBridge: forward contract implemented
- G10 typed safe/bounded BrowserResult: implemented
- G25 profile ownership diagnosis: foundation added; Windows duplicate-profile rehearsal remains required

## Tests-first evidence

`tests/test_browser_bridge.py` was committed before implementation and verifies:
- BrowserBridge/browser_worker contain no direct T1Adapter import
- exact allowed-origin open policy
- same-origin request requires the page to be on the declared origin
- absolute/cross-origin request paths are rejected
- Cookie/Authorization/Set-Cookie injection is rejected
- credentials mode must be `same-origin`
- returned response body is bounded
- cross-origin response redirect is blocked
- navigation interpolates only the declared current-run variable
- semantic locator click behavior
- ambiguous locator does not guess-click
- Chrome profile-in-use errors are distinguished from general browser unavailable errors

Full unit CI passed after implementation.

## Implementation result

New `src/precision_runner/browser_bridge.py` provides:
- `BrowserResultCategory`
- immutable `BrowserResult`
- `OpenSpec`
- generic `BrowserDriver` protocol
- lazy `PlaywrightDriver`
- single-thread `BrowserBridge`
- guarded `open`, `request`, `navigate`, `ensure_checked`, and `click_first` actions

BrowserBridge properties:
- no site-adapter import
- no arbitrary recipe JavaScript execution surface
- no cookie export
- exact origin checks
- same-origin credential restriction
- secret-header blocklist
- bounded response text in memory
- semantic locator strategies only
- no coordinate guess-click

## Dedicated profile / ownership

`PlaywrightDriver` still uses the dedicated persistent Chrome profile and classifies common ProcessSingleton/profile-in-use failures as `PROFILE_IN_USE`.

This is code-level diagnosis only. G25/G27 still require real Windows profile/session rehearsal.

## Compatibility quarantine

The pre-R6 RunnerService still calls legacy action names. To avoid a broken intermediate main branch, R5 quarantines that translation in `legacy_t1_browser_facade.py`.

Important boundary:
- `BrowserBridge`: generic and site-agnostic
- `browser_worker.py`: compatibility import surface only, no direct site-adapter logic
- `legacy_t1_browser_facade.py`: explicitly temporary T1 compatibility translator

R6 must migrate RunnerService to AdapterPlan + BrowserResult directly and remove this facade from the execution path. The facade is not a new architecture contract.

## Body-safety boundary

`BrowserResult.safe_body_text` is bounded before leaving the browser bridge, but it is still transient response content and must not be persisted directly. R7 owns structured redaction-before-persistence. Current R5 code does not persist BrowserResult bodies.

## Safety review

PASS:
- no membership/sale-time/authorization bypass
- no cross-origin credential forwarding
- no arbitrary Cookie/Authorization injection
- no arbitrary JavaScript recipe execution
- no CAPTCHA/queue/rate-limit evasion
- no generated CSS hash dependence
- no final payment authorization automation

## Known deferrals

- R6: direct orchestrator use of AdapterPlan/BrowserResult; remove legacy facade; side-effect-aware retry/error semantics
- R7: redaction and bounded event persistence
- R10: real Windows profile ownership and session persistence evidence

## Next action

R6 — Orchestrator / Error / Side-effect / Retry migration, followed by Checkpoint C2.
