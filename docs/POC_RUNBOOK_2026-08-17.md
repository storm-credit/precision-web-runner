# POC Runbook — T1 2026-08-17 12:00 KST

> **CURRENT STATUS: REHEARSAL PLAN ONLY / LIVE NO-GO.**
>
> Existing runtime is Architecture Spike evidence. Do not treat this runbook as live approval until Deep Design is approved, implementation is reconciled, and `verification/POC_GO_NO_GO.md` reaches GO.

## Purpose

Define the practical Windows rehearsal/live procedure for the narrow POC while preserving fail-closed behavior.

The intended automated boundary is checkout/payment handoff. The runner does not bypass T1 eligibility or automate final payment authorization.

## One-time rehearsal setup

After implementation reconciliation is approved:

1. Install supported Python and Google Chrome.
2. Clone/pull the approved `main` revision.
3. Run the documented setup/run scripts.
4. Dashboard should open on localhost only.
5. Open the dedicated Precision Runner Chrome profile.
6. Sign in to T1 manually inside that Chrome window.
7. Keep this dedicated profile for the POC.

The final exact commands must be revalidated after the existing Architecture Spike is reconciled against Deep Design.

## Dedicated Chrome profile

The runner must not copy cookies/tokens into a backend. The dedicated browser profile owns the login session locally and one runner instance owns that profile.

## Signature configuration evidence

Known:
- target URL: `https://t1.fan/shop/products/525`
- observed inventory item ID: `3454`
- quantity intent: `1`
- observed amount: `500000 KRW`
- target: `2026-08-17 12:00:00 KST`

**LIVE BLOCKER:** exact Signature Edition `shippingType` must be independently verified from the exact target flow.

Do not infer:
- shippingType from the 49,000 KRW test item
- paymentOptionId is required by direct checkout merely because it appeared in cart
- checkout creation guarantees inventory reservation
- checkout handoff means payment success

## Rehearsal — 15/16 Aug

### A. Session/preflight rehearsal

1. Launch the dedicated Chrome profile.
2. Log in manually if needed.
3. Run the safe preflight.
4. Require a PASS with no irreversible checkout call.
5. Restart runner/browser and verify login persistence.
6. Verify a logged-out profile is detected as SESSION_INVALID.

### B. Safe checkout-flow rehearsal

Use only a normal product/flow whose exact request fields you have independently verified and for which you intentionally accept checkout creation. Do not use the 500,000 KRW target as the first end-to-end test.

Verify:
1. exact URL/item/amount/shipping type
2. one checkout request only
3. dynamic current-run `checkoutNumber`
4. navigation to that exact checkout
5. optional consent behavior only if pre-authorized
6. manual payment handoff
7. no final PG/card/OTP/3DS authorization by runner
8. no sensitive data in logs

Do not complete payment during a rehearsal unless you independently intend to buy that rehearsal item.

### C. Scheduler rehearsal

Run at least 5 safe scheduled trials.

For each:
1. choose a safe target several minutes ahead
2. ARM with immutable snapshot
3. observe prewarm
4. observe target dispatch
5. collect:
   - targetAt
   - schedulerWakeAt
   - requestStartedAt
   - responseReceivedAt
   - dispatchLatenessMs
6. verify no early intentional dispatch

Use the measured results to choose/review final `maxLatenessMs`.

## Failure rehearsals

Before LIVE, demonstrate:
- duplicate ARM blocked
- server 4xx stops with no bypass/replay
- missing checkoutNumber fails closed
- navigation failure after confirmed checkout does not create a second checkout
- ambiguous transport does not automatically replay checkout
- browser/profile duplicate ownership is blocked
- logs remain redacted

## Windows live prerequisites

All must PASS in `verification/POC_GO_NO_GO.md`:
- Windows clock synchronized
- sleep/hibernate disabled for the live window
- power/network stable
- no VPN/proxy change planned
- dedicated Chrome profile logged in
- preflight passes
- target values reviewed
- exact Signature `shippingType` confirmed
- adapter/current site contract still valid
- timing rehearsal complete
- no duplicate runner instance
- dashboard bound only to approved interface (localhost baseline)

## Suggested live timeline — only after GO

### 11:40-11:50
- start approved runner revision
- open dedicated Chrome profile
- verify exact LIVE task snapshot
- run fresh preflight

### By 11:55
- review TEST/LIVE badge
- review item/amount/time/adapter version
- ARM once
- leave PC awake and runner visible

### T-30s
- prewarm only
- no irreversible checkout before target

### 12:00:00 KST
- dispatch one allowed checkout action at/after the published permitted target instant
- if server rejects, stop
- if transport outcome is ambiguous, stop for manual inspection
- do not automatically replay irreversible checkout

### Success path
- parse current-run checkoutNumber
- navigate to exact checkout route
- optional exact pre-authorized consent step
- optional normal payment UI opening
- state becomes `WAITING_MANUAL`
- user performs final payment authorization manually

## Retry policy

Per-step policy, not a global retry switch:

- side-effect-free preflight: bounded retry may be allowed by design
- irreversible checkout creation: **automatic replay OFF for live POC**
- ambiguous irreversible transport: no replay; manual inspection
- navigation after known checkout: navigation may be retried while reusing the same checkout identifier, never by creating a second checkout

## Emergency fallback

Keep the controlled browser visible.

If the runner fails:
- read side-effect status and safe next action
- if checkout is known created, reuse/manual-navigate that checkout only when normal site behavior supports it
- if outcome is ambiguous, inspect manually
- do not launch multiple scripts/runner instances
- do not compensate with repeated requests or restriction bypasses

## Evidence to collect

Safe local evidence:
- runId
- adapter version
- target timestamp
- dispatch timestamp/lateness
- response status/classification
- current-run checkoutNumber only if still considered safe local metadata
- checkout navigation result
- manual checkpoint timestamp
- exact failure code if any

Never share/commit:
- cookies
- session IDs/tokens
- Authorization/CSRF
- full checkout JSON/HTML
- name/email/phone/address
- card/payment/OTP/2FA data

## Final rule

The day-of runbook does not override the Go/No-Go gate. Any mandatory UNKNOWN/BLOCKED item means NO-GO for automation.