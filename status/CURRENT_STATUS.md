# Current Status

## Phase

**IMPLEMENTATION AUTHORIZED — R1 DOMAIN CONTRACTS COMPLETE; R2 NEXT.**

The user explicitly approved continuing into coding after Deep Design, reconciliation, and Harness Gate 6. Implementation now proceeds one approved R-slice at a time with tests/checks first.

LIVE remains **NO-GO** until every mandatory Go/No-Go row passes.

## Completed before coding

- Deep Design baseline and review
- Harness / Gate 0-10 workflow
- implementation reconciliation (KEEP/CHANGE/MOVE/DELETE)
- G01-G28 gap matrix
- R1-R10 implementation-ready plan
- Harness Gate 6 PASS for coding approval

## R1 — Domain Contracts

Status: **PASS**

Implemented in the R1 branch:
- first-class `RunMode(TEST, LIVE)`
- approved RunnerState vocabulary
- generic `TaskDefinition`
- adapter-specific `adapter_variables`
- immutable/deep-frozen `ArmedRunSnapshot`
- manual payment boundary policy
- stable ErrorCode/ErrorInfo foundation
- typed immutable RunEvent foundation

Tests were committed before runtime implementation. Full GitHub Actions unit suite passed.

Review evidence:
- `verification/R1_DOMAIN_REVIEW.md`

## Transitional compatibility

Existing Architecture Spike `TaskConfig`, legacy `Event`, and `RunnerState.READY` remain temporarily so R1 does not trigger an uncontrolled adapter/orchestrator rewrite.

They are compatibility shims only. The approved generic domain is now the forward source of truth and later slices migrate runtime behavior onto it.

## Next implementation slice

**R2 — Local Store / Atomic ARM / Restart Safety**

R2 must establish:
- editable TaskDefinition storage separate from ArmedRunSnapshot
- atomic runId + snapshot persistence before scheduling
- versioned local store format
- visible storage corruption/failure
- restart fail-closed behavior
- no silent replay from prior RUNNING/ambiguous state

Do not start R3 until R2 has its own tests, review, CI evidence, and slice completion record.

## Cross-slice checkpoint

Checkpoint C1 occurs after R1, R2, and R3 are independently complete. C1 rechecks:
- domain genericity
- snapshot immutability
- restart/storage invariants
- scheduler/timing safety

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
