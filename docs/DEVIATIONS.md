# Deviations Log

## 2026-08-15 — Runtime implementation preceded deep design completion

- Original plan: finish deep design, harness, blindspot review, and implementation-ready gates before coding.
- Changed area: overall delivery order.
- What changed: a runnable Python/Playwright POC was implemented and merged before the user clarified that coding should happen last.
- Why: the 2026-08-17 live target created pressure to prove feasibility quickly.
- Impact: existing runtime code can contain design choices that were never fully reviewed. It must not be treated as architecture truth.
- Reversible?: yes. Runtime is now classified as **Architecture Spike / prototype evidence** and frozen during Deep Design + Harness work.
- Follow-up verification: after design approval, review every runtime component as KEEP / CHANGE / DELETE against `design/*` and `verification/ACCEPTANCE_MATRIX.md`.
- User approval required?: user explicitly requested the design/harness-first correction.

## 2026-08-15 — Minimal dashboard implemented during core POC build

- Original plan: complete the architecture spike/core runner before building the responsive dashboard.
- Changed area: implementation order.
- What changed: a minimal Concept 02 localhost dashboard was implemented in the same POC slice as scheduler/core/T1 adapter work.
- Why: the user's concrete success target is practical use by 2026-08-17. A working ARM/preflight/status surface was useful to prove the runner flow.
- Impact: UI work moved earlier, but future-platform UI/features were not added. During the design freeze this UI is also considered prototype evidence.
- Reversible?: yes. The HTTP/static UI can be replaced without changing the approved future component contracts.
- Follow-up verification: reconcile every visible control against `design/UI_SPEC.md` after design approval.
- User approval required?: covered by earlier instruction to continue; now superseded by the later design-first clarification.

## 2026-08-15 — Dedicated persistent Chrome profile selected

- Original plan: browser profile/session strategy was left open for architecture spike.
- Changed area: browser execution strategy.
- What changed: POC uses a Precision Runner-specific persistent Chrome profile rather than attaching to the user's everyday Chrome profile.
- Why: simplest way to keep authentication local, persistent across runs, and isolated from normal browsing.
- Impact: user must log into T1 once inside the Precision Runner Chrome window. Chrome must be installed. One runner must own the profile.
- Reversible?: yes. BrowserBridge can later be replaced with another CDP/extension bridge without changing higher-level contracts.
- Follow-up verification: Windows rehearsal must confirm Chrome launches, login persists after restart, profile locking works, and same-origin preflight succeeds.
- User approval required?: no material product-scope change; this matches the recommended session strategy.

## 2026-08-15 — Automatic checkout retry disabled for live POC

- Original plan: allow one bounded retry for selected transport/server failures.
- Changed area: checkout failure/retry policy.
- What changed: irreversible checkout POST replay is disabled for the live POC unless target-side idempotency is independently proven.
- Why: a transport timeout can be ambiguous; replay could create duplicate checkout state or trigger throttling.
- Impact: transient or ambiguous irreversible failures stop for manual inspection instead of automatically replaying checkout.
- Reversible?: yes, only after site-specific idempotency/retry semantics are verified and the design is re-approved.
- Follow-up verification: ensure implementation reconciliation does not apply a generic retry count to irreversible steps.
- User approval required?: no scope expansion; this narrows behavior for safety.

## 2026-08-15 — Mobile-responsive UI retained but LAN remote control deferred from live POC

- Original plan: mobile could optionally control/monitor the Windows runner from the same trusted Wi-Fi during the POC.
- Changed area: control-plane security and mobile scope.
- What changed: deep-design default is localhost-only. Mobile/narrow responsive rendering remains required, but remote LAN control is deferred unless a pairing/authentication/CSRF design is explicitly approved.
- Why: binding the local control API to the LAN introduces a new command-authentication and cross-origin attack surface that is not required to prove the 17 Aug execution flow.
- Impact: live POC control occurs on the Windows PC by default. Mobile visual design is preserved for later secure control-plane work.
- Reversible?: yes, after a secure pairing/auth model is designed and tested.
- Follow-up verification: verify the live dashboard is not unintentionally exposed on `0.0.0.0`.
- User approval required?: this is a scope reduction/safety hardening; surface it in the design review before final approval.

## Template

### YYYY-MM-DD — Short title

- Original plan:
- Changed area:
- What changed:
- Why:
- Impact:
- Reversible?:
- Follow-up verification:
- User approval required?:

## Rule

A material change is not considered complete until this log explains **where the plan changed and why**.