# Next Action

## Single next objective

**R2 — Local Store / Atomic ARM / Restart Safety.**

R1 Domain Contracts passed its tests/review. Do not expand scope or jump to R3 before R2 is independently verified.

## Read first

1. `status/CURRENT_STATUS.md`
2. `verification/R1_DOMAIN_REVIEW.md`
3. `design/IMPLEMENTATION_READY_PLAN.md` — R2 section
4. `design/COMPONENT_CONTRACTS.md` — Local Store / RunnerService
5. `design/STATE_MACHINE.md` — ARM/restart behavior
6. `design/SECURITY_MODEL.md`
7. `harness/IMPLEMENTATION_GATE_CHECKLIST.md`

## R2 Gap IDs

- G02 atomic runId + snapshot before scheduler
- G16 restart fail-closed recovery
- operational support for G01 immutable active-run snapshot

## Tests first

Before runtime integration, write tests for:
- atomic snapshot persistence
- storage failure blocks ARM/scheduling
- corrupt store is visible failure, not silent reset
- restart from RUNNING/ambiguous state never dispatches
- persisted snapshot remains immutable after reload
- terminal/cancelled history is not resumed as a live run

## Allowed implementation scope

- narrow new `src/precision_runner/store.py` (or equivalent)
- store/recovery tests
- only the minimal `service.py` integration required by R2

No scheduler redesign, adapter migration, browser refactor, UI work, or live-target request belongs in R2.

## Completion condition

R2 ends only after:
- full unit suite passes
- changed files are reviewed against storage/restart contracts
- no hidden replay path exists
- status/review evidence is updated

Then R3 becomes eligible.

## LIVE remains separate

R2 completion does not change LIVE NO-GO blockers in `verification/POC_GO_NO_GO.md`.
