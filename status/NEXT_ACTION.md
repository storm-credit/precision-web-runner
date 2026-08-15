# Next Action

## Single next objective

**R7 — Typed / Redacted / Bounded Observability.**

R4-R6 passed and Checkpoint C2 passed. Do not begin R8 Local Control API hardening inside this slice.

## Read first

1. `status/CURRENT_STATUS.md`
2. `verification/R6_ORCHESTRATOR_REVIEW.md`
3. `verification/C2_ADAPTER_BROWSER_ORCHESTRATOR_REVIEW.md`
4. `design/IMPLEMENTATION_READY_PLAN.md` — R7
5. `design/OBSERVABILITY_SPEC.md`
6. `design/SECURITY_MODEL.md`
7. `design/ERROR_POLICY.md`
8. `harness/IMPLEMENTATION_GATE_CHECKLIST.md`

## R7 Gap IDs

- G14 typed RunEvent + redaction-before-persistence
- G15 bounded event retention
- safe timing telemetry foundation for G26

## Tests first

Use fixtures containing hostile/sensitive keys and values:
- Cookie / Set-Cookie
- Authorization
- csrf / nonce / token / session
- email / phone / mobile / address
- card / otp / password
- nested dictionaries/lists containing those fields
- long values / oversized detail payloads

Verify:
- none persist to disk
- BrowserResult `safe_body_text` is never accepted as a persisted raw field
- only allow-listed structured detail keys survive
- sequence ordering is per run
- eventId is unique
- state/stage/code/sideEffect survive round-trip
- retention rotates/truncates safely when record/file limits are reached
- timing metrics such as targetAt/requestStartedAt/responseReceivedAt/lateness/latency can be preserved as safe fields

## Allowed scope

- new event logger/redactor module
- LocalStore event integration if needed
- `service.py` event emission migration
- observability tests
- remove legacy Event JSONL path when no longer referenced

No web API, UI, adapter, BrowserBridge behavior, remote control, or final-payment automation belongs in R7.

## Completion condition

R7 ends when:
- persisted events use typed RunEvent shape
- redaction/allowlist happens before disk write
- no raw BrowserResult body/request dump can enter event storage
- event retention is bounded
- service emits enough safe state/timing/error data to reconstruct a run
- full CI passes
- R7 review evidence is recorded

Then R8 becomes eligible.
