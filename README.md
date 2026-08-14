# Precision Web Runner

A design-first POC for executing an **authorized web action flow at a scheduled time** from a logged-in browser session.

The first real-world adapter is T1 Membership, but the core is intentionally not T1-specific.

## Current status

**POC DESIGN ONLY — implementation has not started.**

The POC question is:

> Can a Windows runner, using the user's already-authenticated browser session, execute a predefined web action at the target time, capture dynamic response data, navigate to the next step, and stop safely before final payment?

## POC scope

- Windows PC runner stays on and armed before the target time.
- Responsive web UI works on desktop and mobile; mobile controls/monitors the PC runner rather than executing the purchase itself.
- T1 is Adapter 001.
- The scheduler runs outside the browser tab.
- The runner may execute same-origin browser actions only after the site normally allows them.
- Server-side membership, sale-time, queue, CAPTCHA, rate-limit, or authorization restrictions are never bypassed.
- Final payment / 3DS / 2FA is a manual checkpoint by default.

## Selected UI direction

**Concept 02 — light dashboard, responsive web/mobile.**

The first viewport must make the target, target time, runner state, and primary CTA obvious.

## Design documents

- `CLAUDE.md` — development constitution and gates
- `docs/POC_SCOPE.md` — exact POC boundary and Definition of Done
- `docs/PRODUCT_DESIGN.md` — product and UX design
- `docs/ARCHITECTURE.md` — control plane / execution plane / recipe architecture
- `docs/BLINDSPOT_AND_TRAPS.md` — blindspot sweep and pre-implementation trap check
- `docs/T1_EVIDENCE.md` — observed T1 request flow, sanitized
- `docs/UI_CONCEPTS.md` — four concepts and selected Concept 02
- `docs/REFERENCE_RESEARCH.md` — which external patterns are useful now vs later
- `docs/DECISIONS_AND_INTERVIEW.md` — inferred intent, decisions, open questions
- `docs/IMPLEMENTATION_PLAN.md` — post-approval implementation plan
- `docs/DEVIATIONS.md` — plan deviations and reasons
- `prompts/META_PROMPTING.md` — context dump → prompt distillation → result verification

## Roadmap

1. **POC** — prove the timed runner with T1, stopping before final payment.
2. **MVP** — add task creation, recipe editor, second-site validation, better device pairing.
3. **General platform** — user-supplied URLs + site recipes/adapters, broader mobile/device support.

## Non-goals for the POC

- Arbitrary URL → fully automatic site understanding
- Cloud SaaS
- Mobile-only high-precision execution
- Automatic CAPTCHA/queue handling
- Server restriction bypass
- Fully automatic payment authorization
- Multi-user accounts, teams, billing, recipe marketplace
