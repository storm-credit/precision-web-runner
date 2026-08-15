# Next Action

## Single next objective

**User review / approval of the Deep Design + Harness baseline.**

The design package is internally reviewed and has no unresolved design BLOCKER. Runtime remains frozen.

## Review order

1. `status/CURRENT_STATUS.md`
2. `design/DESIGN_REVIEW_REPORT.md`
3. `design/DEEP_BLINDSPOT_REVIEW.md`
4. `design/SYSTEM_DESIGN.md`
5. `design/COMPONENT_CONTRACTS.md`
6. `design/STATE_MACHINE.md`
7. `design/ERROR_POLICY.md`
8. `design/TIMING_DESIGN.md`
9. `design/SECURITY_MODEL.md`
10. `design/ADAPTER_SPEC.md`
11. `design/UI_SPEC.md`
12. `verification/ACCEPTANCE_MATRIX.md`
13. `verification/POC_GO_NO_GO.md`

## Decisions to notice during approval

- existing runtime is an Architecture Spike, not final design
- dedicated Chrome profile remains the session strategy
- live POC dashboard defaults to localhost-only
- responsive mobile/narrow UI remains, but remote phone control is deferred
- LIVE checkout POST automatic replay is disabled
- ambiguous irreversible outcome requires manual inspection
- target action is never intentionally dispatched before the permitted opening time
- final payment authorization remains manual

## If approved

Next technical phase is **Implementation Reconciliation**, starting with a KEEP / CHANGE / DELETE inventory of existing prototype code against the approved contracts.

Do not jump directly to feature additions.

## If not approved

Change the design documents first, re-run `prompts/DESIGN_REVIEW_PROMPT.md`, update `docs/DEVIATIONS.md` if the plan changed materially, and keep runtime frozen.

## LIVE remains separate

Design approval does not equal live approval.

LIVE requires all mandatory evidence in `verification/POC_GO_NO_GO.md`, including Signature `shippingType`, Windows/browser rehearsal, timing measurements, and target-contract freshness.