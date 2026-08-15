# R3 Scheduler / Timing Contract Review

## Verdict

**R3 SLICE: PASS.**

This is a deterministic scheduler-contract verdict, not evidence of Windows live timing precision.

## Scope

R3 only, per `design/IMPLEMENTATION_READY_PLAN.md`.

Gap IDs:
- G07 SchedulerSignal / discontinuity contract
- G08 explicit ArmedRunSnapshot `maxLatenessMs` consumption
- foundation for G26 timing evidence

Design authority:
- `design/TIMING_DESIGN.md`
- `design/COMPONENT_CONTRACTS.md` — Scheduler
- `design/STATE_MACHINE.md`
- `design/ERROR_POLICY.md`

## Tests-first evidence

`tests/test_scheduler.py` was committed before scheduler implementation and verifies:
- past target rejected at ARM
- prewarm and target monotonic deadlines
- PREWARM_DUE / TARGET_DUE logical single emission
- cancellation before target
- LATE when target wake exceeds snapshot max lateness
- wall-clock jump -> CLOCK_DISCONTINUITY
- monotonic-only jump -> CLOCK_DISCONTINUITY
- immediate prewarm when ARM occurs inside prewarm window
- target signal never emitted before target monotonic deadline

`tests/test_service_scheduler.py` additionally verifies RunnerService creates its ScheduleRequest directly from the immutable ArmedRunSnapshot.

## Implementation result

New `src/precision_runner/scheduler.py` provides:
- typed `ScheduleRequest`
- typed `SchedulerSignalKind`
- typed `SchedulerSignal`
- injectable Clock protocol + SystemClock
- one SchedulerLease per armed run
- wall-clock target converted once to monotonic deadline at ARM
- prewarm deadline derived without shifting the target earlier
- cancellation signal
- target lateness measured against snapshot `max_lateness_ms`
- wall-vs-monotonic discontinuity detection
- abnormal wait-overshoot detection for suspend/severe scheduler stall

RunnerService now:
- creates the scheduler lease from the immutable snapshot
- preserves R2 ordering: active snapshot persisted before scheduler thread activation
- consumes PREWARM_DUE / TARGET_DUE / CANCELLED / LATE / CLOCK_DISCONTINUITY explicitly
- no longer performs the old hardcoded wall-clock `wait_until` + hardcoded post-wake 2-second comparison
- records safe scheduler lateness details for later observability migration

## Deep-blindspot correction before close

C1 review identified a timing blind spot: if sleep/stall advances wall and monotonic clocks together, clock-skew comparison alone may not detect it.

R3 was therefore hardened before completion:
- each chunked wait measures actual monotonic elapsed time
- abnormal wait overshoot beyond the configured tolerance emits CLOCK_DISCONTINUITY
- deterministic test simulates a 5-second oversleep with wall and monotonic advancing together

This is a reliability hardening within the approved timing design, not a product-scope change.

## Verification evidence

Latest R3 GitHub Actions run `31900095768`:
- package install: PASS
- full `python -m unittest discover -s tests -v`: PASS

## Safety review

PASS:
- target deadline is never intentionally moved earlier
- past target cannot ARM scheduler
- LATE blocks dispatch rather than catching up
- clock/suspend discontinuity blocks dispatch
- scheduler has no T1/browser/network dependency
- cancellation does not imply undo after target-side work; RunnerService still owns that boundary

## Known limits / later evidence

- `_DEFAULT_MAX_LATENESS_MS = 2000` remains a provisional POC default captured into the snapshot; R10 must select/confirm the live value from >=5 Windows rehearsals
- deterministic fake-clock tests do not prove Windows scheduling variance
- existing legacy `timing.py` remains as compatibility/tested utility but RunnerService no longer uses it for armed execution
- detailed timing telemetry schema/persistence is R7; empirical timing evidence is R10

## Completion checklist

- [x] G07 typed scheduler signals
- [x] clock discontinuity behavior
- [x] severe wait/sleep overshoot behavior
- [x] G08 snapshot max lateness consumed
- [x] no intentional early target signal
- [x] service integration uses immutable snapshot
- [x] full CI passes
- [x] no scope expansion

## Next action

Run Checkpoint C1 across R1-R3. R4 is not eligible until C1 passes.
