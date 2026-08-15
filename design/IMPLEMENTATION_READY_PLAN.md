# Implementation-Ready Plan v1

## Status

**PLANNING ONLY — NO RUNTIME CODE IS AUTHORIZED BY THIS DOCUMENT.**

This plan is the final bridge between the approved Deep Design and future coding. It converts the reconciliation inventory and Gap Matrix into ordered, testable implementation slices.

Coding starts only after explicit user approval of this plan.

## Planning invariants

Every slice must:
1. cite the design contract it implements
2. close named Gap IDs
3. define tests/checks before runtime edits
4. make the smallest sufficient change
5. run regression tests
6. review changed files against security/site boundaries
7. update status/deviations if reality differs
8. stop if a new BLOCKER appears

No slice may add a feature outside the POC.

---

# Dependency graph

```text
R1 Domain Contracts
   |
   +--> R2 Local Store / Atomic ARM / Recovery
   +--> R3 Scheduler / Timing
   +--> R4 Adapter Contract + T1 Migration
              |
              +--> R5 Generic BrowserBridge
                         |
R2 + R3 + R4 + R5 ------+--> R6 Orchestrator / Error Policy
                              |
                              +--> R7 Observability
                              |
                              +--> R8 Local Control API
                                      |
                                      +--> R9 Concept 02 UI

R1-R9 verified
   |
   +--> R10 Windows Preflight + Rehearsal + Live Evidence
```

R10 cannot compensate for an unfinished R1-R9 contract.

---

# R1 — Domain Contracts

## Goal
Replace prototype-shaped core models with the approved generic domain contract before changing orchestration behavior.

## Gaps
- G01 immutable ArmedRunSnapshot
- G03 state vocabulary
- G13 stable error shape foundation
- G14 typed event shape foundation
- G20 TEST/LIVE first-class mode foundation

## Design authority
- `design/COMPONENT_CONTRACTS.md`
- `design/STATE_MACHINE.md`
- `design/ERROR_POLICY.md`
- `design/OBSERVABILITY_SPEC.md`

## Allowed runtime files
- `src/precision_runner/models.py`
- optional new narrowly scoped domain module only if it reduces coupling
- `tests/test_models.py`
- new domain/state tests

## Planned changes
- define `RunMode(TEST, LIVE)`
- define complete `RunnerState`
- define generic `TaskDefinition`
- adapter-specific values stored as typed `adapter_variables`
- define immutable/frozen `ArmedRunSnapshot`
- define `run_id`, adapter id/version, target instant, prewarm lead, max lateness, manual-boundary policy
- define stable ErrorInfo/ErrorCode/SideEffectStatus types
- define RunEvent schema types
- remove task-global retry fields from generic core domain
- remove T1 product defaults from generic TaskDefinition

## Tests first
- snapshot cannot be mutated
- editing TaskDefinition after snapshot creation does not change snapshot
- TEST/LIVE parses and serializes distinctly
- state enum contains design vocabulary
- adapter variables round-trip without leaking into generic attributes
- naive/invalid time handling follows explicit rule

## Completion evidence
- all R1 tests pass
- no T1 endpoint/product field is a top-level core-domain invariant
- no runtime behavior beyond model construction changed unintentionally

## Rollback boundary
Single model/domain commit can be reverted before R2 begins.

---

# R2 — Local Store, Atomic ARM, Restart Safety

## Goal
Make ARM a persisted, run-scoped safety boundary rather than an in-memory flag.

## Gaps
- G02 atomic runId + snapshot
- G16 restart fail-closed recovery
- supports G01

## Design authority
- `design/COMPONENT_CONTRACTS.md` Local Store
- `design/STATE_MACHINE.md` restart behavior
- `design/SECURITY_MODEL.md`

## Allowed files
- new `src/precision_runner/store.py` or equivalent narrow module
- minimal `service.py` integration needed for persistence boundary
- store/recovery tests

## Planned changes
- persist editable TaskDefinition separately from ArmedRunSnapshot
- atomically create runId + immutable snapshot before scheduling
- persist active run state/last safe known stage
- storage failure blocks ARM
- startup inspects prior active state
- prior RUNNING/ambiguous state -> `RECOVERY_REQUIRED` failure/manual inspection, never silent replay
- prior safely-cancelled/terminal state remains historical

## Tests first
- ARM persistence atomicity
- storage write failure prevents scheduling
- restart from RUNNING does not dispatch
- restart from ambiguous state does not dispatch
- active snapshot survives process restart as immutable data
- corrupt store is visible failure, not silent default substitution

## Completion evidence
- no scheduler thread starts before snapshot persistence succeeds
- recovery tests prove no hidden replay

## Rollback boundary
Store format is versioned before any live data is trusted.

---

# R3 — Scheduler and Timing Contract

## Goal
Turn the spike wait helper into the explicit Scheduler contract with measurable timing and discontinuity behavior.

## Gaps
- G07 SchedulerSignal / clock discontinuity
- G08 explicit maxLatenessMs
- prepares G26 live timing evidence

## Design authority
- `design/TIMING_DESIGN.md`
- `design/COMPONENT_CONTRACTS.md` Scheduler

## Allowed files
- `src/precision_runner/timing.py`
- optional `scheduler.py` if needed to keep responsibilities clear
- `tests/test_timing.py`

## Planned changes
- wall+monotonic sample captured at ARM
- derive target and prewarm monotonic deadlines
- emit typed PREWARM_DUE/TARGET_DUE/CANCELLED/LATE/CLOCK_DISCONTINUITY signals
- record scheduler wake timestamp/lateness
- use snapshot `max_lateness_ms`
- remove hardcoded 2000ms from orchestrator
- detect simulated sleep/wake/clock discontinuity
- no intentional early dispatch offset

## Tests first
- prewarm deadline ordering
- target signal once only
- cancel before target
- late signal when threshold exceeded
- discontinuity simulation fails closed
- target already past rejected

## Completion evidence
- deterministic unit tests with injectable/fake clock where practical
- no target-site/browser dependency in scheduler tests

---

# R4 — Adapter Contract v1 + T1 Migration

## Goal
Make T1 a real implementation of a generic adapter contract, not logic shared across core/browser layers.

## Gaps
- G11 adapter identity/version/evidence health
- supports G09 browser/adapter separation
- G12 remains a LIVE evidence blocker, not a code gap to guess away

## Design authority
- `design/ADAPTER_SPEC.md`
- `docs/T1_EVIDENCE.md`
- `design/ERROR_POLICY.md`

## Allowed files
- new generic adapter types/module
- `src/precision_runner/t1_adapter.py`
- `tests/test_t1_adapter.py`
- new adapter-contract tests

## Planned changes
- adapter id/version/origin/url pattern/capabilities
- typed variable definitions + evidence state
- `validate()`
- side-effect-free `build_preflight()`
- `build_execution()` with effect classification
- semantic `parse()` result
- ordered semantic locators
- manual checkpoint spec
- exact allowlisted request path/method/header/body contract
- health state UNVERIFIED when critical evidence is unknown/stale

## T1 rules
- current dynamic checkoutNumber extraction stays
- `paymentOptionId` not added to direct checkout without evidence
- Signature shippingType remains UNKNOWN until independently verified
- UNKNOWN critical live field blocks LIVE ARM

## Tests first
- wrong origin rejected
- adapter version recorded
- UNKNOWN required live variable blocks LIVE
- 403 -> rejected/no retry semantics
- 429 -> rate limited/stop semantics
- 2xx missing checkoutNumber -> contract mismatch/ambiguous semantics
- current-run dynamic identifier only

## Completion evidence
- T1 knowledge no longer required by generic domain/scheduler/browser modules

---

# R5 — Generic BrowserBridge

## Goal
Keep the proven Playwright/persistent-profile approach while removing T1 coupling and hardening origin/profile/session boundaries.

## Gaps
- G09 generic BrowserBridge
- G10 typed safe BrowserResult
- G25 profile ownership/lock diagnosis (code half; Windows evidence later)

## Design authority
- `design/COMPONENT_CONTRACTS.md` BrowserBridge
- `design/BROWSER_LIFECYCLE.md`
- `design/SECURITY_MODEL.md`

## Allowed files
- `src/precision_runner/browser_worker.py` (rename only if migration cost is justified)
- browser-bridge tests/mocks

## Planned changes
- retain single worker thread ownership pattern
- accept typed allowlisted browser commands/request specs
- no import/reference to T1Adapter
- enforce expected origin before credentialed same-origin request
- navigation origin/path guard from adapter plan
- typed BrowserResult with safe bounded data
- distinguish profile-lock, browser-crash, timeout, navigation, HTTP response categories
- no cookie export API
- semantic locator execution only
- reuse known checkout URL after confirmed side effect when instructed by orchestrator

## Tests first
- unexpected origin request blocked before browser call
- T1 symbols absent from generic BrowserBridge dependency graph
- raw cookie/export action unavailable
- profile lock maps to stable category
- bounded result body/safe data behavior

## Completion evidence
- BrowserBridge can be unit-tested with a fake adapter plan and no T1 constants

---

# R6 — Orchestrator, State Machine, Side-Effect Error Policy

## Goal
Rebuild RunnerService behavior around immutable snapshots, typed scheduler/browser/adapter results, and no irreversible replay.

## Gaps
- G04 per-step retry
- G05 TRANSPORT_AMBIGUOUS
- G06 confirmed checkout navigation recovery
- G03 state transition enforcement
- G16 recovery integration
- duplicate execution safety

## Design authority
- `design/STATE_MACHINE.md`
- `design/ERROR_POLICY.md`
- `design/SEQUENCE_FLOWS.md`
- `design/COMPONENT_CONTRACTS.md`

## Allowed files
- `src/precision_runner/service.py`
- optional narrow state/error-policy module
- service/state/failure tests

## Planned changes
- orchestrator reads only ArmedRunSnapshot for active run
- formal transition function validates legal transitions
- one irreversible lease per run
- preflight safe retries only where adapter says effect NONE and policy permits
- checkout POST automatic replay = zero
- post-send/no-response -> TRANSPORT_AMBIGUOUS
- known checkout + navigation failure persists identifier and offers same-checkout recovery only
- cancellation allowed only before irreversible dispatch
- WAITING_MANUAL reached only after checkpoint criteria
- POC `SUCCEEDED` semantics explicitly mean automation handoff complete, not payment success

## Tests first
- illegal transitions rejected
- duplicate ARM/run rejected
- cancellation before dispatch works
- cancellation after dispatch cannot claim undo
- ambiguous transport produces no second checkout call
- 403/429 produce one dispatch and stop
- missing checkoutNumber produces no replay
- confirmed checkout navigation failure never calls checkout again
- restart/recovery path does not replay

## Completion evidence
- fake BrowserBridge call-count assertions prove irreversible POST maximum once per run

---

# R7 — Observability, Redaction, Retention

## Goal
Make every run reconstructable without persisting account/session/payment secrets.

## Gaps
- G14 typed RunEvent/redaction
- G15 bounded retention

## Design authority
- `design/OBSERVABILITY_SPEC.md`
- `design/SECURITY_MODEL.md`

## Allowed files
- new event logger/redactor module
- Local Store event integration
- service integration
- observability tests

## Planned changes
- eventId/runId/sequence/state/stage/step/level/code/message/sideEffect/safeDetail
- allowlist safe details
- deny/redact secret/PII keys before persistence
- no raw request/response dump in persisted event
- bounded file/record retention
- timing metrics recorded as safe fields

## Tests first
Use fixtures containing:
- Cookie
- Authorization
- token/session
- email/phone/address
- card/OTP/password

Assert none persist.

## Completion evidence
- persisted rehearsal-like fixture can reconstruct state path and timing without secret fields

---

# R8 — Local Control API Hardening

## Goal
Expose only the approved localhost command surface with typed command results.

## Gaps
- G17 localhost enforcement
- G18 mutating origin protection
- G19 command response contract

## Design authority
- `design/COMPONENT_CONTRACTS.md` Local Control API
- `design/SECURITY_MODEL.md`

## Allowed files
- `src/precision_runner/webapp.py`
- API tests

## Planned changes
- refuse non-loopback bind in POC
- mutating commands validate local expected Origin/Host policy where applicable
- typed response: accepted/currentState/runId/error code/message
- status response remains redacted
- TEST vs LIVE commands explicit
- no arbitrary request/endpoint editor

## Tests first
- non-loopback startup rejected
- cross-origin mutation rejected
- GET status contains no secret fields
- command rejection returns stable safe code

## Completion evidence
- local API cannot be used as generic same-session request proxy

---

# R9 — Concept 02 UI Reconciliation

## Goal
Make user intent and live safety obvious before ARM while preserving the selected responsive visual direction.

## Gaps
- G20 TEST/LIVE separation
- G21 LIVE confirmation summary
- G22 blocker reasons
- G23 side-effect-aware failed CTA
- G24 mobile first-viewport hierarchy

## Design authority
- `design/UI_SPEC.md`
- `design/STATE_MACHINE.md`
- `design/ERROR_POLICY.md`

## Allowed files
- `src/precision_runner/static/index.html`
- UI behavior checks/manual responsive checks

## Planned changes
- always-visible TEST/LIVE badge
- explicit LIVE confirmation before ARM
- show adapter version/health
- show exact ARM blockers
- fields frozen for active snapshot
- state vocabulary aligned
- RUNNING no fake cancel
- FAILED CTA based on NONE/CONFIRMED/AMBIGUOUS
- known checkout recovery opens existing checkout only
- `Checkout Test Now` removed or converted to explicit TEST-only safe action
- 360px/narrow first viewport prioritizes readiness/mode/target/time/state/CTA/blocker

## Checks first
- scripted DOM/state fixtures if lightweight
- manual keyboard/focus check
- 360px, ~820px, desktop viewport checks
- no decorative dead controls

## Completion evidence
A first-time user can answer within 10 seconds:
- what will run
- TEST or LIVE
- when
- readiness/blocker
- what automation does
- where it stops

---

# R10 — Windows Preflight, Safe Rehearsal, Live Evidence

## Goal
Close environment/live evidence gaps after R1-R9 are reconciled and verified.

## Gaps
- G12 Signature shippingType evidence
- G25 profile ownership live evidence
- G26 timing rehearsals
- G27 session persistence
- G28 target contract freshness
- remaining Go/No-Go rows

## Design authority
- `verification/POC_GO_NO_GO.md`
- `docs/POC_RUNBOOK_2026-08-17.md`
- `design/TIMING_DESIGN.md`

## Allowed files after coding approval
- `scripts/preflight_windows.ps1`
- setup/run scripts only if evidence shows need
- runbook/evidence reports

## Script hardening
- explicit PASS/BLOCKED output
- Python/runtime version
- Chrome presence/version
- Windows time synchronization evidence
- power/sleep review evidence
- localhost binding check
- duplicate runner/profile ownership check where feasible

## Required manual evidence
- dedicated profile opens and persists T1 login across runner restart
- duplicate profile/runner attempt is blocked/clearly diagnosed
- exact Signature shippingType independently confirmed from exact product flow without making an unauthorized/early irreversible request
- current checkout contract rechecked near rehearsal/live time
- safe checkout -> dynamic checkout -> navigation -> manual handoff rehearsal
- no irreversible automatic replay observed
- rehearsal logs contain no secrets/PII
- at least 5 scheduled timing rehearsals
- select `maxLatenessMs` from evidence

## Completion evidence
Every mandatory row in `verification/POC_GO_NO_GO.md` is PASS.

If any required row is UNKNOWN, LIVE stays NO-GO.

---

# Cross-slice review checkpoints

## Checkpoint C1 — after R1-R3
Review:
- domain genericity
- snapshot immutability
- restart/storage/timing invariants

Do not proceed if active run configuration can mutate or scheduler safety is unclear.

## Checkpoint C2 — after R4-R6
Review:
- Core contains no T1-specific contract
- BrowserBridge contains no T1-specific contract
- irreversible action can be called at most once automatically
- ambiguity cannot lead to replay

This is the highest-risk checkpoint.

## Checkpoint C3 — after R7-R9
Review:
- no secret leakage
- local API cannot be remotely exposed accidentally
- UI matches actual state/error semantics
- TEST/LIVE intent is explicit

## Checkpoint C4 — R10 before LIVE
Use only `verification/POC_GO_NO_GO.md`. No subjective override.

---

# Proposed commit discipline

Prefer one reviewable commit/PR slice per R-number or smaller if needed.

Do not mix:
- domain redesign + UI redesign
- adapter migration + unrelated timing change
- live target evidence + speculative feature addition

Every PR description must include:
- R-slice
- Gap IDs
- design docs
- tests run
- remaining risks
- deviation entry if plan changed

---

# Final implementation-ready verdict

The project is ready to **present this plan for coding approval** when:
- R1-R10 mappings are internally coherent
- no new design BLOCKER is found
- no runtime file has been modified during planning

Current result: **PLAN COMPLETE FOR REVIEW; CODING NOT STARTED.**