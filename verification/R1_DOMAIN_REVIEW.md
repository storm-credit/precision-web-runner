# R1 Domain Contracts Review

## Verdict

**R1 SLICE: PASS.**

This is an implementation-slice verdict, not LIVE approval.

## Scope

R1 only, per `design/IMPLEMENTATION_READY_PLAN.md`.

Design authority:
- `design/COMPONENT_CONTRACTS.md`
- `design/STATE_MACHINE.md`
- `design/ERROR_POLICY.md`
- `design/OBSERVABILITY_SPEC.md`

Named gaps/foundations:
- G01 immutable ArmedRunSnapshot contract
- G03 state vocabulary contract
- G13 stable error-shape foundation
- G14 typed event-shape foundation
- G20 TEST/LIVE mode foundation

## Tests-first evidence

The first R1 commit added `tests/test_domain_contracts.py` before runtime implementation.

It verifies:
- deep snapshot immutability
- later TaskDefinition edits cannot change an armed snapshot
- TEST/LIVE serialization stays distinct
- approved state vocabulary exists
- adapter-specific values are not generic top-level TaskDefinition fields
- generic target time must be timezone-aware ISO-8601
- ErrorInfo carries code/stage/side-effect/next-action identity
- RunEvent is typed and immutable

## Implementation result

`src/precision_runner/models.py` now provides:
- `RunMode`
- approved `RunnerState` vocabulary
- `RunStage`
- `SideEffectStatus`
- `ErrorCode` / `ErrorInfo`
- generic mutable `TaskDefinition`
- frozen `ManualBoundaryPolicy`
- recursively immutable `ArmedRunSnapshot`
- typed immutable `RunEvent`

Generic `TaskDefinition` has no T1 inventory/price/shipping fields and no generic retry fields. Site-specific values belong in `adapter_variables`.

## Transitional compatibility

The pre-existing Architecture Spike still imports `TaskConfig`, legacy `Event`, and `RunnerState.READY`. R1 keeps these as explicit compatibility shims so a domain-only slice does not trigger an uncontrolled orchestrator/adapter migration.

`READY` is an enum alias of `DRAFT`; it does not add a new domain state when iterating the enum.

The compatibility layer is not the new source of truth and is scheduled for migration/removal in later R4/R6/R7 slices.

This is consistent with the approved dependency order and is not treated as a design deviation.

## Important gap interpretation

R1 establishes the domain contracts. Operational enforcement that an active run actually uses the immutable snapshot occurs when R2/R6 migrate persistence/orchestration. Likewise, RunEvent persistence/redaction is completed in R7 and TEST/LIVE command/UI semantics in R8/R9.

Therefore do not interpret R1 PASS as claiming those later behavioral slices are complete.

## Regression evidence

GitHub Actions run `31899372479` completed successfully:
- package install: PASS
- full `python -m unittest discover -s tests -v`: PASS

## Security / scope review

PASS:
- no target endpoint changes
- no server restriction bypass
- no cookie/token export
- no irreversible retry behavior added
- manual final payment boundary remains enforced by `ManualBoundaryPolicy`
- no new dependency
- no second adapter/platform feature

## Next action

R2 — Local Store / Atomic ARM / Restart Safety.

Do not start R3 in the same slice. C1 review occurs only after R1-R3 are each independently verified.
