# UI Specification v1 — Concept 02

## Goal

The UI must make the user's action, target time, runner readiness, and safety boundary obvious before ARM. It is a control surface, not a decorative dashboard.

## Design direction

Selected concept: **Concept 02 — light, neutral, responsive dashboard**.

Brand language stays generic:
- Task
- Target
- Runner
- Schedule
- Test
- ARM
- Run Log

T1 appears as Adapter/Task context, not product identity.

## Desktop information hierarchy

### Header
- product name
- runner local time (KST)
- device/browser connection indicator
- current mode: TEST or LIVE

### Primary task card
Must show without scrolling at normal desktop viewport:
- task name
- target URL/domain
- adapter
- target date/time/timezone
- target item summary
- validation status
- primary CTA

### Live state card
- finite state name
- countdown
- preflight status
- last safe event
- checkout identifier if created
- exact error code if failed

### Flow card
Ordered steps with status:
- browser/session
- preflight
- target wait
- dispatch
- response parse
- checkout navigation
- optional consent
- manual payment handoff

### Log card
Structured events only; no raw secrets/PII.

## Mobile information hierarchy

First viewport priority:
1. Runner connected/ready?
2. TEST vs LIVE badge
3. target/task
4. target time + countdown
5. current state
6. one primary CTA
7. blocker banner if ARM unavailable

Detailed variables, flow, and logs may be below fold.

POC deep-design decision:
- mobile layout must be responsive and readable
- actual remote LAN control is **not required for live POC**; localhost-only remains security default

## Primary CTA rules

### DRAFT
Primary: `테스트/검증`
Secondary: `Chrome 열기`
ARM disabled with visible reasons.

### TESTED / READY
Primary: `ARM`
Secondary: `Preflight 다시 실행`

### ARMED
Primary destructive: `ARM 해제`
No edit controls for armed snapshot.

### PREWARMING
Primary: `취소` only if irreversible dispatch has not started.
Show target countdown prominently.

### RUNNING
No fake cancel button once irreversible request is in flight.
Show `실행 중` and current step.

### WAITING_MANUAL
Primary: `브라우저에서 결제 계속`
UI clearly states final payment is manual.

### FAILED
Primary depends on side-effect status:
- NONE -> `설정 확인`
- CONFIRMED checkout -> `기존 Checkout 열기` if safe
- AMBIGUOUS -> `수동 확인 필요`

Never show generic `다시 시도` for ambiguous irreversible failures.

## ARM blockers

UI must list exact blockers, not only disable the button.

Examples:
- 로그인/Preflight 미확인
- 대상 시각이 과거
- Signature shippingType 미검증
- 다른 run active
- dashboard/runtime contract mismatch
- target adapter unverified

## Test vs LIVE separation

Visual requirements:
- mode badge always visible
- LIVE ARM requires confirmation summary
- Test mode cannot silently become LIVE

LIVE confirmation summary should repeat:
- task
- domain
- item ID/name summary
- amount
- target time
- adapter version
- final payment boundary

## Consent behavior

If auto-consent option exists:
- wording must make clear it means user has already reviewed/accepted the relevant terms
- default OFF
- changing it while armed is impossible
- failure to find exact consent element stops automation/manual handoff; it does not guess-click

## Payment handoff

If `open payment UI` option exists:
- default can remain OFF until rehearsed
- UI must explicitly say PG/3DS/OTP/final authorization is manual
- after handoff, state is `WAITING_MANUAL`, not `PAID`

## Error presentation

Show:
- stage
- stable code
- concise message
- side-effect status: none/confirmed/ambiguous
- safe next action

Hide:
- cookies
- tokens
- raw JSON/HTML
- email/phone/address
- payment data

## Accessibility / robustness

- keyboard reachable buttons/forms
- clear focus states
- status not conveyed by color alone
- countdown uses tabular numerals
- no control exists purely as decoration
- destructive actions require distinct wording

## First-time comprehension success

A first-time user should be able to answer within 10 seconds:
- What will run?
- When will it run?
- Is the runner/browser ready?
- Is this TEST or LIVE?
- What happens automatically?
- Where will automation stop?

## POC completion UI gate

The UI is acceptable only when every visible POC control maps to a real, tested local action and every unavailable action exposes the reason it is blocked.