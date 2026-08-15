# Current Status

## Phase

**CONTROLLED IMPLEMENTATION — R1-R3 + C1 COMPLETE; R4 NEXT.**

Implementation proceeds one approved R-slice at a time with tests/checks first. LIVE remains **NO-GO** until every mandatory Go/No-Go row passes.

## Completed foundation

- Deep Design + Harness + implementation reconciliation
- G01-G28 gap matrix
- R1-R10 implementation-ready plan
- Harness Gate 6 coding approval

## R1 — Domain Contracts

Status: **PASS**

Evidence: `verification/R1_DOMAIN_REVIEW.md`

Established generic TaskDefinition, immutable ArmedRunSnapshot, TEST/LIVE mode, approved state vocabulary, and error/event contract foundations.

## R2 — Local Store / Atomic ARM / Restart Safety

Status: **PASS**

Evidence: `verification/R2_STORE_RECOVERY_REVIEW.md`

Established versioned LocalStore, atomic active-run persistence before scheduler thread activation, visible storage/corruption failures, and fail-closed restart behavior with no silent replay.

## R3 — Scheduler / Timing Contract

Status: **PASS**

Evidence: `verification/R3_SCHEDULER_REVIEW.md`

Established:
- typed ScheduleRequest / SchedulerSignal contract
- wall-clock target converted to one monotonic deadline at ARM
- PREWARM_DUE / TARGET_DUE / CANCELLED / LATE / CLOCK_DISCONTINUITY
- snapshot maxLatenessMs consumption
- no intentional early target signal
- wall/monotonic jump detection
- abnormal wait/suspend/stall overshoot detection
- service integration from immutable ArmedRunSnapshot

A C1 blindspot review found that sleep/stall can advance wall and monotonic clocks together; R3 was hardened to detect abnormal wait overshoot before closure. Full CI passes after the hardening.

## C1 — Foundation Checkpoint

Status: **PASS**

Evidence: `verification/C1_FOUNDATION_REVIEW.md`

C1 revalidated R1-R3 together:
- generic forward domain
- deep snapshot immutability
- persistence-before-scheduler ordering
- storage/restart fail-closed safety
- monotonic timing contract
- late/discontinuity blocking

No unresolved C1 BLOCKER or MAJOR finding remains.

## Transitional compatibility

Legacy `TaskConfig`, legacy `Event`, `task.json`, T1-coupled adapter/browser paths, and spike retry code remain only where later approved slices own migration. They must not become new core contracts.

## Next implementation slice

**R4 — Adapter Contract + T1 Adapter Migration**

R4 must move T1-specific request schema, variables, evidence status, parsing, locators, and manual-checkpoint semantics behind the approved Adapter v1 contract without weakening R1-R3 foundations.

Do not begin BrowserBridge refactor (R5) inside R4 except for the smallest compile/test seam explicitly required by the adapter contract.

## LIVE blockers remain

- Signature Edition `shippingType` unverified
- Windows dedicated Chrome session persistence not rehearsed
- profile ownership/duplicate runner not rehearsed
- >=5 timing rehearsals not completed
- evidence-based `maxLatenessMs` not selected
- safe checkout/navigation/manual-handoff rehearsal pending
- log redaction inspection pending
- near-live target contract freshness pending

Coding completion never overrides these LIVE gates.
