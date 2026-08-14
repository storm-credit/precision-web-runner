# Deviations Log

## 2026-08-15 — Minimal dashboard implemented during core POC build

- Original plan: complete the architecture spike/core runner before building the responsive dashboard.
- Changed area: implementation order.
- What changed: a minimal Concept 02 localhost dashboard was implemented in the same POC slice as scheduler/core/T1 adapter work.
- Why: the user's concrete success target is practical use by 2026-08-17. A working ARM/preflight/status surface is needed to rehearse the actual runner; delaying all UI would reduce available rehearsal time.
- Impact: UI work moved earlier, but future-platform UI/features were not added. The dashboard remains a thin local control surface over the runner.
- Reversible?: yes. The HTTP/static UI can be replaced without changing T1 response parsing or timing helpers.
- Follow-up verification: verify all visible POC controls call real local API actions; run scheduler and browser rehearsal on Windows.
- User approval required?: covered by the user's explicit instruction to continue and build the POC for 17 Aug.

## 2026-08-15 — Dedicated persistent Chrome profile selected

- Original plan: browser profile/session strategy was left open for architecture spike.
- Changed area: browser execution strategy.
- What changed: POC uses Playwright `launch_persistent_context` with a Precision Runner-specific Chrome profile rather than attaching to the user's everyday Chrome profile.
- Why: simplest way to keep authentication local, persistent across runs, and isolated from the user's normal browser while meeting the two-day POC timeline.
- Impact: user must log into T1 once inside the Precision Runner Chrome window. Chrome must be installed.
- Reversible?: yes. BrowserWorker can later be replaced with another CDP/extension bridge.
- Follow-up verification: Windows live rehearsal must confirm Chrome launches, login persists after restart, and same-origin preflight succeeds.
- User approval required?: no material product-scope change; this is the recommended session strategy already discussed.

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
