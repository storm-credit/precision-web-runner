# Implementation Gap Matrix v1

This matrix translates Deep Design contracts into future implementation work. It is **not an implementation checklist authorization**; runtime stays frozen until coding is explicitly approved.

| ID | Design contract | Current spike | Gap | Priority | Future evidence |
|---|---|---|---|---|---|
| G01 | immutable ArmedRunSnapshot | service reads mutable `self.task` | active run can depend on mutable object | BLOCKER | snapshot immutability + persistence tests |
| G02 | atomic runId + snapshot before scheduler | task.json only | no run-scoped persisted safety state | BLOCKER | atomic ARM test, storage-failure test |
| G03 | DRAFT/TESTED/ARMED/PREWARMING/RUNNING/WAITING_MANUAL/SUCCEEDED | READY-centric subset | design state semantics incomplete | MAJOR | transition table tests |
| G04 | per-step side-effect retry policy | task-global retry fields + retry loop | generic replay construct exists | BLOCKER | ambiguity/no-replay tests |
| G05 | TRANSPORT_AMBIGUOUS semantics | generic transport error string | side effect ambiguity not modeled | BLOCKER | simulated post-send timeout test |
| G06 | confirmed checkout navigation recovery | navigation failure flows to FAILED | known checkout recovery not explicit | MAJOR | same-checkout navigation recovery test |
| G07 | SchedulerSignal + clock discontinuity | monotonic wait helper | no sleep/wake signal/telemetry | MAJOR | discontinuity + late-target tests |
| G08 | explicit snapshot maxLatenessMs | hardcoded 2000ms | rehearsal cannot set contract | MAJOR | timing config/telemetry tests |
| G09 | generic BrowserBridge | BrowserWorker imports T1Adapter | layer coupling | BLOCKER | origin/typed-command tests |
| G10 | BrowserResult typed safe output | dict/raw text internal result | category/safe-data contract missing | MAJOR | result schema/redaction tests |
| G11 | adapter identity/version/evidence health | simple T1Adapter class | no version/evidence status | MAJOR | adapter validation/version tests |
| G12 | Signature shippingType VERIFIED required | default STANDARD_DELIVERY + verified=false | exact live fact still unknown | LIVE BLOCKER | exact product evidence |
| G13 | stable error code/stage/sideEffect/nextAction | raw error strings | unsafe/unclear recovery UX | MAJOR | error-shape tests |
| G14 | typed RunEvent + redaction before persistence | Event(at, level, message, detail) | missing runId/state/code/sequence/redactor | BLOCKER | log schema + secret fixture tests |
| G15 | bounded log retention | unbounded JSONL append | long-term growth | MAJOR | rotation/size test |
| G16 | restart fail-closed recovery | service starts READY | active/ambiguous prior run forgotten | BLOCKER | restart from ARMED/RUNNING tests |
| G17 | localhost-only POC | default localhost, alternate host warns | accidental LAN exposure possible | MAJOR | non-loopback startup rejection test |
| G18 | local mutating origin protection | no origin/CSRF-style validation | local browser page could potentially trigger commands | MAJOR | cross-origin mutation rejection test |
| G19 | command API returns accepted/state/runId/error code | generic ok/data/error | contract incomplete | MINOR/MAJOR | API contract tests |
| G20 | TEST vs LIVE explicit | no first-class mode | dangerous action context ambiguous | BLOCKER | mode transition/UI tests |
| G21 | LIVE ARM confirmation summary | absent | user intent snapshot not explicit | MAJOR | UI behavior test/manual check |
| G22 | visible ARM blocker reasons | partial validation/errors | disabled state not fully explained | MAJOR | blocker rendering checks |
| G23 | side-effect-aware failed CTA | generic error display | ambiguous outcome recovery unsafe | MAJOR | UI state fixture checks |
| G24 | all mobile first-viewport priorities | responsive layout exists | mode/blocker/one-CTA hierarchy incomplete | MINOR | 360px manual/screenshot check |
| G25 | profile ownership/lock diagnosis | generic launch failure | duplicate owner not distinguished | MAJOR | Windows duplicate profile rehearsal |
| G26 | live timing evidence >=5 rehearsals | not measured | max lateness unknown | LIVE BLOCKER | rehearsal report |
| G27 | T1 session persistence rehearsal | not performed on target Windows PC | live session reliability unknown | LIVE BLOCKER | restart/login persistence rehearsal |
| G28 | target contract freshness | old observed contract only | site may change before live | LIVE BLOCKER | near-live harmless contract check |

## Gate interpretation

### Blocks coding reconciliation start
Only if design itself is unresolved. Current design blocker count: **0**.

### Blocks live use
G12, G26, G27, G28 and every mandatory Go/No-Go row remain blocking until evidence exists.

### Highest implementation-risk cluster
1. G01/G02/G03/G04/G05/G16 — state, snapshot, ambiguity, recovery
2. G09/G10/G11 — browser/adapter boundary
3. G13/G14 — error and observability contract
4. G20/G21/G22/G23 — TEST/LIVE user-intent safety

## Rule

A future coding task must reference one or more Gap IDs and state exactly which acceptance evidence closes them. A commit that changes runtime without closing a named gap or an approved defect is out of scope.