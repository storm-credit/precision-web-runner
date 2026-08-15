# Next Action

## Single next objective

**Obtain explicit user approval before runtime coding.**

Implementation reconciliation and the final R1-R10 implementation-ready plan are complete. Harness Gate 6 passed for planning. The project must now stop because the user explicitly requested coding last.

## Approved plan to review

1. `design/IMPLEMENTATION_RECONCILIATION.md`
2. `verification/IMPLEMENTATION_GAP_MATRIX.md`
3. `design/IMPLEMENTATION_READY_PLAN.md`
4. `verification/IMPLEMENTATION_READY_REVIEW.md`
5. `verification/POC_GO_NO_GO.md`

## If coding is approved

Begin **R1 Domain Contracts only**.

Do not jump to R2-R10 in the same uncontrolled change.

R1 must:
- cite Gap IDs G01/G03/G13/G14/G20
- define tests first
- modify only approved R1 files
- keep T1-specific values out of generic core
- create immutable ArmedRunSnapshot foundation
- run regression tests
- complete C1 review prerequisites as applicable
- update status/deviations if reality differs

Then stop for slice verification before R2.

## If coding is not approved yet

Make no runtime changes. Documentation can be clarified, but no feature work starts.

## LIVE remains separate

Coding approval is not LIVE approval. `verification/POC_GO_NO_GO.md` must still pass all target, environment, rehearsal, timing, failure, UX, and day-of-live gates.