# POC Scope

## Goal

Prove one narrow capability before building a general automation platform:

> From a Windows PC that already has a valid logged-in browser session, arm a task in advance, dispatch an allowed web action at the configured target time, carry dynamic response data into the next browser step, and stop safely before final payment.

T1 Membership is the first validation adapter, not the product definition.

## In scope

- Windows local runner
- Responsive web UI usable from desktop and mobile
- Mobile as control/monitor surface for the PC runner
- One scheduled task at a time
- One T1 adapter
- Preflight / arm / cancel / test-run controls
- Local task + run logs
- Browser-context same-origin request execution
- Dynamic response extraction
- Checkout-page navigation
- Configured consent step
- Manual final-payment checkpoint
- Failure reason and timing telemetry
- Duplicate-run prevention
- Bounded retry

## Out of scope

- Arbitrary URL auto-understanding
- AI-generated recipes in production
- Cloud execution
- SaaS user accounts
- Multi-user / team features
- Mobile-only precision execution
- Browser farm
- CAPTCHA/queue bypass
- Anti-bot evasion
- Authorization/membership/sale-time bypass
- Fully automatic payment authorization
- Recipe marketplace
- Complex agent-memory infrastructure

## Definition of Done

POC PASS requires evidence for all items:

1. Runner is armed before target time.
2. Preflight confirms browser connection and authenticated target page/session.
3. Scheduler records the intended target and actual dispatch timestamps.
4. T1 adapter sends the allowed checkout action after the server normally permits it.
5. Response returns a dynamic checkout identifier.
6. Runner extracts it and navigates to the corresponding checkout page.
7. Configured consent can be completed.
8. Runner stops at manual final-payment checkpoint.
9. Failure shows exact step, HTTP/status information where safe, and stop reason.
10. A second click / duplicate scheduler event cannot create a second simultaneous run.
11. Retries are bounded and visible.
12. No raw login cookie or personal checkout payload is stored in a cloud backend.
13. T1 IDs and paths live in the T1 adapter rather than core modules.

## POC exit rule

Once the above passes, stop feature work and write a POC report.

Only then decide whether to continue to MVP.

## MVP gate after POC

The first MVP proof is not more T1 features. It is adding a structurally different second site **without rewriting the scheduler/state machine**. If that requires major core rewrites, the abstraction is not yet validated.
