# Implementation Plan — After Design Approval

This is a **planning document only**. Do not implement until the user approves the POC design and resolves any blocking interview questions.

## Phase 0 — Architecture spike

Goal: prove the hardest assumptions before building the dashboard.

Tasks:
1. Choose browser session strategy.
2. Connect local runner to authenticated target browser context.
3. Execute one harmless same-origin request from that context.
4. Capture a dynamic response field and use it in a follow-up navigation.
5. Prove that raw cookies are not copied into a cloud/backend store.
6. Measure scheduler dispatch timing on Windows.
7. Simulate PC sleep/wake and define failure behavior.

Gate:
- If browser/session attachment is unreliable, re-plan before UI work.

## Phase 1 — Core runner

Implement only generic core concepts:
- Task
- Recipe
- Step
- Run
- Scheduler
- Run lock
- State machine
- Variable extraction/interpolation
- Bounded retry
- Structured redacted logging

Tests first for:
- state transitions
- target-time scheduling
- duplicate-run prevention
- recipe validation
- response extraction
- timeout/failure
- retry limits

## Phase 2 — T1 Adapter 001

Implement T1-specific logic outside core:
- URL match
- request mapping
- checkout response extraction
- checkout route navigation
- consent locator strategy
- manual final-payment checkpoint

Verification order:
1. mocked response
2. safe live test item / non-final purchase flow
3. real target only after prior checks pass

## Phase 3 — Minimal responsive UI

Implement selected Concept 02.

Screens required for POC:
- Dashboard
- Task detail/edit
- Run detail/log
- Settings/device status

Required real controls:
- Test Run
- ARM
- Cancel/Disarm
- View Logs
- Manual Continue at checkpoint

Do not build decorative future features.

## Phase 4 — Mobile control

Make the same UI responsive and reachable from a trusted phone.

POC success:
- phone can see target/state/connection
- phone can test/arm/cancel when allowed
- execution still happens on Windows runner

Do not attempt mobile-only execution in this phase.

## Phase 5 — End-to-end POC verification

Required scenarios:
- happy path to manual payment checkpoint
- target time not yet allowed -> server rejection -> stop
- expired login -> preflight failure
- network timeout
- browser disconnected
- duplicate ARM/run attempt
- runner restart before target
- PC sleep/wake detection
- selector/consent element not found
- response missing checkoutNumber

Produce a POC report with:
- actual timing measurements
- failed scenarios
- unresolved risks
- recommendation: STOP / REWORK / CONTINUE TO MVP

## Phase 6 — POC exit

Stop implementation after POC report.

Do not immediately add general platform features.

If continuing to MVP, the next validation is a second structurally different site adapter without rewriting the generic scheduler/state machine.

## Working method

For each implementation task:
1. restate goal
2. define verification
3. write test or reproducible check
4. implement minimum change
5. run verification
6. spec review
7. code/security review
8. update decision/deviation docs
9. commit

If the plan changes materially, update `docs/DEVIATIONS.md` before proceeding.
