# Current Status

## Phase

**CONTROLLED IMPLEMENTATION — R1 + R2 COMPLETE; R3 NEXT.**

Implementation proceeds one approved R-slice at a time with tests/checks first. LIVE remains **NO-GO** until every mandatory Go/No-Go row passes.

## Completed foundation

- Deep Design + Harness + implementation reconciliation
- G01-G28 gap matrix
- R1-R10 implementation-ready plan
- Harness Gate 6 coding approval

## R1 — Domain Contracts

Status: **PASS**

Evidence: `verification/R1_DOMAIN_REVIEW.md`

Established:
- TEST/LIVE mode
- generic TaskDefinition
- immutable ArmedRunSnapshot
- approved state vocabulary
- error/event contract foundations

## R2 — Local Store / Atomic ARM / Restart Safety

Status: **PASS**

Evidence: `verification/R2_STORE_RECOVERY_REVIEW.md`

Established:
- versioned LocalStore
- editable task separated from immutable active-run snapshot
- atomic active-run persistence before scheduler start
- runId persisted with snapshot
- storage/corruption failures visible
- restart with any active run fails closed
- RUNNING/ambiguous state never silently replays
- terminal cancellation archived to history

The first R2 CI exposed a guard-order defect: target validation ran before recovery blocking. Recovery is now checked first and rechecked under the commit lock. Latest full CI passed.

## Transitional compatibility

Legacy `TaskConfig`, `Event`, `task.json`, T1-coupled browser/adapter paths, and the spike retry loop remain only where later approved slices own their migration. They are not design source of truth.

## Next implementation slice

**R3 — Scheduler / Timing Contract**

R3 closes:
- G07 SchedulerSignal / clock discontinuity
- G08 explicit snapshot maxLatenessMs
- foundation for G26 timing evidence

R3 must be browser/site independent and testable with a fake/injected clock where practical. It must not intentionally dispatch before the configured permitted time.

## Cross-slice checkpoint

After R3 passes independently, run Checkpoint C1 across R1-R3:
- generic domain boundary
- snapshot immutability
- atomic/restart safety
- scheduler/clock safety

Do not start R4 until C1 passes.

## LIVE blockers remain

- Signature Edition `shippingType` unverified
- Windows dedicated Chrome session persistence not rehearsed
- profile ownership/duplicate runner not rehearsed
- >=5 timing rehearsals not completed
- evidence-based `maxLatenessMs` not selected
- safe checkout/navigation/manual-handoff rehearsal pending
- log redaction inspection pending
- near-live target contract freshness pending
