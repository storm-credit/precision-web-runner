# Implementation Reconciliation v1

## Purpose

This document reconciles the existing Architecture Spike with the approved Deep Design baseline **without changing runtime code**.

The existing implementation is evidence that the general approach is feasible. It is not the design authority. The design documents under `design/` are the authority for the next implementation phase.

## Classification vocabulary

- **KEEP** — concept/implementation is aligned enough to retain with only cosmetic or test updates.
- **KEEP + HARDEN** — core idea is correct, but missing safety/contract details must be added.
- **CHANGE** — file remains, but responsibilities/data model/API must materially change.
- **MOVE** — logic belongs in another layer according to the component contract.
- **DELETE** — concept/field/control conflicts with the Deep Design and should not survive implementation reconciliation.

No classification below authorizes code changes yet.

---

## Executive reconciliation result

### KEEP / keep as foundation

- Python 3.11 local process and simple packaging
- dedicated Playwright persistent Chrome profile
- browser worker single-thread ownership pattern
- same-origin page-context `fetch`
- localhost control surface
- T-30s prewarm concept
- monotonic waiting concept
- execution lock concept
- dynamic `checkoutNumber` extraction
- T1-specific adapter module separation as a starting point
- manual final-payment boundary
- Concept 02 light responsive dashboard direction
- fail-closed response parsing as a starting principle

### Must materially change before live approval

1. mutable `TaskConfig` cannot act as the armed run; add immutable `ArmedRunSnapshot`
2. core data model is T1-specific; move product fields to adapter variables
3. current state model lacks `DRAFT`, `TESTED`, and `SUCCEEDED`
4. generic retry fields/loop conflict with per-step side-effect policy
5. scheduler does not emit clock-discontinuity signals or full timing telemetry
6. BrowserWorker contains T1 adapter logic; BrowserBridge must become generic
7. error results do not carry stable code/stage/side-effect/next-action semantics
8. event logging lacks runId, sequence, state, step, code, side-effect classification, redaction enforcement, and retention bounds
9. Local Store does not atomically persist runId + immutable snapshot before scheduling
10. restart/recovery behavior is not implemented
11. web API does not implement the required command response contract and allows non-local bind by warning only
12. TEST and LIVE are not first-class separated modes in the dashboard
13. UI does not show complete ARM blocker reasons or side-effect-aware recovery actions
14. live `maxLatenessMs` is hardcoded as a spike value rather than snapshot configuration derived from rehearsal evidence
15. adapter version/evidence status/health are not represented

---

## File-by-file inventory

### `src/precision_runner/__init__.py`
**Verdict: KEEP**

Reason:
- package identity only
- no known design conflict

Later checks:
- version should match reconciled release version

### `src/precision_runner/__main__.py`
**Verdict: KEEP**

Reason:
- thin CLI/module entrypoint is appropriate

Later checks:
- should continue delegating to the local control application only

### `src/precision_runner/models.py`
**Verdict: CHANGE MAJOR**

Useful spike evidence:
- timezone-aware target parsing
- typed dataclass validation
- explicit enum state concept

Required changes:
- replace T1-shaped core `TaskConfig` with generic `TaskDefinition`
- move `inventory_item_id`, `amount`, `currency_code`, `shipping_type`, `shipping_type_verified`, consent/payment adapter values into typed adapter variables/policy
- add explicit `mode = TEST | LIVE`
- add `adapterId` + `adapterVersion`
- add `runId`
- add immutable `ArmedRunSnapshot`
- snapshot must contain target instant, timezone, adapter version, validated variables, prewarm lead, `maxLatenessMs`, manual-boundary policy, and version/hash identity
- state vocabulary must align with `DRAFT -> TESTED -> ARMED -> PREWARMING -> RUNNING -> WAITING_MANUAL -> SUCCEEDED`, plus FAILED/CANCELLED
- add stable error/event types rather than raw strings

DELETE from generic core model:
- generic `max_retries` and `retry_delay_ms` applying to the whole task
- default T1 product ID/price/shipping values as core defaults
- `READY` as the only pre-arm state; it may remain a visual alias only if mapped explicitly

Design references:
- `design/COMPONENT_CONTRACTS.md`
- `design/STATE_MACHINE.md`
- `design/ERROR_POLICY.md`
- `design/ADAPTER_SPEC.md`

### `src/precision_runner/timing.py`
**Verdict: KEEP + HARDEN**

Useful spike evidence:
- scheduling occurs outside the browser
- target delay converts into a monotonic deadline
- cancellation is checked during wait

Required changes:
- Scheduler becomes an explicit component returning `PREWARM_DUE | TARGET_DUE | CANCELLED | LATE | CLOCK_DISCONTINUITY`
- capture wall + monotonic samples at ARM
- support explicit prewarm deadline
- detect sleep/wake / clock discontinuity
- return/record scheduler wake timestamp and lateness
- use snapshot `maxLatenessMs`; remove service hardcoded `2000ms`
- expose timing measurements required by `TIMING_DESIGN.md`

Do not add intentional early dispatch offsets.

### `src/precision_runner/t1_adapter.py`
**Verdict: CHANGE MAJOR, KEEP EVIDENCE**

Useful spike evidence:
- T1 origin restriction
- observed checkout endpoint and headers
- request-body construction
- current-run checkoutNumber parsing
- semantic agreement text
- HTTP rejection is currently fail-closed

Required changes:
- implement Adapter Contract v1 identity/version/origin patterns/capabilities
- define typed variable schema with evidence status `VERIFIED | INFERRED | UNKNOWN`
- expose `validate`, `buildPreflight`, `buildExecution`, `parse`, `locators`, `manualCheckpoint`
- each step declares `effect = NONE | IRREVERSIBLE`
- parsing returns semantic status + side-effect status, not a generic `retryable` boolean
- adapter health/version must become `UNVERIFIED` when target contract changes
- Signature `shippingType` remains UNKNOWN and blocks LIVE

KEEP:
- dynamic checkoutNumber must come from current response only
- do not merge cart `paymentOptionId` into direct checkout without evidence

DELETE:
- adapter-level implication that a generic `retryable` boolean can authorize checkout replay

### `src/precision_runner/browser_worker.py`
**Verdict: CHANGE MAJOR / MOVE T1 LOGIC**

Useful spike evidence:
- Playwright objects owned by one worker thread
- dedicated persistent Chrome profile
- manual visible browser
- same-origin page-context fetch is feasible
- semantic text lookup is better than generated class hashes

Required changes:
- rename/shape responsibility as generic `BrowserBridge`
- MOVE T1 endpoint/payload/locator knowledge out of BrowserBridge into T1 Adapter plans
- accept only allow-listed typed `BrowserCommand` / request specs
- enforce expected origin on navigation and same-origin request
- return typed `BrowserResult {ok, category, httpStatus, finalUrl, safeData, reason}`
- bound/redact any body text before it can leave bridge diagnostics
- detect profile-lock / browser ownership conflicts distinctly
- verify expected session/origin markers in preflight path
- define browser crash/disconnect category for pre/post-side-effect error policy
- support reuse of known checkout URL after confirmed checkout without creating a second checkout

DELETE:
- hardwired references to `T1Adapter` inside the generic browser execution layer
- generic arbitrary action-string dispatch as a future public recipe surface; internal typed dispatch is acceptable

### `src/precision_runner/service.py`
**Verdict: CHANGE CRITICAL**

Useful spike evidence:
- one RunnerService orchestration point
- local execution lock
- arm/prewarm/dispatch/manual-handoff structure
- task edits blocked while active
- no auto-payment authorization
- no HTTP replay in current live defaults

Critical gaps:

1. **Immutable snapshot**
   - current scheduled thread reads `self.task`
   - Deep Design requires atomically persisted immutable `ArmedRunSnapshot`

2. **Run identity**
   - no runId-scoped state/events/snapshot

3. **State machine**
   - current READY/ARMED/PREWARMING/RUNNING/WAITING_MANUAL/FAILED/CANCELLED does not implement DRAFT/TESTED/SUCCEEDED contract

4. **Retry semantics**
   - `_create_checkout_with_retry()` remains a generic replay loop even though live max retries are forced to zero
   - replace with per-step Error Policy; irreversible checkout has no automatic replay

5. **Transport ambiguity**
   - current transport failure becomes a generic error; must become `TRANSPORT_AMBIGUOUS` once an irreversible request may have left the client

6. **Navigation after side effect**
   - confirmed checkout + navigation failure must preserve current checkoutNumber and must not permit creating another checkout automatically

7. **Atomic persistence / restart**
   - no persisted active snapshot/state/recovery marker
   - restart from ARMED/RUNNING must follow fail-closed recovery contract

8. **Timing telemetry**
   - only dispatchAt is logged; required timing fields are missing
   - hardcoded 2-second late cutoff is spike-only

9. **Event contract**
   - raw message/detail event model is insufficient

10. **Error contract**
   - stable code/stage/sideEffect/nextAction missing

KEEP conceptually:
- active execution lease
- prewarm flow
- manual checkpoint
- local-only orchestration

DELETE/replace:
- task-global retry loop/config
- silent fallback to default TaskConfig after persisted task parse failure; corrupted persisted safety data must be visible

### `src/precision_runner/webapp.py`
**Verdict: CHANGE MAJOR**

Useful spike evidence:
- small local control API is sufficient for POC
- default bind is `127.0.0.1`
- dashboard can operate without cloud backend

Required changes:
- POC must refuse non-loopback bind rather than only print a warning, unless a separately approved authenticated LAN mode exists
- mutating response contract must include accepted/currentState/runId/error code as designed
- reject unexpected cross-origin mutating requests / add local-origin checks appropriate to POC
- expose redacted status only
- distinguish TEST commands from LIVE ARM explicitly
- no direct generic endpoint editor

DELETE/restrict:
- unrestricted `--host` exposure for POC
- immediate checkout control as a generic live shortcut; if retained it must be TEST-only and follow the same safe test contract

### `src/precision_runner/static/index.html`
**Verdict: CHANGE MAJOR, KEEP DESIGN FOUNDATION**

KEEP:
- Concept 02 light cards
- responsive single-page control surface
- clear target/countdown/state presentation
- local manual-payment message
- structured event rendering direction

Required changes:
- always-visible TEST/LIVE badge
- LIVE ARM confirmation summary
- exact blocker list instead of relying only on disabled controls/errors
- adapter/version/validation health visible
- state UI aligned with DRAFT/TESTED/.../SUCCEEDED
- error panel shows stage/code/side-effect/next action
- RUNNING has no misleading cancel/undo
- AMBIGUOUS failures must not show generic retry
- known checkout after navigation failure should offer existing checkout recovery rather than new checkout
- first mobile viewport must prioritize connection/mode/target/time/state/one CTA/blocker
- form must be frozen against current ArmedRunSnapshot while armed

DELETE or redesign:
- `Checkout Test Now` as a loosely scoped advanced action; retain only if it is explicitly TEST mode and safe-item confirmed
- any UI field suggesting global retry settings

### `pyproject.toml`
**Verdict: KEEP + REVIEW**

KEEP:
- Python >=3.11
- setuptools packaging
- Playwright optional browser dependency
- console entrypoint

Later review:
- pin/update Playwright only after Windows rehearsal evidence
- add no new framework dependency unless it solves a demonstrated POC need

### `tests/test_models.py`
**Verdict: CHANGE / EXPAND**

KEEP useful assertions:
- timezone parsing
- shipping confirmation concept
- consent/payment policy validation

Required new coverage:
- TaskDefinition vs ArmedRunSnapshot immutability
- TEST/LIVE separation
- adapter version snapshotting
- state transitions
- corrupted storage behavior
- no task mutation affecting active run

### `tests/test_timing.py`
**Verdict: KEEP + EXPAND**

Required new coverage:
- PREWARM/TARGET signals
- max lateness
- cancellation
- clock discontinuity/sleep simulation
- monotonic snapshot logic
- telemetry calculation

### `tests/test_t1_adapter.py`
**Verdict: KEEP + EXPAND**

KEEP:
- checkout response extraction tests
- request shape tests where backed by evidence

Required new coverage:
- adapter identity/version/origin
- evidence status and LIVE blocking of UNKNOWN required variable
- side-effect classification
- 403/429/2xx-shape mismatch semantics
- no retry authorization from adapter
- dynamic checkout identifier scoped to current run

### New tests required by design
**Verdict: ADD LATER — NOT NOW**

Planned files/categories:
- state-machine transition/invariant tests
- service snapshot/atomic ARM tests
- irreversible ambiguity/no-replay tests
- confirmed-checkout navigation-recovery tests
- browser origin-guard tests
- profile-lock/duplicate-run tests
- event redaction/schema tests
- web API localhost/origin/command-contract tests
- UI TEST/LIVE and blocker behavior checks
- restart/recovery tests

### `scripts/setup_windows.ps1`
**Verdict: KEEP**

Reason:
- simple and appropriately local

Later hardening:
- verify Python 3.11+ explicitly
- report installed Playwright/Chrome versions for rehearsal evidence

### `scripts/run_windows.ps1`
**Verdict: KEEP**

Reason:
- explicitly binds to `127.0.0.1`
- simple deterministic startup

Later hardening:
- surface duplicate runner/port/profile ownership error clearly

### `scripts/preflight_windows.ps1`
**Verdict: CHANGE MAJOR**

KEEP:
- Python check
- Chrome discovery
- Windows Time query
- power-scheme display

Required changes:
- produce explicit PASS/BLOCKED results instead of informational output only
- verify time service/sync state sufficiently for gate evidence
- verify sleep/hibernate live-window condition or require explicit operator confirmation
- verify runner dependency import/version
- verify localhost-only configuration
- verify duplicate runner/profile ownership state where possible
- produce evidence usable by Go/No-Go checklist

### `.github/workflows/tests.yml`
**Verdict: KEEP + EXPAND AFTER RECONCILIATION**

KEEP:
- automatic install and unit tests

Later add:
- syntax/static validation of design-aligned modules as needed
- no CI network calls to T1 or payment systems

---

## Responsibility moves

```text
CURRENT SPIKE                       DESIGN TARGET

TaskConfig(T1 fields)        ->     TaskDefinition + adapterVariables
                                  + immutable ArmedRunSnapshot

RunnerState.READY            ->     DRAFT / TESTED domain states

BrowserWorker(T1 knowledge)  ->     BrowserBridge(generic commands)
                                   T1Adapter(builds plans/locators)

service retry loop           ->     Core ErrorPolicy per step/effect

raw Event(message/detail)    ->     RunEvent typed/redacted schema

service task.json only       ->     LocalStore task + atomic snapshot/run metadata

hardcoded late=2000ms        ->     snapshot.maxLatenessMs from rehearsal evidence

web host warning             ->     localhost-only enforcement for POC

Run Now                      ->     explicit TEST-mode safe action only
```

---

## Planned implementation order after coding is explicitly approved

This order minimizes unsafe partial states.

### R1 — Domain contracts first
- TaskDefinition
- ArmedRunSnapshot
- RunId
- Mode
- State machine
- Error/Event types

### R2 — Store + atomic ARM
- snapshot persistence
- run metadata
- restart inspection
- execution lease semantics

### R3 — Scheduler/timing
- monotonic deadlines
- prewarm/target signals
- discontinuity detection
- telemetry
- configurable max lateness

### R4 — Adapter Contract v1
- generic adapter plan types
- T1 adapter migration
- evidence status/version/health

### R5 — BrowserBridge
- generic typed commands
- origin guards
- structured safe results
- profile ownership errors

### R6 — Orchestrator/Error Policy
- deterministic state transitions
- no irreversible replay
- ambiguity handling
- confirmed-side-effect navigation recovery

### R7 — Observability
- typed event logger
- redaction before persistence
- bounded retention

### R8 — Local API
- localhost enforcement
- typed command results
- origin protection

### R9 — UI reconciliation
- TEST/LIVE separation
- blockers
- state/CTA rules
- side-effect-aware failure UI

### R10 — Windows gates and rehearsals
- preflight evidence
- safe flow rehearsal
- 5 timing rehearsals
- log inspection
- target contract freshness

No later reconciliation item should be implemented before its prerequisites merely to improve appearance or add features.

---

## KEEP / CHANGE / DELETE totals

At file level:
- KEEP or KEEP+HARDEN: entrypoints, timing foundation, packaging, Windows setup/run, existing test seeds, CI foundation
- CHANGE: models, adapter, browser bridge, service, web API, UI, Windows preflight, all test suites need expansion
- DELETE as whole file: **none**

At concept level, DELETE/replace:
- task-global retry policy
- retry loop applying to irreversible checkout
- T1 product fields in generic core model
- hardcoded dynamic/liveness assumptions
- non-local POC dashboard exposure by warning only
- loosely scoped immediate checkout control outside explicit TEST mode
- hidden mutable armed configuration

The architecture spike is therefore **salvageable but not live-authoritative**. Reconciliation should refactor contracts around the proven browser/session/checkout path rather than rewrite everything from zero.

---

## Reconciliation verdict

**DESIGN-TO-CODE INVENTORY: COMPLETE**

**RUNTIME CODE CHANGES: NOT STARTED**

**RECOMMENDATION: RECONCILE, DO NOT REWRITE FROM SCRATCH**

The highest-risk existing mismatches are `models.py` + `service.py`; they must be reconciled before any live confidence can be inferred from the current spike.