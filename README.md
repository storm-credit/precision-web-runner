# Precision Web Runner

A local-first POC for executing an **authorized web action flow at a scheduled time** from a logged-in browser session.

The first real-world adapter is T1 Membership, but the scheduler/runner core is intentionally separated from T1-specific request mapping.

## Current status

**POC IMPLEMENTATION IN PROGRESS — branch `poc/t1-runner-v1`.**

The current POC implements:

- local Windows scheduler outside the browser tab
- dedicated persistent Chrome profile (login stays local)
- responsive Concept 02 dashboard
- task save / browser open / preflight / ARM / cancel
- T1 checkout request adapter
- dynamic `checkoutNumber` extraction and checkout navigation
- bounded retry and duplicate execution lock
- optional pre-authorized agreement checkbox handling
- optional payment-window opening while final PG authorization stays manual
- structured local logs without raw cookies/response bodies

## 17 Aug 2026 target

The POC is being narrowed for the 2026-08-17 12:00 KST T1 sale. The goal is to reach the checkout/payment handoff reliably; it does **not** bypass membership, sale-time, stock, queue, CAPTCHA, rate-limit, or payment controls.

The default task contains the observed Signature Edition item values, but `shipping_type_verified` is deliberately false until the shipping contract is confirmed.

## Quick start on Windows

Requires Python 3.11+ and Google Chrome.

```powershell
.\scripts\setup_windows.ps1
.\scripts\run_windows.ps1
```

Dashboard:

```text
http://127.0.0.1:8765/
```

Use **Chrome 열기 / 로그인** once and sign in to T1 inside the dedicated Precision Runner Chrome profile.

Before ARM:

1. Verify the exact target URL/item/price.
2. Verify `shippingType` and tick **배송 유형 확인 완료**.
3. Run Preflight.
4. Rehearse with a safe/test item before using the high-value target.
5. Disable Windows sleep for the live window.

See `docs/POC_RUNBOOK_2026-08-17.md`.

## Safety boundary

The runner fails closed when the target server rejects a request. It does not implement:

- membership/authorization bypass
- sale-time bypass
- CAPTCHA or queue bypass
- anti-bot/rate-limit evasion
- payment/3DS/2FA bypass
- credential/cookie exfiltration

Final payment authorization remains manual.

## Design documents

- `CLAUDE.md` — development constitution and gates
- `docs/POC_SCOPE.md` — POC boundary and Definition of Done
- `docs/PRODUCT_DESIGN.md` — product and UX design
- `docs/ARCHITECTURE.md` — control / execution / adapter architecture
- `docs/BLINDSPOT_AND_TRAPS.md` — blindspot sweep and implementation traps
- `docs/T1_EVIDENCE.md` — sanitized observed T1 request flow
- `docs/UI_CONCEPTS.md` — four UI concepts and selected Concept 02
- `docs/REFERENCE_RESEARCH.md` — external reference adoption decisions
- `docs/DECISIONS_AND_INTERVIEW.md` — decisions and open questions
- `docs/IMPLEMENTATION_PLAN.md` — phased plan
- `docs/DEVIATIONS.md` — plan changes and reasons
- `docs/POC_RUNBOOK_2026-08-17.md` — practical rehearsal/live runbook
- `prompts/META_PROMPTING.md` — context dump → prompt distillation → verification

## Roadmap

1. **POC** — timed local runner + T1 adapter, stopping at manual payment authorization.
2. **MVP** — second structurally different adapter and generic recipe editor.
3. **General platform** — user URLs + adapters/recipes + broader device support.
