# Current Status

## Phase

**CONTROLLED IMPLEMENTATION — R1-R6 + C1/C2 COMPLETE; R7 NEXT.**

Implementation proceeds one approved R-slice at a time with tests/checks first. LIVE remains **NO-GO** until every mandatory Go/No-Go row passes.

## Completed and reviewed

- R1 Domain Contracts — PASS
- R2 Local Store / Atomic ARM / Restart Safety — PASS
- R3 Scheduler / Timing Contract — PASS
- C1 Domain/Storage/Timing checkpoint — PASS
- R4 Adapter Contract + T1 Adapter Migration — PASS
- R5 Generic BrowserBridge + Typed BrowserResult — PASS
- R6 Orchestrator / Error / Side-effect / Retry Migration — PASS
- C2 Adapter/Browser/Orchestrator checkpoint — PASS

Evidence:
- `verification/R1_DOMAIN_REVIEW.md`
- `verification/R2_STORE_RECOVERY_REVIEW.md`
- `verification/R3_SCHEDULER_REVIEW.md`
- `verification/C1_FOUNDATION_REVIEW.md`
- `verification/R4_ADAPTER_REVIEW.md`
- `verification/R5_BROWSER_BRIDGE_REVIEW.md`
- `verification/R6_ORCHESTRATOR_REVIEW.md`
- `verification/C2_ADAPTER_BROWSER_ORCHESTRATOR_REVIEW.md`

## R6 result

The active execution path now follows the approved contracts:

```text
ArmedRunSnapshot
  -> AdapterPlan
  -> Generic BrowserBridge / BrowserResult
  -> AdapterStepResult
  -> Core ErrorInfo + SideEffectStatus + LocalStore policy
```

Key safety behavior now enforced:
- DRAFT -> TESTED before ARM or TEST execution
- LIVE and TEST snapshots are distinct
- irreversible checkout request dispatches at most once automatically
- legacy task retry fields are ignored by forward orchestration
- transport/no-response after irreversible dispatch => TRANSPORT_AMBIGUOUS / no replay
- 403/429/server rejection => stop; no alternate endpoint/replay
- 2xx contract mismatch => AMBIGUOUS / no replay
- confirmed checkout + navigation failure preserves current-run checkout identifier
- recovery can reopen the existing checkout without a second create-checkout request
- duplicate execution signals cannot dispatch a second irreversible action
- successful automation stops at WAITING_MANUAL, not PAID
- legacy T1 browser facade removed from active path

The first R6 CI revealed R2/R3 regression tests that still assumed DRAFT -> ARM. Those tests were aligned to the already-approved TESTED-before-ARM state machine while preserving their original storage/scheduler assertions. Full CI then passed.

## C2 result

Status: **PASS**

C2 confirms:
- site facts remain adapter-owned
- BrowserBridge is site-agnostic
- exact-origin/credential protections remain
- Core has no site endpoint/payload/locator literals on the forward path
- ambiguity cannot create an automatic replay
- confirmed-side-effect recovery reuses only the known current-run checkout

No unresolved C2 BLOCKER or MAJOR finding remains.

## Next implementation slice

**R7 — Typed / Redacted / Bounded Observability**

R7 must replace the legacy Event JSONL path with typed RunEvent persistence that:
- assigns runId + sequence + state + stage + code + sideEffect
- admits only safe allow-listed detail fields
- redacts/blocks secret and PII keys before persistence
- never persists BrowserResult response bodies
- keeps event storage bounded/rotated
- records safe timing metrics needed for rehearsal analysis

Do not begin R8 API hardening inside R7.

## LIVE blockers remain

- G12 Signature Edition `shippingType` unverified
- G26 >=5 Windows timing rehearsals / evidence-based maxLatenessMs pending
- G27 Windows dedicated Chrome session persistence/profile ownership pending
- G28 near-live target contract freshness pending
- safe checkout/navigation/manual-handoff rehearsal pending
- rehearsal log redaction inspection pending

Coding completion never overrides these LIVE gates.
