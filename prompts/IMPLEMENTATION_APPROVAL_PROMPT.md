# Implementation Approval Prompt

Use this prompt only after Deep Design + Harness + Reconciliation are complete.

## Context Dump

- Project: Precision Web Runner
- Current phase: implementation-ready planning complete; runtime frozen
- Design authority: `design/*`
- Reconciliation authority: `design/IMPLEMENTATION_RECONCILIATION.md`
- Gap authority: `verification/IMPLEMENTATION_GAP_MATRIX.md`
- Ordered plan: `design/IMPLEMENTATION_READY_PLAN.md`
- Harness review: `verification/IMPLEMENTATION_READY_REVIEW.md`
- Live gate: `verification/POC_GO_NO_GO.md`
- Existing runtime: Architecture Spike only
- POC boundary: Windows-local, T1 Adapter 001, manual final payment, no restriction bypass

## Goal Prompt

Goal:
Implement the approved Precision Web Runner POC reconciliation one R-slice at a time, starting at R1 only.

Success conditions:
- close only the Gap IDs assigned to the active slice
- satisfy cited design contracts
- tests/checks are defined before code
- minimal/surgical runtime change
- no T1-specific logic leaks into generic core
- no irreversible checkout auto-replay
- no secret/PII persistence
- final payment remains manual
- regression suite passes
- changed-file review completed
- status/deviations updated when needed

Stop conditions:
- a new design BLOCKER appears
- observed target behavior contradicts approved design
- required change exceeds current R-slice
- session safety would require cookie/token export
- solution requires server restriction bypass
- irreversible ambiguity would require automatic replay
- final payment authorization would need automation
- a critical condition cannot be tested

## Implementation constraints

- Start with R1 only; do not pre-implement R2-R10.
- Read `CLAUDE.md`, `status/CURRENT_STATUS.md`, and `status/NEXT_ACTION.md` first.
- Reference Gap IDs in the task/commit/PR.
- Modify only files permitted by the active R-slice unless a documented blocker requires replanning.
- Preserve the existing proven Architecture Spike behavior only where it conforms to design.
- Prefer reconciliation over rewrite-from-zero.
- No speculative framework/dependency additions.
- No live T1 irreversible request as a coding test.

## Result Verification

Before saying the slice is complete, report:
1. Gap IDs closed
2. design contracts satisfied
3. files changed
4. tests written first / checks used
5. test output
6. security/side-effect review
7. deviations from plan
8. remaining blockers
9. whether next R-slice is now safe to begin

Never report the POC as LIVE-ready from implementation evidence alone. LIVE requires `verification/POC_GO_NO_GO.md` PASS.