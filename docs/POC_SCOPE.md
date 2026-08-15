# POC Scope

## Goal

Prove one narrow capability before building a general automation platform:

> From a Windows PC with a dedicated valid logged-in browser session, arm a task in advance, dispatch one allowed web action at the configured permitted target time, carry dynamic response data into the next browser step, and stop safely before final payment authorization.

T1 Membership is the first validation adapter, not the product definition.

## In scope

- Windows local runner
- responsive Concept 02 UI for desktop/narrow/mobile layouts
- localhost control surface for live POC
- one scheduled live task at a time
- one T1 adapter
- preflight / ARM / DISARM / test controls
- immutable ArmedRunSnapshot
- local task + redacted run logs
- browser-context same-origin request execution
- dynamic response extraction
- checkout-page navigation
- optional pre-authorized consent handling
- optional normal payment-UI handoff
- **manual final payment authorization**
- exact failure stage/reason/side-effect status
- duplicate-run prevention
- per-step bounded retry only where side-effect policy permits it
- timing telemetry and rehearsal measurements

## Explicit live-POC boundaries

- Dashboard binds to localhost by default.
- Remote LAN/mobile control is deferred until pairing/authentication/CSRF design exists.
- Mobile/narrow responsiveness remains required for future control-plane reuse and UI validation.
- Automatic replay of irreversible checkout creation is disabled unless idempotency is independently proven.

## Out of scope

- arbitrary URL auto-understanding
- AI-generated production recipes
- cloud execution
- SaaS user accounts
- multi-user / team features
- mobile-only precision execution
- remote LAN control without security design
- browser farm
- CAPTCHA/queue bypass
- anti-bot evasion
- authorization/membership/sale-time bypass
- rate-limit evasion
- fully automatic payment authorization
- recipe marketplace
- complex external agent-memory infrastructure

## Definition of Done

POC PASS requires evidence that:

1. Runner is armed before target time using an immutable validated snapshot.
2. Dedicated Chrome profile/session ownership and persistence are verified.
3. Preflight confirms expected origin/session without irreversible checkout.
4. Scheduler records target, wake, dispatch, and response timestamps.
5. One allowed T1 checkout action is dispatched at/after the published permitted target instant.
6. Server rejection fails closed without bypass/replay.
7. Ambiguous irreversible transport outcome does not automatically replay.
8. Success response yields a current-run dynamic checkout identifier.
9. Runner navigates using that same identifier and does not guess/reuse an old one.
10. Optional configured consent behavior is exact and fail-closed.
11. Runner reaches the manual payment handoff; final PG/3DS/OTP/payment authorization remains manual.
12. Duplicate ARM/run is blocked.
13. Logs show exact state/stage/timing while containing no raw auth secrets, PII dumps, or payment data.
14. T1-specific IDs/endpoints remain outside generic scheduler/state/lock contracts.
15. Required rows in `verification/ACCEPTANCE_MATRIX.md` pass.
16. `verification/POC_GO_NO_GO.md` reaches GO before live ARM.

## Design completion before coding reconciliation

Runtime code already exists as Architecture Spike evidence. No further feature implementation/reconciliation starts until:
- `design/*` is reviewed
- no unresolved BLOCKER remains
- user approves the deep-design baseline

## POC exit rule

After the POC evidence is collected, stop feature work and write a result report.

Classify:
- STOP
- REWORK
- CONTINUE TO MVP

Do not automatically expand into general-platform features.

## MVP gate after POC

The first abstraction test is a structurally different second site Adapter v1 without rewriting the generic scheduler, state machine, execution lease, BrowserBridge contract, or event model. If major core rewrites are required, the abstraction is not validated.