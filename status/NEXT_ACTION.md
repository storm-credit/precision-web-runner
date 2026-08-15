# Next Action

## Single next objective

Complete the **Implementation-Ready Plan** while keeping runtime code frozen.

The Deep Design baseline has been reviewed, the user instructed the project to continue, and the existing Architecture Spike has now been classified file-by-file in `design/IMPLEMENTATION_RECONCILIATION.md`.

## Required planning order

1. Read `status/CURRENT_STATUS.md`.
2. Read `design/IMPLEMENTATION_RECONCILIATION.md`.
3. Read `verification/IMPLEMENTATION_GAP_MATRIX.md`.
4. Map each future implementation slice to one or more Gap IDs.
5. For each slice, name the design contract it satisfies.
6. Define tests/checks **before** code changes.
7. Define completion evidence and rollback boundary.
8. Verify dependency order so no unsafe half-state is introduced.
9. Re-run Harness Gate 6 — Implementation Ready.
10. Present the final plan for explicit user coding approval.

## Planned slices

- R1 Domain contracts: TaskDefinition, ArmedRunSnapshot, RunId, Mode, state/error/event types
- R2 Local Store + atomic ARM + restart inspection
- R3 Scheduler/timing/discontinuity/telemetry
- R4 Adapter Contract v1 + T1 migration
- R5 Generic BrowserBridge + origin/profile guards
- R6 Orchestrator + side-effect-aware Error Policy
- R7 Observability/redaction/retention
- R8 Local Control API hardening
- R9 Concept 02 UI reconciliation + TEST/LIVE/blockers
- R10 Windows evidence gates + safe rehearsals

## Do not do next

- do not modify `src/`, `tests/`, `scripts/`, or dependencies
- do not add features outside reconciliation
- do not add second-site support
- do not enable LAN/remote phone control
- do not automate final payment authorization
- do not guess Signature `shippingType`
- do not perform irreversible live target requests merely to collect evidence

## Coding trigger

Runtime implementation begins only after the user explicitly approves the final R1-R10 implementation plan.

## LIVE remains separate

Even after coding approval/completion, LIVE remains NO-GO until all mandatory target/environment/rehearsal/timing/failure/UI/day-of-live gates pass in `verification/POC_GO_NO_GO.md`.