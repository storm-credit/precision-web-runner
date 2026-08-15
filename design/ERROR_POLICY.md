# Error Policy v1

## Goal

Every failure must answer three questions:
1. What failed?
2. Is the external side effect known, impossible, or ambiguous?
3. What is the only safe next action?

## Error classes

### CONFIG_INVALID
Examples:
- malformed URL
- target in past
- missing adapter variable
- unverified shipping type

Side effect: none.
Action: block ARM; user edits configuration.

### SESSION_INVALID
Examples:
- unauthenticated target page
- login redirect
- expected account/session marker absent

Side effect: none.
Action: block execution; manual login + fresh preflight.

### PREFLIGHT_TRANSIENT
Examples:
- safe GET/read-only network timeout
- transient 5xx on a side-effect-free check

Side effect: none by contract.
Action: bounded retry permitted if the adapter marks the step side-effect-free.

### SERVER_REJECTION
Examples:
- 400 validation failure
- 401 authentication
- 403 authorization/membership
- 409 site-defined conflict
- sale not open / item unavailable if represented as rejection

Side effect: normally no accepted checkout, but semantics belong to server response.
Action: fail closed. No bypass, no alternate endpoint, no automatic repeated attempts.

### RATE_LIMITED
Examples:
- 429
- explicit throttling response

Action: stop live automation. Never evade rate limit or rotate identity/network.

### CONTRACT_MISMATCH
Examples:
- 2xx but expected `checkoutNumber` absent
- response shape changed
- expected semantic checkout page marker missing

Side effect: may be ambiguous.
Action: no replay; inspect manually and update adapter only after evidence.

### TRANSPORT_AMBIGUOUS
Examples:
- connection reset after request send
- client timeout with no HTTP response

Side effect: **unknown** for irreversible POST.
Action: no automatic replay. Require manual inspection.

### NAVIGATION_AFTER_SIDE_EFFECT
Checkout creation is known successful but page navigation failed.

Action:
- persist safe dynamic identifier
- do not create another checkout
- allow manual navigation if normal site flow supports it

### LOCATOR_MISMATCH
Expected semantic element not found/ambiguous.

Action:
- do not click a guessed location
- stop at manual checkpoint when safe, otherwise fail

### CLOCK_DISCONTINUITY
PC sleep, clock jump, or scheduler wake outside allowed window.

Action: fail closed if timing guarantee is no longer valid.

### DUPLICATE_ATTEMPT
Second ARM/run or duplicate scheduler signal conflicts with active lease.

Action: reject duplicate locally; existing run remains authoritative.

### LOCAL_STORAGE_FAILURE
Could not persist snapshot/event needed for safe recovery.

Action: do not ARM or dispatch irreversible action.

### BROWSER_DISCONNECTED
Browser context crashed/closed.

Before target: recover only with fresh preflight.
After irreversible dispatch: treat outcome as ambiguous unless server result was already known.

## Retry matrix

| Step type | Automatic retry? | Rule |
|---|---|---|
| local validation | N/A | fix config |
| browser open/navigation before side effect | bounded | if no external side effect |
| safe read-only preflight | bounded | adapter must declare sideEffect=NONE |
| checkout/irreversible POST | **NO by POC default** | enable only if proven idempotent with evidence |
| navigation after confirmed checkout | bounded navigation retry may be allowed | must reuse same checkout identifier |
| consent locator | no blind retry/click | semantic re-query only, then manual/fail |
| payment UI open | bounded UI re-query; no payment authorization retry | final authorization manual |

## Ambiguity rule

When uncertain whether an irreversible request succeeded, choose **do not replay**.

This is stricter than maximizing speed, because duplicate orders are worse than a visible manual recovery path.

## User-facing error shape

```text
code: stable machine-readable code
stage: PRECHECK | PREWARM | DISPATCH | PARSE | NAVIGATE | CONSENT | HANDOFF
message: concise human explanation
sideEffect: NONE | CONFIRMED | AMBIGUOUS
nextAction: explicit safe action
httpStatus?: safe status only
runId
at
```

Do not expose cookies, tokens, raw response bodies, PII, or payment data.

## Retry configuration invariant

A generic `max_retries` field must never automatically apply to all steps. Retry policy is per-step and constrained by side-effect classification.

## Live POC decision

For T1 checkout creation, automatic POST replay is **disabled** until target-side idempotency is independently proven. Transport ambiguity therefore stops the run and requires manual inspection.