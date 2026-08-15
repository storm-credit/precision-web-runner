# POC Acceptance Matrix v1

This matrix defines what must be demonstrated before claiming the POC works. A row is PASS only with reproducible evidence.

| ID | Scenario | Given | When | Expected | Evidence |
|---|---|---|---|---|---|
| A01 | Task validation | invalid/missing required field | save/ARM | blocked with exact reason | UI/API result |
| A02 | Past target | target time already passed | ARM | blocked | event/error code |
| A03 | Unknown live field | Signature shippingType unverified | LIVE ARM | blocked | blocker shown |
| A04 | Dedicated profile | runner starts | open browser | dedicated profile used; no cookie export | visible profile + code/config review |
| A05 | Logged-out session | target profile logged out | preflight | SESSION_INVALID, no ARM | event/log |
| A06 | Logged-in preflight | valid session | preflight | PASS without irreversible checkout | event + network observation |
| A07 | Immutable ARM snapshot | task armed | user tries edit | active snapshot unchanged/edit blocked | API/UI result |
| A08 | Duplicate ARM | one run active | second ARM | rejected locally | event `DUPLICATE_BLOCKED` |
| A09 | T-30 prewarm | scheduled run | prewarm deadline | browser warm + safe preflight | timestamps |
| A10 | Target dispatch | armed, awake PC | target instant | one irreversible dispatch starts | request timestamp |
| A11 | Late wake | target missed beyond policy | scheduler wakes | no checkout dispatch | `LATE_DISPATCH_BLOCKED` |
| A12 | Server 4xx | target rejects | checkout step | fail closed, no bypass/replay | HTTP status + single attempt |
| A13 | 429 | rate limited | checkout/preflight | no evasion/repeated hammering | event + request count |
| A14 | Transport ambiguity | irreversible request outcome unknown | timeout/reset | no automatic replay | one request + ambiguous error |
| A15 | Success parse | observed success response | adapter parse | current-run checkoutNumber extracted | unit/live evidence |
| A16 | Missing checkoutNumber | 2xx unexpected body | parse | CONTRACT_MISMATCH, no guessed ID | unit test |
| A17 | Checkout navigation | checkoutNumber known | navigate | exact current-run checkout route opens | visible URL/event |
| A18 | Navigation failure after checkout | checkout created | navigation fails | no second checkout; ID retained | event/request count |
| A19 | Consent OFF | checkout page ready | handoff | no consent auto-click | visible state |
| A20 | Consent ON valid | user pre-authorized, exact locator | consent step | exact checkbox handled | visible state/event |
| A21 | Consent locator mismatch | expected text/role absent | consent step | no coordinate guess; manual/fail | event |
| A22 | Payment handoff | checkout ready | configured open payment UI | payment surface opens; state WAITING_MANUAL | visible browser/event |
| A23 | Final authorization boundary | WAITING_MANUAL | PG requires approval | runner does not approve/pay | manual observation |
| A24 | Sensitive logging | rehearsal includes account session | inspect logs | no cookies/tokens/PII/payment data | log inspection |
| A25 | Browser profile lock | one runner owns profile | second starts | second blocked | error/event |
| A26 | Browser crash before target | safe margin remains | browser closes | recovery requires fresh preflight or fails per policy | event |
| A27 | Browser crash after dispatch | outcome unknown | browser closes | no automatic replay | event/request count |
| A28 | Process restart in ambiguous RUNNING | persisted active run | service restarts | recovery required; no silent replay | state/event |
| A29 | Mobile/responsive view | narrow viewport | open dashboard | target/time/state/CTA visible | screenshot/manual review |
| A30 | Real CTA | any visible control | activate | real action or explicit disabled reason | UI integration check |
| A31 | Adapter separation | inspect core | T1 adapter removed conceptually | core has no T1 IDs/endpoint assumptions | code/design review |
| A32 | Timing measurement | >=5 safe scheduled rehearsals | summarize | median/max dispatch lateness recorded | rehearsal report |

## Mandatory live subset

Before 2026-08-17 LIVE ARM, at minimum PASS:
A02, A03, A04, A05/A06 as appropriate, A08, A09, A10 via safe rehearsal, A12, A14, A15, A16, A17, A18, A22, A23, A24, A25, A29, A30, A32.

## Evidence rule

"Code appears to do this" is not enough for browser/timing/live rows. Use the strongest available evidence:
1. observed live/safe rehearsal behavior
2. automated integration test
3. unit test for pure logic
4. code review only when runtime demonstration is impossible

## Failure rule

A failed mandatory row blocks LIVE. It may not be waived by optimistic inference. Unknown counts as not passed.