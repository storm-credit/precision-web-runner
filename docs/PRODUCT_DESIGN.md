# Product Design

> High-level product/UX summary. `design/UI_SPEC.md` and `design/STATE_MACHINE.md` are the detailed sources of truth.

## Product idea

Precision Web Runner is a scheduled web-action runner. A user creates a task with a target URL, target time, and site adapter variables. A Windows-local runner executes the approved flow in an already-authenticated dedicated browser context.

For the POC, only T1 Adapter 001 is in scope.

## Core user flow

1. Open local dashboard.
2. Confirm runner/browser readiness.
3. Review task and target facts.
4. Confirm target URL, amount/item, target time, adapter version, and blockers.
5. Run safe preflight/rehearsal.
6. ARM the task.
7. Runner creates immutable ArmedRunSnapshot.
8. T-30s prewarm begins.
9. Runner dispatches one allowed target action at the configured permitted target instant.
10. UI shows state, step, timing, and safe result.
11. Dynamic response data drives checkout navigation.
12. Optional pre-authorized consent/payment-UI handoff may run.
13. Runner reaches `WAITING_MANUAL`.
14. User performs final PG/payment authorization manually.

## Responsive UX

Selected direction: **Concept 02 — light dashboard**.

### Desktop

Primary layout:
- runner/browser readiness
- TEST/LIVE mode
- task/target summary
- target time/countdown
- validation blockers
- current state
- flow steps
- ARM/DISARM or relevant state CTA
- structured run log

### Mobile / narrow viewport

First viewport prioritizes:
1. runner readiness
2. TEST/LIVE mode
3. task/target
4. target time/countdown
5. current state
6. primary CTA/blocker

The UI remains responsive, but **remote LAN phone control is not required for the live POC**. Security baseline is localhost-only until secure pairing/authentication is designed.

## Domain states

```text
DRAFT
  -> TESTED
  -> ARMED
  -> PREWARMING
  -> RUNNING
  -> WAITING_MANUAL
  -> SUCCEEDED

Failure/cancel paths:
active state -> FAILED
DRAFT/TESTED/ARMED/PREWARMING -> CANCELLED where safe
```

Every transition records timestamp, reason, and safe code.

## CTA rules

- DRAFT: `테스트/검증`, `Chrome 열기`; ARM disabled with reasons
- TESTED: `ARM`
- ARMED: `ARM 해제`
- PREWARMING: `취소` only before irreversible dispatch
- RUNNING: no misleading undo/cancel once request is in flight
- WAITING_MANUAL: `브라우저에서 결제 계속`; final authorization manual
- FAILED: next action depends on side-effect status; no generic retry for ambiguous irreversible outcomes

Do not show a CTA that has no real implementation or safe meaning.

## Generalization model

A TaskDefinition contains:
- id
- name
- targetUrl
- targetAt
- timezone
- adapterId
- adapterVariables
- consentPolicy
- handoffPolicy
- mode

At ARM, it becomes an immutable ArmedRunSnapshot with:
- runId
- taskVersion
- adapterVersion
- normalized target
- normalized variables
- policy
- armedAt

A Run/Event model contains:
- runId
- state path
- target/prewarm/dispatch/response timestamps
- current step
- side-effect status
- safe result/stop reason
- structured redacted events

## Test vs LIVE

The interface must never silently promote TEST to LIVE.

LIVE ARM confirmation repeats:
- domain/task
- item/amount summary
- target time
- adapter version
- unresolved blockers
- manual payment boundary

Unknown target-site facts that affect irreversible execution block LIVE.

## POC usability success

A first-time user should quickly understand:
- what will run
- when
- which browser/device owns execution
- whether session/preflight is ready
- whether this is TEST or LIVE
- what happens automatically
- where automation stops
- why ARM is blocked if unavailable

## POC outcome semantics

`checkoutNumber` creation does not imply inventory reservation or payment success.

POC automated success means the configured manual-payment handoff was reached safely. Actual payment outcome remains outside the automated POC objective.