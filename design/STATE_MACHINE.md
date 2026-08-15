# Run State Machine v1

## States

```text
DRAFT
  -> TESTED
  -> ARMED
  -> PREWARMING
  -> RUNNING
  -> WAITING_MANUAL
  -> SUCCEEDED

Any non-terminal state may -> FAILED when a fatal condition occurs.
DRAFT/TESTED/ARMED/PREWARMING may -> CANCELLED when cancellation is still safe.
```

POC UI may collapse `DRAFT` and `TESTED` visually, but the domain distinction remains useful.

## State meanings

### DRAFT
Editable task exists but has not passed current validation/test evidence.

Allowed:
- edit
- save
- open browser
- preflight/test

Forbidden:
- live target dispatch

### TESTED
Task definition passed required local validation and a safe rehearsal/preflight policy appropriate to current mode.

Allowed:
- edit -> returns to DRAFT
- ARM
- additional tests

### ARMED
Immutable ArmedRunSnapshot exists and scheduler lease is active.

Entry requirements:
- target in future
- adapter validates
- required target facts confirmed
- no other active live lease
- local storage write succeeds

Allowed:
- DISARM/CANCEL before irreversible dispatch

Forbidden:
- task edits affecting current snapshot
- second ARM

### PREWARMING
Prewarm deadline reached.

Responsibilities:
- ensure browser process/context available
- open/warm target origin
- run safe preflight
- verify session/expected origin

Exit:
- pass -> remain waiting for target / transition logically toward RUNNING at target
- fatal preflight -> FAILED
- user cancel before dispatch -> CANCELLED

### RUNNING
Irreversible target action is being dispatched or its deterministic immediate follow-up is executing.

Entry condition:
- target signal reached within max lateness
- execution lease acquired
- run not cancelled

Cancellation rule:
- once checkout request dispatch begins, generic cancel cannot claim to undo it
- UI must show "in flight" rather than promise cancellation

### WAITING_MANUAL
Automated portion reached the configured manual checkpoint.

Typical condition:
- checkout page reached
- optional configured consent handled
- optional payment UI opened
- final payment authorization not performed by runner

Allowed:
- user completes payment manually
- user aborts
- runner may observe non-sensitive completion state only if explicitly designed later

### SUCCEEDED
POC automation objective is complete according to configured checkpoint semantics.

For the current POC, success means **successful handoff to the manual payment boundary**, not proof that payment completed.

### FAILED
Fatal stop with exact failure code/reason.

Terminal for the current run. A new attempt requires explicit user action and, for ambiguous irreversible outcomes, manual inspection first.

### CANCELLED
Run stopped before irreversible dispatch or safely disarmed.

## Transition table

| From | Event | Guard | To |
|---|---|---|---|
| DRAFT | safe validation/test passes | no blockers | TESTED |
| TESTED | edit | none | DRAFT |
| TESTED | ARM | all ARM gates pass | ARMED |
| ARMED | cancel | dispatch not started | CANCELLED |
| ARMED | prewarm due | not cancelled | PREWARMING |
| PREWARMING | preflight failure | fatal | FAILED |
| PREWARMING | cancel | dispatch not started | CANCELLED |
| PREWARMING | target due | within lateness + lease | RUNNING |
| RUNNING | target step rejected | fail-closed | FAILED |
| RUNNING | checkout + navigation complete | checkpoint criteria met | WAITING_MANUAL |
| WAITING_MANUAL | handoff accepted as POC completion | policy | SUCCEEDED |
| any active | invariant violation | fatal | FAILED |

## State-event requirements

Every transition logs:
- runId
- priorState
- nextState
- timestamp
- transitionCode
- safe reason
- stepId if applicable

## Restart behavior

On process restart:
- do not silently resume an old irreversible run
- inspect persisted snapshot/state
- if state was ARMED and target still safely in future, recovery requires an explicit recovery policy
- if state was RUNNING or result ambiguous, mark `FAILED/RECOVERY_REQUIRED` and require manual inspection

POC default should prefer fail-closed recovery over hidden replay.

## Impossible states / invariants

- two active RUNNING states for the same runId
- ARMED without persisted snapshot
- RUNNING without execution lease
- SUCCEEDED before configured manual checkpoint is reached
- retry after ambiguous success
- task mutation changing an active snapshot
- WAITING_MANUAL while browser is on unrelated origin without explanation