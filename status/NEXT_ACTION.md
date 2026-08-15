# Next Action

## Single next objective

**R3 — Scheduler / Timing Contract.**

R1 and R2 passed independently. Do not begin R4 before R3 passes and Checkpoint C1 reviews R1-R3 together.

## Read first

1. `status/CURRENT_STATUS.md`
2. `verification/R1_DOMAIN_REVIEW.md`
3. `verification/R2_STORE_RECOVERY_REVIEW.md`
4. `design/IMPLEMENTATION_READY_PLAN.md` — R3 section
5. `design/TIMING_DESIGN.md`
6. `design/COMPONENT_CONTRACTS.md` — Scheduler
7. `harness/IMPLEMENTATION_GATE_CHECKLIST.md`

## R3 Gap IDs

- G07 SchedulerSignal / clock discontinuity
- G08 explicit `maxLatenessMs`
- prepares G26 live timing evidence

## Tests first

Write deterministic timing tests for:
- prewarm deadline ordering
- PREWARM_DUE and TARGET_DUE each emitted once
- cancellation before target
- LATE when max lateness exceeded
- clock/sleep discontinuity fails closed
- already-past target rejection
- no intentional early target signal

Use an injected/fake clock where practical. Browser/T1 dependencies are forbidden in scheduler tests.

## Allowed implementation scope

- `src/precision_runner/timing.py`
- optional narrow `scheduler.py` if clearer
- `tests/test_timing.py` and new scheduler tests
- minimal `service.py` integration to consume the scheduler contract

No adapter migration, BrowserBridge refactor, UI work, or target-site request belongs in R3.

## Completion condition

R3 ends only after:
- full unit suite passes
- hardcoded orchestrator lateness policy is replaced by snapshot timing contract
- no early dispatch path exists
- discontinuity/late behavior is explicit
- R3 review evidence is recorded
- C1 review passes

Then R4 becomes eligible.
