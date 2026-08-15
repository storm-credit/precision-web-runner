# Implementation Reconciliation Plan — AFTER Deep Design Approval

> Planning document only. Runtime code already exists as Architecture Spike evidence. Do not modify it until the deep-design baseline is reviewed and approved by the user.

## Phase 0 — Design review / freeze exit

Requirements:
- `design/*` reviewed
- `harness/GATES.md` through Design Review complete
- no unresolved BLOCKER
- user approval recorded
- `verification/ACCEPTANCE_MATRIX.md` accepted

Output:
- explicit DESIGN PASS
- list of implementation reconciliation tasks

## Phase 1 — Spike inventory: KEEP / CHANGE / DELETE

Review every runtime artifact against deep contracts.

At minimum:
- `src/precision_runner/models.py`
- `src/precision_runner/timing.py`
- `src/precision_runner/service.py`
- `src/precision_runner/browser_worker.py`
- `src/precision_runner/t1_adapter.py`
- `src/precision_runner/webapp.py`
- `src/precision_runner/static/index.html`
- Windows scripts
- tests

For each file/component record:
- KEEP — already matches contract
- CHANGE — behavior/interface must change
- DELETE — prototype approach conflicts with design

Do not start editing until this inventory exists.

## Phase 2 — Safety-critical core first

Priority order:
1. immutable ArmedRunSnapshot
2. finite state machine
3. one irreversible execution lease
4. per-step side-effect classification
5. no automatic irreversible checkout replay
6. structured error taxonomy
7. redacted event schema
8. scheduler target/monotonic timing contract
9. restart/recovery fail-closed behavior

Tests before implementation changes for each contract.

## Phase 3 — BrowserBridge reconciliation

Implement/verify:
- dedicated persistent Chrome profile
- single profile owner
- session preflight
- origin allowlist
- same-origin request execution
- no cookie export
- browser crash/restart classification
- popup/new-tab observation for payment handoff

## Phase 4 — T1 Adapter 001 reconciliation

Adapter must conform to `design/ADAPTER_SPEC.md`.

Verify:
- exact origin/path/method/body contract
- current-run `checkoutNumber` extraction only
- no merging unrelated cart fields without evidence
- semantic locators
- unknown live facts block ARM
- Signature `shippingType` confirmed before LIVE

## Phase 5 — UI reconciliation

Concept 02 only.

Verify all state-specific behavior from `design/UI_SPEC.md`:
- TEST/LIVE distinction
- exact blockers
- immutable armed settings
- no misleading cancel after irreversible dispatch
- side-effect-aware failure actions
- WAITING_MANUAL wording
- narrow/mobile first-viewport requirements

POC binding remains localhost-only.

## Phase 6 — Automated verification

Map tests to `verification/ACCEPTANCE_MATRIX.md`.

At minimum cover pure/local logic:
- task/snapshot validation
- state transitions
- duplicate lease
- error classification
- no retry on ambiguous irreversible step
- checkout response extraction
- missing dynamic ID
- redaction
- timing helper behavior
- restart recovery policy

## Phase 7 — Windows/browser rehearsal

Only after automated checks pass.

Perform safe rehearsals for:
- login/session persistence
- profile lock
- safe preflight
- checkout creation/navigation on a safe intended item/flow
- consent configuration if used
- payment handoff without final authorization
- browser failure behavior
- log redaction

## Phase 8 — Timing rehearsal

Run at least 5 safe scheduled trials.

Record:
- targetAt
- schedulerWakeAt
- requestStartedAt
- responseReceivedAt
- dispatchLatenessMs

Select final `maxLatenessMs` from evidence and update design/decision docs if necessary.

## Phase 9 — Live Go/No-Go

Use `verification/POC_GO_NO_GO.md`.

Unknown mandatory item = NO-GO.

No last-minute unreviewed feature or retry change is allowed to turn NO-GO into GO.

## Phase 10 — POC exit report

After live/safe proof, write:
- actual result
- state/timing path
- failure/success evidence
- remaining risks
- abstraction findings
- recommendation: STOP / REWORK / CONTINUE TO MVP

Do not immediately build generic-platform features.

## Working method

For every implementation reconciliation task:
1. cite the exact design contract
2. define test/check first
3. make the smallest change
4. run targeted test
5. run regression
6. review security/spec impact
7. update deviations if behavior changed
8. commit with evidence

If reality contradicts design, stop and update/review the design before continuing.