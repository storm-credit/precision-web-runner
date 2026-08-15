# R7 Typed / Redacted / Bounded Observability Review

## Verdict

**R7 SLICE: PASS PENDING NORMAL CI MERGE GATE.**

This review covers the observability contract only. It does not approve Local Control API/UI behavior or LIVE use.

## Gap coverage

- G14 typed RunEvent + redaction-before-persistence
- G15 bounded local event retention
- timing telemetry foundation for G26

## Tests-first evidence

`tests/test_observability.py` specifies and verifies:
- Cookie / Set-Cookie / Authorization / token / session / CSRF / nonce rejection
- email / phone / address / card / OTP / password rejection
- nested/unapproved detail rejection
- raw request/response body and HTML fields never persist
- typed eventId/runId/sequence/state/stage/step/code/sideEffect round-trip
- per-run monotonic event sequence and unique event IDs
- safe timing metrics and current-run checkoutNumber retention
- sensitive message pattern redaction
- bounded detail values
- bounded record count
- bounded event-file bytes
- state-path reconstruction from safe persisted events

The byte-retention fixture was corrected during R7 diagnosis so the configured file cap is large enough to hold one typed event; the test now measures retention/trimming rather than an impossible schema-smaller-than-cap condition.

## Implementation result

New `src/precision_runner/observability.py` provides:
- typed immutable persisted `RunEvent`
- `EventLogger`
- allow-list-first safe-detail admission
- deny rules for secret/PII/body fields before event creation and disk write
- string defense-in-depth redaction
- message/detail length bounds
- per-run sequence assignment
- UUID event IDs
- bounded record/file retention
- atomic file rewrite

RunnerService now emits structured events for:
- runner/task/browser lifecycle
- preflight
- ARM/cancel/test acceptance
- prewarm/target due
- request start/response received
- checkout parse/navigation
- consent/payment-UI handoff
- manual checkpoint
- stable failure codes

Safe timing fields include target/request/response/checkpoint timestamps and wake/dispatch/response/navigation latency metrics.

## Raw body boundary

BrowserResult `safe_body_text` remains transient adapter-parser input only. RunnerService never passes it to EventLogger. EventLogger additionally rejects body/html-style keys even if a future caller tries to supply them.

## Security review

PASS for R7 scope:
- no cookie/token/session export
- no account PII persistence
- no payment credential/OTP persistence
- no raw checkout/page/network dump persistence
- no permission/sale-time/CAPTCHA/queue/rate-limit bypass added
- final payment authorization remains manual

## Retention

POC event storage is bounded by both:
- maximum record count
- maximum file bytes

Oldest records are trimmed first. A single event that cannot fit the configured cap fails closed rather than writing an oversized record.

## Diagnostics cleanup

The superseded R7 PR #10 used a temporary diagnostic workflow only to surface unittest failure details. It was closed and is not merged. The clean R7 branch/PR uses the repository's normal test workflow with no diagnostic workflow change.

## Known deferrals

- R8: localhost-only Local Control API and mutation-origin/command-result contract
- R9: Concept 02 UI mapping to typed state/error/event data
- R10: real Windows timing/session/profile/target evidence and final redaction inspection

## Next action

After normal CI passes and this slice is merged, proceed to R8 — Local Control API.
