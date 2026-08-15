# Architecture

> This is the high-level architecture summary. Deep contracts live under `design/` and take precedence if this summary is less specific.

## POC architecture

```text
Responsive Local UI
        |
        v
Local Control API (localhost-only by default)
        |
        v
RunnerService / Orchestrator
   |        |        |        \
   |        |        |         -> EventLogger / Local Store
   |        |        |
   |        |        -> Site Adapter v1 (T1 Adapter 001)
   |        -> Scheduler / Clock layer
   -> Run State Machine + Execution Lease
        |
        v
BrowserBridge
        |
        v
Dedicated persistent Chrome profile
        |
        v
Authorized target origin
        |
        v
Manual payment handoff
```

The POC is local-first. It avoids a cloud backend holding another site's authentication session.

## Deep-design references

- `design/SYSTEM_DESIGN.md`
- `design/COMPONENT_CONTRACTS.md`
- `design/STATE_MACHINE.md`
- `design/SEQUENCE_FLOWS.md`
- `design/ERROR_POLICY.md`
- `design/TIMING_DESIGN.md`
- `design/BROWSER_LIFECYCLE.md`
- `design/SECURITY_MODEL.md`
- `design/OBSERVABILITY_SPEC.md`
- `design/ADAPTER_SPEC.md`
- `design/UI_SPEC.md`

## Why not a hosted web app alone?

A hosted controller cannot assume it can read/replay another origin's HttpOnly/SameSite cookies. Target actions therefore execute through the user's dedicated authenticated browser context on the Windows machine.

## Control plane

Provides:
- task configuration
- target time
- test/preflight
- ARM/DISARM
- state/progress
- redacted logs

Security baseline for POC:
- bind to localhost by default
- mobile/narrow responsive rendering remains part of UI design
- remote LAN phone control is deferred until pairing/authentication/CSRF protection is separately designed

## Execution plane

Windows local runner owns:
- immutable ArmedRunSnapshot
- monotonic scheduling
- prewarm
- browser/session lifecycle
- one irreversible execution lease
- adapter orchestration
- state transitions
- structured redacted logs

## BrowserBridge

POC decision is now explicit:
- dedicated Precision Runner persistent Chrome profile
- manual user login
- same-origin page-context requests
- no cookie export
- one runner owns the profile

The browser implementation remains replaceable behind the BrowserBridge contract.

## Scheduler

Do not use a page JavaScript timer as scheduling authority.

The scheduler:
- records target wall-clock instant + timezone
- derives monotonic target deadline after ARM
- emits prewarm/target signals
- detects unsafe late/sleep conditions
- records actual dispatch/response timing

The runner does not intentionally dispatch before the published permitted opening time and does not claim millisecond server alignment without evidence.

## Adapter model

Core knows generic concepts only:
- task
- snapshot
- run
- schedule
- state
- step
- result
- event

T1 Adapter 001 owns:
- T1 URL/origin rules
- endpoint/method/body mapping
- T1 response parsing
- semantic locators
- T1-specific evidence/unknown fields

Unknown fields that affect LIVE irreversible execution block ARM.

## Retry / ambiguity

Read-only side-effect-free preflight can use bounded retry.

Irreversible checkout POST automatic replay is disabled for the live POC unless idempotency is independently proven. Ambiguous irreversible outcome requires manual inspection.

## Persistence

Persist locally:
- editable task metadata
- immutable run snapshot metadata
- adapter/version identifiers
- timing metrics
- structured redacted events

Never persist/log:
- raw cookies
- Authorization/CSRF/token values
- full personal checkout JSON/HTML
- card/payment secrets
- OTP/2FA

## Manual boundary

Automation can reach the configured checkout/payment handoff. Final PG/card/simple-payment authorization remains manual.

`WAITING_MANUAL` is not equivalent to paid/completed.

## Existing code

Current Python/Playwright runtime is **Architecture Spike / prototype evidence**. It must later be reconciled as KEEP / CHANGE / DELETE against the deep-design contracts after user approval.