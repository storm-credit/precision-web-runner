# CLAUDE.md — Precision Web Runner

## 0. Current phase

**POC IMPLEMENTATION APPROVED.** The user explicitly approved continuing implementation on 2026-08-15.

Implement only the POC required for the 2026-08-17 live rehearsal/use. Do not expand into the general platform until the POC exit report.

The first real-world adapter is T1, but the core must remain generic enough to support a second site without rewriting the scheduler or run state machine.

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

Implementation is now permitted, but steps 8-13 remain mandatory.

## 3. POC success criteria

The POC is successful only when all of the following are verified:

- A Windows runner can be armed before a target time.
- The scheduler runs outside the browser page and records target/dispatch timing.
- The runner uses a dedicated logged-in browser context without copying raw authentication cookies to a cloud backend.
- The T1 adapter can execute the allowed checkout request after the site normally permits it.
- Dynamic `checkoutNumber` is extracted from the response and used for navigation.
- The checkout page can be reached and configured consent can be handled.
- Final PG/payment authorization remains manual.
- Failure shows the exact failed step and reason.
- Duplicate execution is prevented.
- Retry is bounded.
- T1-specific IDs/endpoints remain outside generic timing/state modules.

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

Opening a payment window may be automated only after explicit local configuration; actual payment authorization remains manual.

## 5. POC architecture rules

Current implementation target:
- Python 3.11+ local process
- responsive localhost dashboard
- scheduler running in Python, not page JavaScript
- Playwright persistent Chrome context with a dedicated local profile
- browser-context same-origin fetch
- T1 adapter separated from generic task/timing/state code
- local structured logs only

Do not add a cloud backend for the POC.

## 6. Browser/session rules

- Use a dedicated Precision Runner Chrome profile.
- The user logs in manually once.
- Do not scrape, export, or persist raw cookies.
- Execute T1 fetch calls from the T1 page context with `credentials: same-origin`.
- Do not attach to the user's ordinary Chrome profile for the POC.

## 7. Recipe/adapter rules

Prefer declarative/typed adapter data. Do not support arbitrary stored `eval` recipes.

Allowed conceptual step families:
- navigate
- waitUntil
- preflight
- sameOriginFetch
- extract
- click/check
- manualCheckpoint

T1 adapter may describe actions the site already allows; it must not remove restrictions.

## 8. Time/reliability rules

Do not rely on one browser `setTimeout()` for precision scheduling.

Account for:
- local clock drift
- browser/background throttling
- PC sleep
- DNS/TLS cold start
- network jitter
- timezone
- duplicate dispatch

Use a monotonic deadline once armed and prewarm the browser before dispatch.

Do not claim millisecond accuracy unless measured on the user's Windows machine.

## 9. Pre-implementation / live-run trap gate

Before a live run explicitly check:
- browser profile is logged in
- target URL/item/amount are correct
- `shippingType` is confirmed
- target time/timezone are correct
- Windows is time-synchronized
- sleep is disabled for the live window
- preflight passes
- safe rehearsal has passed
- retry remains bounded
- final payment remains manual

Unresolved critical items block ARM.

## 10. UI rules

Selected design: **Concept 02 — light dashboard**.

Desktop and mobile use one responsive design system, but the live execution engine is Windows-local for the POC.

On the first viewport show:
- target/task
- target time
- runner state/countdown
- primary ARM/cancel actions

Every visible button/form must perform a real action.

## 11. Change/deviation rule

When implementation differs from the approved plan, update `docs/DEVIATIONS.md` before completion.

Record:
- date
- original plan
- changed area
- what changed
- why
- impact
- reversibility
- follow-up verification

## 12. Testing rule

At minimum test:
- task validation
- target-time timing helpers
- response extraction
- non-retryable vs retryable HTTP classification
- missing checkoutNumber fail-closed behavior
- syntax/imports
- local dashboard status route

Before live use also perform manual Windows/Chrome rehearsal.

Do not use the 500,000 KRW target as the first end-to-end test.

## 13. Meta-prompting rule

For large AI tasks use:

1. Context Dump
2. Prompt Distillation
3. Result Verification

A Goal Prompt includes success and stop conditions.
An Implementation Prompt includes constraints and verification.
A Research Prompt defines source quality, scope, freshness, and verification method.

## 14. Stop conditions

Stop/re-plan when:
- success requires bypassing a server restriction
- login/session handling cannot remain local and safe
- the flow requires automatic final payment authorization
- a critical assumption cannot be tested
- implementation drifts outside POC scope
- the T1 API/page contract changes materially

## 15. Current implementation caveats

- Signature Edition `inventoryItemId=3454` and amount `500000 KRW` were observed earlier.
- The direct checkout contract was validated from another normal item.
- Signature Edition `shippingType` has not yet been independently verified, so live ARM must stay blocked until the user confirms it.
- POC timing accuracy must be measured on the user's Windows PC; container/unit tests do not prove live timing accuracy.
