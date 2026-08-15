# System Design v1

## 1. System goal

Precision Runner executes a previously configured, authorized web action flow at a target time from a user-controlled Windows machine and an already-authenticated browser context, then stops at a defined manual checkpoint.

The POC proves one T1 flow. The core architecture must not depend on T1 identifiers or copy target-site authentication into a cloud service.

## 2. Trust boundaries

```text
User
  |
  v
Local Dashboard (localhost / trusted LAN only)
  |
  v
Runner Service (Windows process)
  |         \
  |          -> Local task/run store (redacted)
  v
Browser Bridge / Persistent Chrome
  |
  v
Target Origin (T1 Adapter 001)
  |
  v
External PG handoff [manual authorization boundary]
```

Trust rules:
- Browser session secrets stay inside the browser profile.
- Runner may command browser actions but does not export raw cookies.
- Dashboard is a controller, not an authority for target-site eligibility.
- Target server is authoritative for membership, time, stock, and validation.
- PG is outside automatic authorization scope.

## 3. Control plane vs execution plane

### Control plane
Owns configuration and visibility:
- task settings
- target time
- adapter variables
- test/live mode
- ARM / DISARM
- state and logs

It must not perform precision scheduling itself.

### Execution plane
Owns irreversible execution:
- task snapshot at ARM
- scheduler
- preflight
- duplicate-run lease
- browser bridge commands
- adapter execution
- state transitions
- redacted event log

## 4. Configuration snapshot rule

When a task is ARMED, the runner creates an immutable execution snapshot containing:
- task identity/version
- adapter version
- target URL
- target time/timezone
- validated adapter variables
- consent/payment-handoff options
- execution policy

Editing the task after ARM must not mutate the armed run. User must disarm, edit, and re-arm.

## 5. Authority model

### Runner authority
The runner may decide:
- whether local preconditions pass
- when to dispatch relative to configured target
- whether a response is structurally usable
- whether to stop/retry according to policy

### Target-site authority
The target server decides:
- authentication validity
- authorization/membership
- sale opening
- stock/availability
- request validity
- checkout acceptance

A target-site rejection is not overridden by DOM manipulation or alternate endpoints.

## 6. Execution invariant

For one armed run there is at most one active irreversible checkout-dispatch lease.

The runner must never create a second checkout merely because the first result is ambiguous.

## 7. Data model

### TaskDefinition
Editable user intent.

Fields:
- id
- name
- targetUrl
- targetAt
- timezone
- adapterId
- adapterVariables
- consentPolicy
- handoffPolicy
- mode: TEST | LIVE

### ArmedRunSnapshot
Immutable validated copy created at ARM.

Fields:
- runId
- taskVersion
- adapterVersion
- normalized target
- normalized variables
- policy
- armedAt

### RunState
Current finite-state-machine state + reason.

### RunEvent
Structured redacted telemetry. Raw cookies, tokens, full response bodies, personal checkout data, and payment secrets are forbidden.

## 8. POC storage

Local filesystem is sufficient.

Persist:
- TaskDefinition
- non-secret ArmedRunSnapshot
- state/event metadata
- timing measurements
- redacted error summaries

Do not persist:
- browser cookie database copies outside Chrome profile
- Authorization/CSRF tokens
- full checkout JSON
- card/PG credentials

## 9. Browser model

POC default: dedicated persistent Chrome profile controlled through Playwright/CDP-compatible browser automation.

Reasons:
- reproducible session ownership
- isolation from everyday browsing
- cookies remain inside browser profile
- visible manual login and PG handoff

The browser remains a replaceable adapter behind BrowserBridge.

## 10. Site Adapter model

Core invokes an Adapter interface; adapter owns site semantics.

Core must not know:
- endpoint path
- item IDs
- payload shape
- selector/text strategy
- response field names

Core knows only generic operations and typed results.

## 11. Precision model

The POC defines precision as **measured dispatch behavior**, not a promise of simultaneous arrival at server opening.

- wall clock establishes target instant
- monotonic time protects wait calculations
- T-30s prewarm reduces cold-start cost
- dispatch, response and lateness are separately recorded
- PC sleep/wake discontinuity is detected
- late-dispatch policy fails closed beyond the configured tolerance

## 12. Manual boundary

Automatic flow may prepare the checkout and optionally open the payment UI after pre-authorized consent configuration.

It must stop before:
- card confirmation
- simple-payment final approval
- 3DS
- OTP/2FA
- any equivalent final financial authorization

## 13. Mobile boundary

POC mobile is a control/monitor surface for the Windows runner.

Mobile does not own precision execution because of background suspension and browser-extension variability.

## 14. Extensibility test

The architecture is considered generalizable only if a second structurally different site can be added later by implementing Adapter v1 without rewriting:
- scheduler
- state machine
- run lock
- event model
- browser bridge contract

If those must change materially, the abstraction failed and must be revised before MVP.