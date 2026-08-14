# CLAUDE.md — Precision Web Runner

## 0. Current phase

**DESIGN FIRST.** Do not implement application code until the user explicitly approves the design and POC scope.

The first real-world adapter is T1, but the core must remain generic enough to support a second site without rewriting the scheduler or runner.

## 1. Required behavior

Before coding:
- State assumptions explicitly.
- If multiple interpretations exist, show them rather than silently choosing.
- Prefer the simplest solution that satisfies the POC.
- Do not add speculative platform features.
- Touch only files required by the approved task.
- Convert vague requests into verifiable success criteria.

These rules intentionally bias toward caution, simplicity, and evidence.

## 2. Mandatory workflow

1. Context dump
2. User intent / primary user / success conditions
3. Blindspot sweep
4. Pre-implementation trap check
5. Design
6. User approval
7. Implementation plan
8. Tests first where practical
9. Minimal implementation
10. Spec review
11. Code/security review
12. Verification with evidence
13. Update decisions/deviations/current status

Do not skip from rough idea directly to implementation.

## 3. POC success criteria

The POC is successful only when all of the following are verified:

- A Windows runner can be armed before a target time.
- The scheduler runs outside the browser page and records target time, dispatch time, and response time.
- The runner uses a logged-in browser context without copying raw authentication cookies to a cloud backend.
- The T1 adapter can execute the allowed checkout request after the site normally permits it.
- Dynamic `checkoutNumber` is extracted from the response and used for navigation.
- The checkout page can be reached and the configured consent step can be handled.
- The flow stops at a manual final-payment checkpoint by default.
- Failure shows the exact failed step and reason.
- Duplicate execution is prevented.
- Retry is bounded.
- T1-specific IDs/endpoints are outside the core runner.

## 4. Safety and site-boundary rules

Never implement:
- membership/authorization bypass
- sale-time bypass
- CAPTCHA solving or bypass
- queue bypass
- anti-bot evasion
- rate-limit evasion
- payment/3DS/2FA bypass
- credential or cookie exfiltration

If the target server rejects the action because the user is not eligible or the action is not yet allowed, stop and report the server rejection.

Final payment authorization is manual unless the user later explicitly changes scope and the design is re-reviewed.

## 5. Architecture rules

Do not assume a hosted web app can use another site's logged-in cookies.

POC architecture:
- Responsive Control UI
- Local Windows Runner
- Browser execution bridge
- Recipe/Adapter engine
- Scheduler/clock layer
- Run state machine and structured logs

The browser action must run in an authorized browser context for the target origin.

## 6. Recipe rules

Prefer declarative, allow-listed steps. Do not support arbitrary `eval` in recipes.

Allowed step families:
- navigate
- waitUntil
- waitForSelector
- waitForText
- sameOriginFetch
- extract
- click
- check
- fill
- assert
- manualCheckpoint

A recipe may describe actions the site already allows; it must not remove or bypass restrictions.

## 7. Time/reliability rules

Do not rely on one browser `setTimeout()` for precision scheduling.

Before implementation, account for:
- local clock drift
- browser/background throttling
- PC sleep
- DNS/TLS cold start
- network jitter
- timezone
- duplicate dispatch

Log at least:
- targetAt
- armedAt
- preflightAt
- requestStartedAt
- responseReceivedAt
- completedAt/failedAt

Do not claim millisecond accuracy unless measured.

## 8. Pre-implementation trap gate

Before writing runner code, explicitly check:
- SameSite / HttpOnly / CORS
- CSRF / nonce / dynamic tokens
- browser profile/session strategy
- scheduler behavior during sleep
- selector stability
- idempotency / duplicate order risk
- bounded retry policy
- payment/3DS/manual stop point
- sensitive-data redaction
- mobile browser limitations

Unresolved critical items block implementation.

## 9. UI rules

Selected design: **Concept 02 — light dashboard**.

Desktop and mobile use one responsive design system.

On the mobile first viewport, show:
- target/task
- target time
- runner state
- primary CTA

Every visible button and form must eventually perform a real action; do not leave decorative controls in the shipped POC.

## 10. Change/deviation rule

When the implementation differs from the approved plan, update `docs/DEVIATIONS.md` before declaring completion.

Record:
- date
- original plan
- changed area
- what changed
- why
- impact
- reversibility
- follow-up verification

## 11. Testing rule

At minimum test:
- scheduler timing logic
- state transitions
- recipe validation
- response extraction
- duplicate-run prevention
- bounded retry
- timeout/failure handling
- secret/log redaction

Do not use a high-value real purchase as the first end-to-end test. Use safe/testable actions and stop before final payment.

## 12. Meta-prompting rule

For large AI tasks use:

1. Context Dump
2. Prompt Distillation
3. Result Verification

A Goal Prompt must include success and stop conditions.
An Implementation Prompt must include constraints and verification.
A Research Prompt must define source quality, scope, freshness, and verification method.

## 13. Stop conditions

Stop and ask/re-plan when:
- the design must materially change
- success requires bypassing a server restriction
- login/session handling cannot be kept safe
- the flow requires automatic payment authorization
- a critical assumption cannot be tested
- requirements conflict
- implementation drifts outside POC scope
