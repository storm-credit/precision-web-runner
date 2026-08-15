# Decisions & Interview

This file captures explicit user intent, accepted design defaults, and the few facts that still require evidence before LIVE use.

## User intent

The user wants a practical tool that can:
- prepare a timed web action in advance
- execute automatically at a target time
- use an already-authenticated local browser session
- present a clear responsive web/mobile design
- start with T1 but later support other target URLs through site adapters/recipes

Immediate objective: **narrow POC**, not SaaS/general platform.

The user also explicitly clarified on 2026-08-15:
- **deep design and harness first**
- coding comes last

Therefore current runtime code is Architecture Spike evidence and is frozen until design approval.

## Primary user

POC primary user:
- one trusted repository owner/user
- Windows PC
- local browser

No multi-user/team/account/billing design in POC.

## Product decisions

- Repository: `storm-credit/precision-web-runner`
- Product working name: Precision Web Runner / Precision Runner
- First adapter: T1 Membership
- UI: Concept 02 light responsive dashboard
- T1-specific values stay outside generic core contracts
- future URLs require Adapter/Recipe contracts; URL alone is not automation
- server-side restrictions are not bypassed
- final payment authorization is manual
- unknown target facts block LIVE rather than being guessed

## Resolved architecture decisions

### D1. Browser session strategy — RESOLVED
Use a **dedicated persistent Chrome profile** for the POC.

Why:
- keeps authentication local
- isolates normal browsing
- repeatable ownership/lifecycle
- no cookie export required

### D2. Control-plane exposure — RESOLVED
Live POC dashboard defaults to **localhost-only**.

Responsive mobile/narrow layout remains required, but remote phone/LAN control is deferred until pairing/authentication/CSRF protection is separately designed.

### D3. Consent behavior — RESOLVED AS POLICY
Auto-consent may exist as an optional configuration only when the user has already reviewed and accepted the applicable terms.

Rules:
- default OFF
- immutable once armed
- exact semantic locator required
- locator mismatch -> manual/fail; never coordinate guess
- final payment remains manual

### D4. Timing policy — RESOLVED BASELINE
Use the published permitted target instant with synchronized Windows clock and monotonic scheduling after ARM.

Do not intentionally dispatch before the allowed opening time to compensate for latency.
Do not add timing offsets until rehearsal evidence justifies a reviewed change.

### D5. Irreversible retry policy — RESOLVED BASELINE
Automatic replay of checkout creation is **OFF** for live POC unless site-specific idempotency is independently proven.

Read-only preflight can use bounded retry when declared side-effect-free.

### D6. Existing code status — RESOLVED
Existing `src/`, `tests/`, and `scripts/` are an Architecture Spike. They are not the design source of truth and will later be reconciled as KEEP / CHANGE / DELETE.

## POC assumptions accepted for design

1. Windows PC can remain powered on and awake during an armed live window.
2. User can log into T1 manually before ARM.
3. One live task/run is active at a time.
4. Local persistence is acceptable for non-secret task/run metadata.
5. Payment/PG final authorization remains user-controlled.

These assumptions still require rehearsal where runtime behavior matters.

## Evidence still required before LIVE

### E1. Signature shippingType
The exact Signature Edition `shippingType` remains UNKNOWN.

This is a LIVE ARM blocker.

### E2. Windows session persistence
Dedicated Chrome login persistence/restart behavior must be observed on the user's Windows PC.

### E3. Timing variance
Actual scheduler/dispatch lateness must be measured over safe rehearsals before selecting final `maxLatenessMs`.

### E4. Target contract freshness
T1 flow must be rechecked near rehearsal/live time for material API/page changes.

## Question-induction rule

Do not ask the user generic interview questions merely because a template contains them.

Ask only when an unresolved answer would materially change:
- architecture
- security
- irreversible behavior
- live readiness
- UX semantics

For evidence questions that can be answered by a safe rehearsal or repository inspection, perform/read that evidence before asking the user to repeat information.

## Design-approval rule

Implementation reconciliation may begin only after:
- deep design review finds no unresolved BLOCKER
- the user approves the baseline

LIVE use additionally requires `verification/POC_GO_NO_GO.md` PASS.