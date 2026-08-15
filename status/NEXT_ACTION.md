# Next Action

## Single next objective

**R6 — Orchestrator / Error / Side-effect / Retry Migration.**

R4/R5 forward contracts are ready. R6 migrates RunnerService onto them and removes the temporary legacy browser execution path.

## Read first

1. `status/CURRENT_STATUS.md`
2. `verification/R4_ADAPTER_REVIEW.md`
3. `verification/R5_BROWSER_BRIDGE_REVIEW.md`
4. `design/IMPLEMENTATION_READY_PLAN.md` — R6
5. `design/STATE_MACHINE.md`
6. `design/ERROR_POLICY.md`
7. `design/COMPONENT_CONTRACTS.md` — RunnerService
8. `design/ADAPTER_SPEC.md`
9. `harness/IMPLEMENTATION_GATE_CHECKLIST.md`

## R6 Gap IDs

- G03 full state semantics
- G04 per-step side-effect retry policy
- G05 TRANSPORT_AMBIGUOUS handling
- G06 confirmed-checkout navigation recovery
- G13 stable error shape
- G20 TEST/LIVE intent at orchestrator boundary
- completes R4/R5 integration

## Tests first

Specify tests for:
- LIVE ARM builds/validates adapter snapshot and blocks UNKNOWN shippingType
- irreversible create_checkout is dispatched at most once per run
- transport failure during irreversible request => AMBIGUOUS / no replay
- 403/429/server rejection => terminal, no alternate request or retry
- 2xx missing checkoutNumber => CONTRACT_MISMATCH/AMBIGUOUS / no replay
- confirmed checkoutNumber + navigation failure preserves number and never creates a second checkout
- duplicate execution lease blocks second dispatch
- cancel semantics before vs after irreversible dispatch
- WAITING_MANUAL is not PAID/SUCCEEDED by implication
- TEST and LIVE run snapshots stay distinct
- browser/action plan is obtained from adapter; RunnerService has no T1 endpoint/payload/locator literals

## Allowed scope

- `src/precision_runner/service.py`
- adapter/browser integration seams
- orchestrator/error tests
- removal of legacy browser facade from active execution path; delete it if no longer referenced
- narrow model additions only if required by approved ErrorInfo/state contracts

No UI/API/observability overhaul, second adapter, remote control, or final payment authorization belongs in R6.

## Completion condition

R6 ends when:
- service consumes AdapterPlan + BrowserResult directly
- irreversible POST generic retry loop is gone
- side-effect ambiguity is explicit
- confirmed checkout navigation recovery cannot duplicate checkout creation
- temporary T1 browser facade is unused/deletable
- full CI passes
- R6 review recorded
- C2 review of R4-R6 passes

Then R7 becomes eligible.
