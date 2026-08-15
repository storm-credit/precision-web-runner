# Checkpoint C2 — Adapter / Browser / Orchestrator Review

## Verdict

**C2: PASS — R7 ELIGIBLE AFTER R6 MERGE.**

C2 reviews R4-R6 together. It does not approve LIVE use.

## Reviewed slices

- R4 — Adapter Contract + T1 Adapter Migration
- R5 — Generic BrowserBridge + Typed BrowserResult
- R6 — Orchestrator / Error / Side-effect / Retry Migration

Evidence:
- `verification/R4_ADAPTER_REVIEW.md`
- `verification/R5_BROWSER_BRIDGE_REVIEW.md`
- `verification/R6_ORCHESTRATOR_REVIEW.md`

## Cross-slice invariants

| Invariant | Result | Evidence |
|---|---|---|
| Site facts live behind Adapter v1 | PASS | R4 T1Adapter plans/schema/evidence |
| Signature shippingType remains UNKNOWN unless independently verified | PASS | R4 evidence tests |
| Browser layer has no T1 request construction | PASS | R5 source test |
| Browser same-origin credential guard is enforced | PASS | R5 tests |
| Cookie/Authorization injection is blocked | PASS | R5 tests |
| Browser results are typed and response body bounded | PASS | R5 BrowserResult tests |
| Semantic locator strategy replaces CSS-hash dependence | PASS | R4/R5 tests |
| RunnerService consumes AdapterPlan + BrowserResult | PASS | R6 implementation/tests |
| RunnerService contains no site endpoint/payload/locator literals | PASS | R6 source test |
| irreversible create-checkout has no generic retry loop | PASS | R6 source/behavior tests |
| transport ambiguity preserves active run and forbids replay | PASS | R6 test |
| server rejection/rate limit does not trigger bypass/replay | PASS | R6 tests |
| confirmed checkout nav failure preserves current-run dynamic ID | PASS | R6 + LocalStore safe_variables tests |
| recovery navigation reuses existing checkout only | PASS | R6 test |
| duplicate execution signal does not produce second dispatch | PASS | R6 test |
| final automation state is WAITING_MANUAL, not paid | PASS | R6 test |

## Reviewer lenses

### Architecture
PASS.

Dependency direction now matches the approved design:

```text
Core Snapshot
  -> Site Adapter Plan
     -> Generic BrowserBridge
        -> Typed BrowserResult
     -> Adapter semantic parse
  -> Core side-effect/error/state policy
```

No browser-to-adapter back-reference remains on the forward execution path.

### Side-effect safety
PASS.

The irreversible step is one-shot by design. Ambiguous outcome is a recovery state, not a retry signal. Confirmed checkout navigation failure is separated from create-checkout failure and retains the known dynamic identifier.

### Security
PASS FOR IMPLEMENTATION FOUNDATION.

Exact origin, same-origin credentials, forbidden secret headers, no cookie export, no arbitrary JS recipe, and manual final-payment boundary remain intact.

### Target evidence discipline
PASS.

Observed facts, inferred values, and unknown values remain distinct. No normal-item shipping observation is silently promoted to the Signature product.

### Failure semantics
PASS FOR R6.

Core now owns stable ErrorInfo categories and side-effect status; adapter semantic codes cannot grant retry permission.

### Testability
PASS.

Network/browser behavior is covered through BrowserResult fakes and injected seams without real T1 calls.

## Findings

### BLOCKER
None.

### MAJOR
None unresolved.

### MINOR / deferred
1. `TaskConfig` and old dashboard `task.json` remain temporary compatibility representations until R8/R9.
2. Legacy `Event` JSONL logging remains until R7; no raw BrowserResult body is persisted, but structured redaction must become explicit next.
3. `browser_worker.py` compatibility alias can be removed after callers fully use BrowserBridge naming; it has no site logic.
4. Adapter `legacy_variables()` is a POC migration seam for the existing task form. General recipe configuration remains post-POC.
5. Real Chrome profile/session behavior still requires R10 Windows evidence.

## Scope check

No second adapter, arbitrary URL AI, cloud runner, LAN/mobile remote control, CAPTCHA/queue bypass, rate-limit evasion, automatic final-payment authorization, or generalized retry system was introduced.

## Decision

R4-R6 integration is stable enough to proceed to **R7 — Typed / Redacted / Bounded Observability**.

R7 must not persist BrowserResult `safe_body_text` directly. Only allow-listed structured fields may reach disk.

LIVE remains NO-GO independently of C2.
