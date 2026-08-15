# CLAUDE.md — Precision Web Runner

## 0. Current phase

**DEEP DESIGN + HARNESS FREEZE.**

The user explicitly clarified on 2026-08-15 that coding should happen last. Runtime code already present in the repository is therefore treated as **Architecture Spike / prototype evidence**, not as the design source of truth.

Until the deep-design baseline is reviewed and approved:
- do not add runtime features
- do not refactor `src/`, `tests/`, `scripts/`, or dependencies except for a tiny explicitly approved measurement spike
- do not bend design decisions merely to match existing prototype code
- do not expand into the general platform

Read first:
1. `status/CURRENT_STATUS.md`
2. `status/NEXT_ACTION.md`
3. `harness/GATES.md`
4. `docs/POC_SCOPE.md`
5. `design/*`
6. `verification/*`

## 1. Operating principles

Apply these on every substantial task:
- think before coding
- state assumptions explicitly
- separate observed facts from inference
- prefer the simplest sufficient design
- make surgical changes
- do not add speculative future features
- convert vague goals into verifiable success conditions
- never claim completion without evidence

If multiple interpretations materially change the outcome, surface them instead of silently choosing.

## 2. Mandatory workflow

1. Context Dump
2. User intent / primary user / success conditions
3. Ask only materially necessary missing questions
4. Blindspot Sweep
5. Implementation Trap Check
6. Deep Design / contract update
7. Design Review
8. User approval
9. Implementation reconciliation plan
10. Tests/checks first where practical
11. Minimal implementation
12. Spec/security review
13. Verification with evidence
14. Update decisions/deviations/current status

During the current freeze, stop at step 8.

## 3. Harness gates

`harness/GATES.md` is mandatory.

A later gate may not silently weaken an earlier scope/safety rule.

Finding severity:
- BLOCKER — must resolve before implementation
- MAJOR — resolve or explicitly accept with rationale
- MINOR — may defer
- NOTE — informational

No implementation reconciliation while a BLOCKER remains.

## 4. POC goal

Prove that a Windows-local runner can:
- use a dedicated already-authenticated browser context
- arm a task before a target time
- preflight safely
- dispatch one allowed web action at the configured permitted target time
- capture dynamic response data
- navigate to the next checkout step
- optionally handle pre-authorized consent
- stop at manual final-payment authorization
- report exact timing/state/failure information

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
- automatic CAPTCHA/queue handling
- anti-bot/rate-limit evasion
- authorization/membership/sale-time bypass
- automatic final payment authorization
- complex external memory infrastructure

## 6. Safety/site-boundary rules

Never implement:
- membership/authorization bypass
- sale-time bypass
- CAPTCHA solving/bypass
- queue bypass
- anti-bot evasion
- rate-limit evasion
- payment/3DS/2FA bypass
- credential/cookie exfiltration

If the target server rejects the action because it is not permitted, stop and report the rejection.

The target server is authoritative for authorization, sale opening, request validity, and availability.

## 7. Architecture source of truth

Deep design lives under `design/`.

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

Existing runtime code is assessed later as KEEP / CHANGE / DELETE against these contracts.

## 8. Browser/session rules

POC baseline:
- dedicated Precision Runner Chrome profile
- manual user login
- one local runner owns the profile
- no cookie/token export
- target requests execute in the authorized browser context
- no attachment to everyday Chrome profile by default

Profile/session lifecycle is defined in `design/BROWSER_LIFECYCLE.md`.

## 9. Adapter rules

Use `design/ADAPTER_SPEC.md`.

Core must not know T1:
- endpoint paths
- item IDs
- payload fields
- response field names
- selector/text strategy

No arbitrary stored `eval` recipe language.

Unknown adapter fields that affect irreversible LIVE execution block ARM.

## 10. Error/retry rules

Use `design/ERROR_POLICY.md`.

Critical invariant:
- **automatic replay of an irreversible checkout POST is disabled in the live POC unless idempotency is independently proven and approved**

A generic `max_retries` value must never be applied blindly to irreversible steps.

Ambiguous side effect => do not replay automatically.

## 11. Timing/reliability rules

Use `design/TIMING_DESIGN.md`.

- wall clock expresses target instant
- monotonic time owns waiting after ARM
- prewarm before target
- record actual dispatch/response timing
- detect sleep/wake discontinuity
- do not intentionally dispatch before the published allowed opening time
- do not claim millisecond/server-synchronized precision without measurement

## 12. State-machine rules

Use `design/STATE_MACHINE.md`.

At minimum preserve:
- immutable ArmedRunSnapshot
- one irreversible execution lease
- exact state transition reason/timestamp
- no misleading cancel once irreversible request is in flight
- WAITING_MANUAL is not PAID
- ambiguous crash/restart never silently replays

## 13. Security rules

Use `design/SECURITY_MODEL.md` and `design/OBSERVABILITY_SPEC.md`.

POC dashboard default is **localhost-only**.

Remote phone/LAN control is not required for live POC and requires separate pairing/auth/CSRF design before enabling.

Never persist/log:
- Cookie / Set-Cookie
- Authorization
- CSRF/nonce/token values
- email/phone/address from checkout data
- payment credentials
- OTP/2FA
- full checkout HTML/JSON dumps

## 14. UI rules

Selected design: **Concept 02 — light dashboard**.

Use `design/UI_SPEC.md`.

Desktop and narrow/mobile view use one responsive system.

First viewport must communicate:
- runner readiness
- TEST vs LIVE
- target/task
- target time/countdown
- state
- primary CTA
- blocker reason when CTA unavailable

Every visible control must map to a real behavior or explicit disabled reason.

## 15. Interview/question rule

Do not interview mechanically.

Ask only when missing context would materially change:
- architecture
- security
- irreversible behavior
- live readiness
- user-facing semantics

Do not re-ask questions already answered by repository evidence or explicit user decisions.

Unknown target-site facts remain UNKNOWN; never fill them from guesswork.

## 16. Blindspot / trap rule

Before implementation reconciliation, re-run the blindspot review across:
- architecture
- authentication/session
- browser lifecycle
- timing/reliability
- security/privacy
- operation/recovery
- UX states
- testability

Reject shortcuts such as:
- cloud replay of foreign cookies
- browser timer as precision authority
- generated CSS hash as sole selector
- hardcoded dynamic checkout identifiers
- guessed DOM clicks
- unbounded retry
- automatic irreversible replay
- payment authorization automation
- server restriction bypass

## 17. Testing/verification rules

`verification/ACCEPTANCE_MATRIX.md` defines required evidence.

For timing/browser/live behavior, code review alone is insufficient.

Before LIVE use:
- safe Windows/browser rehearsal
- target contract confirmation
- timing measurements
- log-redaction inspection
- failure-path verification
- `verification/POC_GO_NO_GO.md` PASS

Unknown mandatory acceptance items count as not passed.

## 18. Change/deviation rule

If reality differs from approved design, update `docs/DEVIATIONS.md` before declaring work complete.

Record:
- date
- original plan
- changed area
- what changed
- why
- impact
- reversibility
- follow-up verification
- whether user approval is required

## 19. Meta-prompting rule

For substantial AI work use:

1. Context Dump
2. Prompt Distillation
3. Result Verification

Goal Prompt:
- goal
- success conditions
- stop conditions

Implementation Prompt:
- approved design/contracts
- file scope
- constraints
- tests/checks
- completion evidence

Research Prompt:
- primary/official sources first
- scope
- freshness
- cross-check method
- fact vs inference labeling

Design review uses `prompts/DESIGN_REVIEW_PROMPT.md`.

## 20. Current known facts / blockers

Known:
- T1 origin `https://t1.fan`
- Signature target product path `/shop/products/525`
- observed Signature `inventoryItemId=3454`
- observed Signature amount `500000 KRW`
- normal-item direct checkout flow produced dynamic `checkoutNumber`

Still UNKNOWN / blocking LIVE:
- exact Signature-specific `shippingType`
- Windows live session persistence proof
- actual Windows scheduling variance
- whether current T1 contract changes before rehearsal/live window

Do not infer checkout creation means inventory reservation.

## 21. Global stop conditions

Stop/re-plan when:
- design must materially change
- a BLOCKER remains
- success requires bypassing server restrictions
- session handling cannot remain local/safe
- final payment authorization must be automated
- an irreversible outcome is ambiguous and replay would be required
- a critical assumption cannot be tested
- target-site contract materially changes
- work drifts outside POC scope