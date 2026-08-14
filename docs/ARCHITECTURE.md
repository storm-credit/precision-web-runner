# Architecture

## POC architecture

```text
Responsive Web UI (desktop/mobile)
        |
        v
Local Control API on Windows PC
        |
        +--> Scheduler / Clock layer
        +--> Run state machine
        +--> Recipe engine
        +--> Structured redacted logs
        |
        v
Browser execution bridge
        |
        v
Logged-in target origin (T1 for Adapter 001)
```

The POC is intentionally local-first. It avoids a cloud backend holding another site's authentication session.

## Why not a hosted web app alone?

A random hosted control site cannot safely assume it can read or replay another origin's HttpOnly/SameSite cookies. The action therefore executes inside an authorized browser context or through a local browser automation bridge attached to that context.

## Recommended POC execution model

### Control plane

A responsive local web app provides:
- task configuration
- target time
- test/arm/cancel
- runner state
- step progress
- logs

It can be opened on the PC and, optionally, from a phone on the same trusted network.

### Execution plane

A Windows local runner owns:
- precise scheduling
- browser process/session connection
- preflight
- recipe execution
- step/state logging
- duplicate-run lock

### Browser bridge

The bridge executes target-origin actions in the logged-in context. For a same-origin API call, the preferred POC shape is to execute `fetch` from the page context rather than copy cookies into the runner.

The exact Playwright/CDP/profile strategy remains an implementation decision and must be proven in the architecture spike before the UI is built out.

## Scheduler

Do not use a browser tab timer as the authoritative scheduler.

The scheduler should:
- store target wall-clock time + timezone
- use monotonic elapsed time once armed
- detect sleep/wake discontinuity
- preflight before execution
- record actual dispatch timestamp
- enforce one-run lease/lock

POC does not promise true millisecond server alignment. It measures actual dispatch/response timing and keeps timing assumptions visible.

## Recipe engine

The recipe engine should be declarative and allow-listed.

Example conceptual step flow:

```yaml
steps:
  - type: waitUntil
    at: ${targetTime}
  - type: sameOriginFetch
    request: checkoutRequest
  - type: extract
    from: response.checkoutNumber
    as: checkoutNumber
  - type: navigate
    to: /shop/checkout/${checkoutNumber}
  - type: waitForText
    text: 주문 내용과 약관에 동의합니다
  - type: check
    target: configured-consent
  - type: manualCheckpoint
    reason: final-payment
```

No arbitrary JavaScript `eval` in stored recipes for the POC.

## Separation rule

Core modules know only generic concepts:
- task
- schedule
- run
- recipe
- step
- variable
- result

T1 adapter owns:
- T1 URL patterns
- T1 endpoints
- T1 request mapping
- T1 selector/text strategy
- T1 response extraction

## Persistence

POC persistence can remain local.

Store:
- task metadata
- recipe versions
- run timing
- redacted response summaries

Do not persist:
- raw cookies
- authorization headers
- full checkout page JSON containing personal information
- card/payment secrets

## Mobile boundary

POC mobile support means responsive control/monitoring.

High-precision execution happens on the paired Windows runner. Mobile-only background execution is explicitly deferred because browser background suspension and extension support differ by platform.
