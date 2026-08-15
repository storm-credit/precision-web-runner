# Precision Web Runner

A local-first POC for executing an **authorized web action flow at a scheduled time** from a logged-in browser session.

T1 Membership is Adapter 001, but the scheduler, state machine, browser bridge, and adapter contracts are designed to remain site-agnostic.

## Current status

**DEEP DESIGN + HARNESS FREEZE.**

Runtime code already exists in `main`, but it is currently classified as **Architecture Spike / prototype evidence**. The user explicitly requested that coding happen last, so no further runtime expansion/refactor should occur until the deep design is reviewed and approved.

Read first:

- `status/CURRENT_STATUS.md`
- `status/NEXT_ACTION.md`
- `CLAUDE.md`
- `harness/GATES.md`
- `verification/POC_GO_NO_GO.md`

## Immediate POC target

The narrow POC target remains the 2026-08-17 T1 flow:

```text
Windows runner
  -> dedicated logged-in Chrome profile
  -> scheduled prewarm
  -> one allowed target-time checkout action
  -> dynamic checkoutNumber
  -> checkout navigation
  -> optional pre-authorized consent handling
  -> manual payment handoff
```

The runner never bypasses membership, sale-time, stock, queue, CAPTCHA, rate-limit, authorization, or payment controls. Final PG/3DS/OTP/payment authorization remains manual.

## Deep-design baseline

### System / contracts
- `design/SYSTEM_DESIGN.md`
- `design/COMPONENT_CONTRACTS.md`
- `design/STATE_MACHINE.md`
- `design/SEQUENCE_FLOWS.md`

### Reliability / security
- `design/ERROR_POLICY.md`
- `design/TIMING_DESIGN.md`
- `design/BROWSER_LIFECYCLE.md`
- `design/SECURITY_MODEL.md`
- `design/OBSERVABILITY_SPEC.md`

### Extensibility / UX
- `design/ADAPTER_SPEC.md`
- `design/UI_SPEC.md`

## Harness

- `CLAUDE.md` — project constitution
- `harness/HARNESS_OVERVIEW.md` — review roles and process architecture
- `harness/GATES.md` — mandatory context/design/implementation/live gates
- `status/CURRENT_STATUS.md` — current phase and known facts
- `status/NEXT_ACTION.md` — one next objective
- `prompts/META_PROMPTING.md` — context dump → prompt distillation → result verification
- `prompts/DESIGN_REVIEW_PROMPT.md` — deep-design review prompt

## Verification

- `verification/ACCEPTANCE_MATRIX.md` — Given/When/Expected evidence matrix
- `verification/POC_GO_NO_GO.md` — mandatory live gate
- `docs/POC_RUNBOOK_2026-08-17.md` — rehearsal/live runbook (must be reconciled after design approval)

## Existing prototype

The repository currently contains a Python/Playwright local prototype with:
- local scheduler
- dedicated persistent Chrome profile
- Concept 02 responsive dashboard
- T1 checkout adapter
- checkoutNumber extraction/navigation
- local logs and basic tests

Do **not** treat this implementation as final architecture. After design approval it must be reviewed component-by-component as `KEEP / CHANGE / DELETE` against the contracts under `design/`.

## Known LIVE blockers

- Signature Edition `shippingType` is still not independently verified.
- Windows/T1 session persistence has not yet been rehearsed on the user's machine.
- Actual Windows scheduling variance has not yet been measured.
- Current target-site behavior must be rechecked before live use.

Therefore current live status is **NO-GO / DESIGN IN REVIEW**.

## Original supporting documents

- `docs/POC_SCOPE.md`
- `docs/PRODUCT_DESIGN.md`
- `docs/ARCHITECTURE.md`
- `docs/BLINDSPOT_AND_TRAPS.md`
- `docs/T1_EVIDENCE.md`
- `docs/UI_CONCEPTS.md`
- `docs/REFERENCE_RESEARCH.md`
- `docs/DECISIONS_AND_INTERVIEW.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/DEVIATIONS.md`

## Roadmap

1. **Deep Design + Harness** — current phase.
2. **Implementation reconciliation** — only after design approval.
3. **POC rehearsal / live decision** — only after acceptance and Go/No-Go evidence.
4. **MVP** — second structurally different adapter to validate abstraction.
5. **General platform** — user URLs + adapters/recipes + broader device support.