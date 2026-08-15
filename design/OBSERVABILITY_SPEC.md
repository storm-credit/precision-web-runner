# Observability Specification v1

## Goal

Logs must be detailed enough to reconstruct *what happened and when* without becoming a dump of account/session/payment data.

## Event schema

```text
RunEvent {
  eventId,
  runId,
  sequence,
  at,
  state,
  stage,
  stepId?,
  level,
  code,
  message,
  sideEffect: NONE | CONFIRMED | AMBIGUOUS,
  safeDetail
}
```

## Required event families

### Lifecycle
- RUNNER_STARTED
- BROWSER_OPENED
- TASK_SAVED
- RUN_ARMED
- RUN_DISARMED
- RUN_FAILED
- MANUAL_CHECKPOINT_REACHED

### Timing
- PREWARM_STARTED
- PREFLIGHT_COMPLETED
- SCHEDULER_TARGET_DUE
- REQUEST_STARTED
- RESPONSE_RECEIVED
- CHECKOUT_PAGE_READY

### Safety
- DUPLICATE_BLOCKED
- LATE_DISPATCH_BLOCKED
- SESSION_INVALID
- CONTRACT_MISMATCH
- TRANSPORT_AMBIGUOUS
- SECRET_REDACTED if diagnostic instrumentation detects attempted unsafe field logging

## Timing detail

Safe fields may include:
- targetAt
- requestStartedAt
- responseReceivedAt
- dispatchLatenessMs
- responseLatencyMs
- navigationLatencyMs

## HTTP detail

Safe by default:
- method
- endpoint identifier/name, not necessarily full query
- HTTP status
- response byte length
- adapter semantic classification

Forbidden by default:
- request/response full body
- Cookie / Set-Cookie
- Authorization
- CSRF/nonce
- session IDs
- account PII

A local diagnostic mode, if ever added, must still redact secrets and is out of POC scope.

## Dynamic checkout identifier

A checkoutNumber may be logged locally only if current evidence indicates it is not an authentication secret. It must never be used as proof of inventory reservation or payment completion.

## Redaction

Redaction runs **before persistence**.

Minimum denylist keys/patterns:
- cookie
- set-cookie
- authorization
- csrf
- token
- session
- email
- phone
- mobile
- address
- card
- otp
- password

Denylist is not sufficient alone: structured logging should only admit known safe fields.

## Retention

POC local retention may be simple, but logs must be bounded.

Recommended baseline:
- keep recent run summaries
- rotate/truncate oversized event files
- never preserve raw browser traces automatically

## UI rendering

The UI shows:
- latest state
- current step
- countdown/timing
- exact safe failure code
- safe next action
- recent structured events

The UI does not show raw network dumps.

## Reproducibility

A run report should be constructible from persisted safe events:
- configuration snapshot identity/version
- adapter version
- target time
- state path
- timing metrics
- known checkout identifier if safe
- failure/stop reason

## Completion evidence

Before live approval, inspect at least one rehearsal log and confirm no cookie, token, email, phone, address, or payment field is present.