# R6 Orchestrator / Error / Side-effect / Retry Review

## Verdict

**R6 SLICE: PASS.**

This is the critical orchestration convergence verdict. It does not approve LIVE use.

## Gap coverage

- G03 full state semantics: operational path now requires DRAFT -> TESTED -> ARM/RUN and preserves WAITING_MANUAL
- G04 per-step side-effect retry policy: irreversible generic retry loop removed
- G05 TRANSPORT_AMBIGUOUS: explicit ErrorInfo + no replay
- G06 confirmed checkout + navigation recovery: safe dynamic variable persisted and existing checkout reopen path added
- G13 stable ErrorInfo-compatible failure data: implemented in RunnerService status/failure path
- G20 TEST/LIVE intent at orchestrator boundary: snapshots are distinct and LIVE ARM requires tested state
- completes R4 AdapterPlan and R5 BrowserResult integration

## Tests-first evidence

R6-specific tests were committed before the orchestrator implementation:
- `tests/test_orchestrator_safety.py`
- `tests/test_store_safe_variables.py`

They verify:
- LIVE ARM blocks UNKNOWN Signature shippingType
- preflight success creates TESTED state before ARM/run
- irreversible transport failure => TRANSPORT_AMBIGUOUS / AMBIGUOUS / exactly one dispatch
- 403/429/5xx server rejection => terminal, no replay
- 2xx without checkoutNumber => CONTRACT_MISMATCH / AMBIGUOUS / no replay
- confirmed checkout + navigation failure preserves checkoutNumber and never creates a second checkout
- existing confirmed checkout can be reopened with navigation only
- successful automation stops at WAITING_MANUAL, never PAID by implication
- TEST run snapshot remains TEST
- duplicate execution lease blocks the duplicate signal without failing the authoritative run
- service source contains no T1 endpoint/payload/locator literals and no generic retry loop
- current-run safe dynamic variables round-trip through LocalStore

## Implementation result

`RunnerService` now consumes the approved forward contracts directly:

```text
TaskDefinition / ArmedRunSnapshot
       -> Adapter validation / AdapterPlan
       -> BrowserBridge BrowserResult
       -> AdapterStepResult
       -> Core ErrorInfo / state / LocalStore policy
```

The service no longer constructs:
- target endpoint paths
- site payload field names
- site locator text
- checkout response field names

Those remain adapter-owned.

## Irreversible action invariant

Create-checkout execution contains exactly one BrowserBridge request call and no loop.

Legacy `TaskConfig.max_retries` can still exist for compatibility, but RunnerService does not read it. Setting it to a nonzero value does not cause an irreversible replay.

Outcome policy:
- no HTTP result / transport failure after irreversible dispatch => `TRANSPORT_AMBIGUOUS`, sideEffect=AMBIGUOUS, active run preserved
- adapter/server rejection => `SERVER_REJECTION` or `RATE_LIMITED`, sideEffect=NONE, terminal run archived
- success-shaped response missing required dynamic variable => `CONTRACT_MISMATCH`, AMBIGUOUS, active run preserved
- confirmed dynamic checkout + navigation failure => `NAVIGATION_AFTER_SIDE_EFFECT`, CONFIRMED, checkoutNumber preserved

No automatic replay is available for any of these irreversible outcomes.

## Confirmed-side-effect recovery

The current-run dynamic navigation variable is persisted in the active-run record as `safe_variables`.

`open_existing_checkout()`:
- requires an active immutable snapshot
- requires the confirmed current-run checkout number
- executes only the adapter-declared navigation step
- never invokes the irreversible create-checkout step
- returns to WAITING_MANUAL on successful recovery navigation

## State semantics

Forward user flow now distinguishes:
- DRAFT after edit/start
- TESTED after successful safe preflight
- ARMED for scheduled LIVE snapshot
- PREWARMING
- RUNNING only around irreversible execution
- WAITING_MANUAL at manual payment boundary
- FAILED / CANCELLED

The runner does not label checkout creation or payment UI opening as PAID.

## R2/R3 regression-test adjustment

The first R6 CI exposed an expected contract evolution: older R2/R3 tests directly called `arm()` from DRAFT because TESTED was not operationally enforced yet.

Those regression tests were updated to set the state to TESTED before exercising their actual subject:
- R2 storage-before-scheduler behavior
- R3 snapshot-to-scheduler fidelity

Their original safety assertions remain unchanged. This is alignment to the already-approved state machine, not a scope/design change.

## Legacy browser facade removal

`legacy_t1_browser_facade.py` has been deleted.
`browser_worker.py` is now only a compatibility alias to generic BrowserBridge.
The active execution path no longer passes through a T1-specific browser layer.

## Verification evidence

GitHub Actions run `31901135861` completed successfully:
- package install: PASS
- full `python -m unittest discover -s tests -v`: PASS

## Security / safety review

PASS:
- exact-origin BrowserBridge remains authoritative
- no credential/cookie export
- no server restriction bypass
- no rate-limit evasion
- no automatic irreversible replay
- no guessed dynamic checkout identifier
- final payment/card/OTP/3DS authorization remains outside automation
- UNKNOWN Signature shippingType still blocks LIVE execution planning

## Known deferrals

- R7 typed/redacted/bounded EventLogger replaces legacy Event JSONL persistence
- R8 API contract/origin protections
- R9 UI state/confirmation/blocker mapping
- R10 Windows/browser/timing/target evidence

## Next action

Run Checkpoint C2 across R4-R6. R7 becomes eligible only after C2 PASS.
