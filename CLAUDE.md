# CLAUDE.md — Precision Web Runner

## 0. Current phase

**CONTROLLED IMPLEMENTATION — R1 COMPLETE, R2 NEXT.**

Deep Design + Harness + Implementation Reconciliation are complete, Harness Gate 6 passed, and the user explicitly approved continuing into coding. Runtime work is now allowed **only one approved R-slice at a time** according to `design/IMPLEMENTATION_READY_PLAN.md`.

Current permission:
- current approved slice (`status/NEXT_ACTION.md`): allowed
- tests/checks for that slice: required first where practical
- unrelated `src/`, `tests/`, `scripts/`, dependencies: prohibited
- speculative/future features: prohibited

R1 Domain Contracts is complete and reviewed. R2 Local Store / Atomic ARM / Restart Safety is next. Do not start R3 implicitly inside R2.

Read first:
1. `status/CURRENT_STATUS.md`
2. `status/NEXT_ACTION.md`
3. `harness/IMPLEMENTATION_GATE_CHECKLIST.md`
4. `harness/GATES.md`
5. `docs/POC_SCOPE.md`
6. `design/IMPLEMENTATION_READY_PLAN.md`
7. `design/IMPLEMENTATION_RECONCILIATION.md`
8. `verification/IMPLEMENTATION_GAP_MATRIX.md`
9. remaining `design/*` and `verification/*`

## 1. Operating principles

Apply on every substantial task:
- think before coding
- state assumptions explicitly
- separate observed facts from inference
- prefer the simplest sufficient solution
- make surgical changes
- do not add speculative future features
- translate vague goals into verifiable success conditions
- never claim completion without evidence

If multiple interpretations materially change the result, surface them instead of silently choosing.

## 2. Mandatory workflow

1. Context Dump
2. User intent / primary user / success conditions
3. Ask only materially necessary missing questions
4. Blindspot Sweep
5. Implementation Trap Check
6. Deep Design / contract update
7. Design Review
8. User approval
9. Implementation reconciliation + implementation-ready plan
10. Explicit coding approval
11. Select exactly one R-slice
12. Tests/checks first where practical
13. Minimal implementation
14. Spec/security review
15. Verification with evidence
16. Update decisions/deviations/current status
17. Only then make the next R-slice eligible

During the current phase, follow `status/NEXT_ACTION.md`; do not batch later R-slices into the current change.

## 3. Harness gates

`harness/GATES.md` and `harness/IMPLEMENTATION_GATE_CHECKLIST.md` are mandatory.

Finding severity:
- BLOCKER — must resolve before implementation
- MAJOR — resolve or explicitly accept with rationale
- MINOR — may defer
- NOTE — informational

Every implementation slice must:
- be an approved R1-R10 slice
- name Gap IDs
- name design authority files
- define tests/checks and completion evidence
- preserve safety/site boundaries
- update status after verification

A failed implementation-gate checkbox stops the slice or triggers replanning.

## 4. POC goal

Prove that a Windows-local runner can:
- use a dedicated authenticated browser context
- arm a task before a target time
- preflight safely
- dispatch one normally permitted web action at the configured opening time
- capture dynamic response data
- navigate to checkout
- optionally handle pre-authorized consent
- stop at manual final-payment authorization
- report exact state/timing/failure information

T1 is Adapter 001, not the product definition.

## 5. POC non-goals

Do not build during POC:
- arbitrary URL auto-understanding
- AI-generated production recipes
- cloud execution
- SaaS users/teams/billing
- recipe marketplace
- browser farm
- mobile-only precision execution
- remote LAN control without separate security design
- CAPTCHA/queue bypass
- anti-bot/rate-limit evasion
- membership/authorization/sale-time bypass
- automatic final payment authorization
- complex external memory infrastructure

## 6. Safety/site-boundary rules

Never implement:
- membership/authorization bypass
- sale-time bypass
- CAPTCHA solving/bypass
- queue bypass
- anti-bot or rate-limit evasion
- payment/3DS/2FA bypass
- credential/cookie exfiltration

If the target server rejects the action because it is not permitted, stop and report it. The target server is authoritative for authorization, opening time, request validity, and availability.

## 7. Architecture source of truth

Deep design under `design/` is authoritative. Existing pre-reconciliation runtime is Architecture Spike evidence, and each approved R-slice migrates it toward the design contracts.

Core boundaries:
- Control UI
- Local Control API
- RunnerService / Orchestrator
- Scheduler
- BrowserBridge
- Site Adapter v1
- EventLogger
- Local Store
- Manual Payment Handoff

Use `design/IMPLEMENTATION_RECONCILIATION.md` for KEEP/CHANGE/MOVE/DELETE decisions.

## 8. Domain/state invariants

Use `design/COMPONENT_CONTRACTS.md` and `design/STATE_MACHINE.md`.

Must preserve:
- generic TaskDefinition separate from adapter variables
- immutable ArmedRunSnapshot
- runId + adapter version captured before scheduler activation
- one irreversible execution lease
- state path: DRAFT -> TESTED -> ARMED -> PREWARMING -> RUNNING -> WAITING_MANUAL -> SUCCEEDED, plus FAILED/CANCELLED
- every transition has timestamp + reason/code
- no task mutation changing an active snapshot
- no misleading cancel after irreversible dispatch
- WAITING_MANUAL is not PAID
- restart/ambiguous outcome never silently replays

R1 established the domain-contract types. Later slices must migrate active runtime behavior onto them rather than expanding the legacy compatibility layer.

## 9. Browser/session rules

Use `design/BROWSER_LIFECYCLE.md` and `design/SECURITY_MODEL.md`.

POC baseline:
- dedicated Precision Runner Chrome profile
- user logs in manually
- one runner owns profile
- no cookie/token export
- target requests run in authorized browser context
- BrowserBridge is generic and T1-free
- adapter provides origin/request/locator plans

POC dashboard default is localhost-only. Remote phone/LAN control requires a separately approved pairing/auth/CSRF design.

## 10. Adapter rules

Use `design/ADAPTER_SPEC.md`.

Core must not know T1 endpoint paths, product IDs, payload fields, response names, or locator text.

Every adapter has:
- id/version
- exact supported origins/patterns
- typed variables
- evidence status VERIFIED/INFERRED/UNKNOWN
- preflight/execution plans with side-effect classification
- semantic parsing and locators
- manual checkpoint

Unknown fields affecting irreversible LIVE execution block ARM.

No arbitrary stored `eval` recipe language.

## 11. Error/retry rules

Use `design/ERROR_POLICY.md`.

Critical invariant:
- **irreversible checkout POST is not automatically replayed in live POC unless idempotency is independently proven and approved**

Do not use task-global retry for all steps.

Per-step policy depends on effect classification.

Ambiguous irreversible outcome => `TRANSPORT_AMBIGUOUS` / no replay / manual inspection.

Confirmed checkout + navigation failure => reuse known checkout identifier; do not create a second checkout.

## 12. Timing rules

Use `design/TIMING_DESIGN.md`.

- wall clock defines user target instant
- monotonic clock owns waiting after ARM
- T-30s prewarm baseline
- no irreversible prewarm request
- record schedulerWakeAt/requestStartedAt/responseReceivedAt and derived lateness
- detect sleep/wake or clock discontinuity
- `maxLatenessMs` belongs to ArmedRunSnapshot and is selected from rehearsal evidence
- do not intentionally dispatch before published opening time
- do not claim millisecond/server-synchronized precision without measurement

## 13. Observability/security rules

Use `design/OBSERVABILITY_SPEC.md`.

RunEvent must eventually carry runId, sequence, state, stage, stepId, level, stable code, message, sideEffect, safeDetail.

Redaction occurs before persistence.

Never persist/log:
- Cookie / Set-Cookie
- Authorization
- CSRF/nonce/token/session material
- email/phone/address from checkout data
- payment credentials
- OTP/2FA
- full checkout HTML/JSON dumps

Logs must be bounded.

## 14. UI rules

Selected design: **Concept 02 — light dashboard**. Use `design/UI_SPEC.md`.

First viewport communicates:
- runner readiness
- TEST vs LIVE
- target/task
- target time/countdown
- current state
- one primary CTA
- blocker reason when unavailable

LIVE requires explicit confirmation summary. RUNNING cannot offer fake undo. AMBIGUOUS failures cannot show generic retry. Final payment remains visibly manual.

Every visible control must map to real behavior or a clear disabled reason.

## 15. Reconciliation / implementation rules

Use:
- `design/IMPLEMENTATION_RECONCILIATION.md`
- `verification/IMPLEMENTATION_GAP_MATRIX.md`
- `design/IMPLEMENTATION_READY_PLAN.md`

Every coding task must state:
- R-slice (R1-R10)
- Gap IDs addressed
- design contract satisfied
- files allowed to change
- test/check written first or why not
- completion evidence
- rollback boundary

Prefer one reviewable commit/PR slice per R-number. Do not rewrite from scratch unless evidence-backed review proves the approved reconciliation path unusable.

## 16. Interview/question rule

Do not interview mechanically. Ask only if missing context materially changes architecture, security, irreversible behavior, live readiness, or user-facing semantics.

Do not re-ask resolved questions. Unknown target-site facts remain UNKNOWN; never fill them by guess.

## 17. Blindspot / trap rule

Before each coding slice, re-check:
- architecture boundaries
- auth/session lifecycle
- timing/sleep/recovery
- security/privacy
- side-effect ambiguity
- duplicate execution
- target contract versioning
- UX intent and TEST/LIVE separation
- testability

Reject shortcuts such as browser-only precision timers, hardcoded dynamic IDs, generated CSS hashes as sole locators, guessed clicks, unbounded retry, automatic irreversible replay, payment authorization automation, or server restriction bypass.

## 18. Testing/verification rules

`verification/ACCEPTANCE_MATRIX.md`, `verification/IMPLEMENTATION_GAP_MATRIX.md`, and per-slice review evidence define completion.

Code review alone is insufficient for browser/timing/live behavior.

Before LIVE:
- exact Signature `shippingType` evidence
- Windows session persistence rehearsal
- profile ownership/duplicate-run rehearsal
- at least 5 timing rehearsals and selected maxLatenessMs
- safe checkout/navigation/manual-handoff rehearsal
- log redaction inspection
- target contract freshness check
- `verification/POC_GO_NO_GO.md` fully PASS

Unknown mandatory rows = NO-GO.

## 19. Change/deviation rule

If reality differs materially from approved design or implementation-ready plan, update `docs/DEVIATIONS.md` before claiming completion.

Record original plan, changed area, what/why, impact, reversibility, follow-up verification, and user-approval need.

## 20. Meta-prompting rule

For substantial AI work:
1. Context Dump
2. Prompt Distillation
3. Result Verification

Goal Prompt = goal + success conditions + stop conditions.
Implementation Prompt = approved contracts + file scope + constraints + tests + evidence.
Research Prompt = primary sources + scope + freshness + cross-check + fact/inference labels.

## 21. Current known live blockers

Known:
- T1 origin `https://t1.fan`
- target product path `/shop/products/525`
- observed Signature `inventoryItemId=3454`
- observed amount `500000 KRW`
- normal-item direct checkout returned dynamic checkoutNumber

Still UNKNOWN / blocking LIVE:
- Signature-specific `shippingType`
- Windows session persistence proof
- actual scheduling variance / chosen maxLatenessMs
- near-live target-contract freshness

Do not infer checkout creation means inventory reservation or payment success.

## 22. Global stop conditions

Stop/re-plan when:
- design must materially change
- a design BLOCKER appears
- requested work is not mapped to an approved gap
- success requires bypassing server restrictions
- session handling cannot remain local/safe
- final payment authorization would need automation
- irreversible outcome is ambiguous and replay would be required
- a critical assumption cannot be tested
- target-site contract materially changes
- work drifts outside POC scope
