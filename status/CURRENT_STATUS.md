# Current Status

## Phase

**CONTROLLED IMPLEMENTATION — R1-R5 COMPLETE; R6 NEXT.**

Implementation proceeds one approved R-slice at a time with tests/checks first. LIVE remains **NO-GO** until every mandatory Go/No-Go row passes.

## Completed and reviewed

- R1 Domain Contracts — PASS
- R2 Local Store / Atomic ARM / Restart Safety — PASS
- R3 Scheduler / Timing Contract — PASS
- C1 Domain/Storage/Timing checkpoint — PASS
- R4 Adapter Contract + T1 Adapter Migration — PASS
- R5 Generic BrowserBridge + Typed BrowserResult — PASS

Evidence:
- `verification/R1_DOMAIN_REVIEW.md`
- `verification/R2_STORE_RECOVERY_REVIEW.md`
- `verification/R3_SCHEDULER_REVIEW.md`
- `verification/C1_FOUNDATION_REVIEW.md`
- `verification/R4_ADAPTER_REVIEW.md`
- `verification/R5_BROWSER_BRIDGE_REVIEW.md`

## R5 result

The forward browser layer is now site-agnostic:
- BrowserBridge imports no T1 adapter
- exact origin/open/request/navigation guards
- same-origin credentials only
- Cookie/Authorization/Set-Cookie injection blocked
- typed BrowserResult / BrowserResultCategory
- bounded transient response body
- declarative RequestSpec/NavigationSpec execution
- semantic locator check/click only
- duplicate-profile launch classification foundation

A temporary `legacy_t1_browser_facade.py` preserves the pre-R6 RunnerService action surface so the intermediate main branch remains usable. It is explicitly a compatibility quarantine, not a new architecture contract.

## Next implementation slice

**R6 — Orchestrator / Error / Side-effect / Retry Migration**

R6 is the critical convergence slice. It must:
- make RunnerService consume AdapterPlan + BrowserResult directly
- remove the legacy T1 browser facade from the execution path
- enforce full state semantics
- remove task-global/generic irreversible retry behavior
- model TRANSPORT_AMBIGUOUS explicitly
- distinguish confirmed checkout + navigation failure from ambiguous checkout creation
- keep current checkoutNumber recovery scoped to current run
- expose stable ErrorInfo-compatible failure data
- preserve TEST/LIVE intent boundary

After R6 passes, run Checkpoint C2 across R4-R6 before R7.

## LIVE blockers remain

- G12 Signature Edition `shippingType` unverified
- G26 >=5 Windows timing rehearsals / evidence-based maxLatenessMs pending
- G27 Windows dedicated Chrome session persistence/profile ownership pending
- G28 near-live target contract freshness pending
- safe checkout/navigation/manual-handoff rehearsal pending
- log-redaction inspection pending

Coding completion never overrides these LIVE gates.
