# Checkpoint C1 — Domain / Storage / Timing Foundation Review

## Verdict

**C1: PASS — R4 ELIGIBLE AFTER R3 MERGE.**

C1 reviews R1-R3 together. It does not approve target-site integration or LIVE use.

## Reviewed slices

- R1 — Domain Contracts
- R2 — Local Store / Atomic ARM / Restart Safety
- R3 — Scheduler / Timing Contract

Evidence:
- `verification/R1_DOMAIN_REVIEW.md`
- `verification/R2_STORE_RECOVERY_REVIEW.md`
- `verification/R3_SCHEDULER_REVIEW.md`

## Cross-slice invariants

| Invariant | Result | Evidence |
|---|---|---|
| Generic forward domain is separate from T1 product fields | PASS | TaskDefinition + adapter_variables |
| Active run configuration is immutable | PASS | deep-frozen ArmedRunSnapshot + tests |
| Task edits cannot mutate armed run | PASS | R1 mutation test |
| runId + snapshot exist before scheduler thread starts | PASS | R2 persistence/order tests |
| storage failure prevents scheduler/browser work | PASS | R2 failing-store test |
| corrupt store is visible, not silently reset | PASS | R2 StoreCorrupt test |
| restart never silently replays an active/in-flight run | PASS | R2 recovery tests |
| target is converted once to monotonic deadline | PASS | R3 SchedulerLease |
| scheduler never intentionally emits target early | PASS | R3 fake-clock test |
| max lateness comes from armed snapshot contract | PASS | R3 service/scheduler integration test |
| missed target fails closed | PASS | R3 LATE signal |
| wall/monotonic clock jumps fail closed | PASS | R3 discontinuity tests |
| suspend/severe wait overshoot fails closed | PASS | R3 oversleep hardening test |
| scheduler has no site/browser dependency | PASS | scheduler module + tests |

## Reviewer lenses

### Architecture
PASS.

The dependency direction is now suitable for the next phase:

```text
TaskDefinition
  -> ArmedRunSnapshot
     -> LocalStore
     -> ScheduleRequest / SchedulerLease
        -> RunnerService consumption
```

Site-specific migration can now occur in R4 without redesigning timing/storage foundations.

### Reliability
PASS FOR FOUNDATION.

The most dangerous foundation cases are fail-closed:
- persistence failure before ARM
- restart with active run
- clock discontinuity
- severe wait overshoot
- excessive target lateness

Actual Windows variance remains an R10 evidence requirement.

### Side-effect safety
PASS FOR FOUNDATION.

R1-R3 add no permission bypass and no final-payment automation. Restart does not replay prior work, and late/discontinuous schedules do not catch up with an irreversible request.

### Security/privacy
PASS FOR FOUNDATION.

No credential/session export is introduced. Persistence contains task/run metadata, not browser cookies or payment data. Full structured redaction is still R7.

### Testability
PASS.

Scheduler logic is isolated behind an injected clock, and store/recovery logic is exercised without target-network access.

## Findings

### BLOCKER
None.

### MAJOR
None unresolved.

### MINOR / explicitly deferred

1. Legacy `TaskConfig`, legacy `Event`, and T1Adapter ownership still exist in the spike runtime. R4-R7 own migration; they are not allowed to become new core contracts.
2. Legacy `task.json` is still dual-written during migration. Versioned generic storage is authoritative for new run-safety behavior; later API/adapter slices remove the compatibility path.
3. Terminal history append and active-file removal are safety-ordered rather than one multi-file transaction. If removal fails, the active marker remains and recovery blocks; duplicate history is preferable to silent replay. This is acceptable for the POC.
4. `maxLatenessMs=2000` is still a provisional default. R10 empirical evidence must confirm/select the LIVE value.
5. Deterministic scheduler tests do not prove OS scheduling accuracy; they prove contract behavior only.

## Scope check

C1 did not introduce:
- second adapter
- arbitrary URL automation
- cloud execution
- LAN/mobile remote control
- CAPTCHA/queue/anti-bot bypass
- automatic irreversible retry
- final payment authorization

## Decision

The foundation is stable enough to proceed to **R4 — Adapter Contract + T1 Adapter Migration**.

R4 must not change R1-R3 contracts merely to accommodate the current T1 spike. If T1 evidence contradicts a foundation contract, stop and re-review rather than weakening the foundation silently.

LIVE remains NO-GO independently of C1.
