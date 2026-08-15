# R2 Local Store / Atomic ARM / Restart Safety Review

## Verdict

**R2 SLICE: PASS.**

This verdict covers persistence/recovery safety only. It does not approve scheduler precision, adapter migration, browser behavior, checkout semantics, or LIVE use.

## Scope

R2 only, per `design/IMPLEMENTATION_READY_PLAN.md`.

Gap IDs:
- G02 atomic runId + snapshot before scheduler
- G16 restart fail-closed recovery
- operational support for G01 immutable active-run snapshot

Design authority:
- `design/COMPONENT_CONTRACTS.md` — Local Store / RunnerService
- `design/STATE_MACHINE.md` — ARM and restart behavior
- `design/SECURITY_MODEL.md`

## Tests-first evidence

R2 tests were committed before runtime/store implementation:
- `tests/test_store.py`
- `tests/test_service_recovery.py`

They cover:
- editable TaskDefinition separated from active snapshot
- loaded ArmedRunSnapshot remains deeply immutable
- atomic write failure is visible and leaves no active-run file
- corrupt active store raises StoreCorrupt instead of silently defaulting
- RUNNING/AMBIGUOUS state survives for recovery review
- CANCELLED terminal run moves to history and is not resumed
- versioned store format
- storage failure blocks ARM before scheduler/browser work
- restart from RUNNING/AMBIGUOUS fails closed with RECOVERY_REQUIRED and no browser call
- successful ARM persists runId/snapshot before schedule thread starts

## Implementation result

New `src/precision_runner/store.py` provides:
- schema version 1
- separate editable task and active-run files
- `ActiveRunRecord`
- atomic same-directory temp-file + fsync + replace writes
- run history append for terminal records
- explicit StoreError / StoreCorrupt
- immutable ArmedRunSnapshot reconstruction

`RunnerService` now:
- accepts/injects LocalStore
- inspects active-run state on startup
- never silently resumes a prior active run
- blocks another ARM while recovery is pending
- creates UUID runId + immutable LIVE snapshot
- persists the active snapshot before changing state or starting the schedule thread
- stores active state transitions conservatively
- keeps in-flight/ambiguous failures for manual recovery review
- archives safe pre-dispatch terminal cancellation/failure

## First CI finding and correction

The first R2 implementation CI failed one recovery test because `arm()` performed T1 target validation before checking the persisted recovery block. That ordering could surface an unrelated configuration error before the more authoritative safety condition.

Correction:
- recovery/active-run guard now executes before target validation in `arm()` and `run_now()`
- the guard is rechecked under the commit lock before persistence/start

This was a local control-order defect, not a design change. The approved R2 contract remains unchanged.

## Verification evidence

Latest R2 GitHub Actions run `31899750846`:
- package install: PASS
- full `python -m unittest discover -s tests -v`: PASS

## Security / side-effect review

PASS for R2 scope:
- persistence is local only
- no cookie/token export added
- no target endpoint/request change
- no bypass behavior added
- no new irreversible replay behavior added
- storage failure before ARM prevents scheduling
- restart never performs target/browser actions automatically

## Transitional items intentionally not solved in R2

- legacy `task.json` remains temporarily alongside the versioned generic task store; later adapter/API migration removes this compatibility path
- exact side-effect classification for every RUNNING failure is intentionally conservative and is refined in R6
- generic retry loop still exists in Architecture Spike code but remains effectively zero-retry and is removed/reworked in R6
- hardcoded lateness threshold and scheduler signaling are R3
- T1-specific Browser/Adapter coupling is R4/R5
- a user-facing recovery-resolution command is later control/orchestrator work; R2 only guarantees no silent replay

These are already assigned to later approved slices and do not expand R2.

## Completion checklist

- [x] G02 persistence boundary implemented and tested
- [x] G16 restart fail-closed implemented and tested
- [x] active snapshot immutable after reload
- [x] scheduler not started when active snapshot persistence fails
- [x] no browser activity on recovery startup
- [x] full unit suite passes
- [x] no scope expansion

## Next action

R3 — Scheduler / Timing Contract.

Do not begin R4 until R3 passes independently and Checkpoint C1 reviews R1-R3 together.
