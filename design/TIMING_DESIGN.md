# Timing Design v1

## Objective

Execute the target action as close as practical to the configured target instant while making timing uncertainty measurable and never using timing tricks to bypass server-side opening rules.

## Clock model

Three notions of time are separated:

### Wall clock
User-facing KST target such as `2026-08-17T12:00:00+09:00`.

Used for:
- configuration
- logs
- display

### Monotonic clock
Process-local non-adjustable elapsed-time source.

Used for:
- countdown after ARM
- sleep/discontinuity detection
- scheduler waits

### Target-server observation
HTTP response timing / Date-like metadata may be observed for diagnostics, but the runner does not assume it can perfectly synchronize to a private server clock.

## ARM algorithm

At ARM:
1. parse target instant with timezone
2. sample wall clock and monotonic clock together
3. compute monotonic target deadline
4. persist target + samples
5. create prewarm deadline
6. activate one scheduler lease

If system wall clock changes after ARM, monotonic deadline remains the execution reference unless a discontinuity policy invalidates the run.

## Prewarm

POC default: `T-30s`.

Purpose:
- ensure Chrome process alive
- ensure target origin page loaded
- resolve DNS/TLS ahead of time through normal page access
- verify session
- run safe preflight

Prewarm must not call the irreversible checkout endpoint.

## Dispatch

At target monotonic deadline:
- re-check cancellation
- acquire irreversible execution lease
- record `schedulerWakeAt`
- record `requestStartedAt` immediately before browser/page request
- execute once
- record `responseReceivedAt` when a response/result is known

## Required telemetry

Per run:
- configuredTargetAt
- armedAt
- prewarmScheduledAt
- prewarmStartedAt
- preflightCompletedAt
- schedulerWakeAt
- requestStartedAt
- responseReceivedAt
- checkoutParsedAt
- checkoutPageReadyAt
- manualCheckpointAt

Derived:
- wakeLatenessMs = schedulerWakeAt - targetAt
- dispatchLatenessMs = requestStartedAt - targetAt
- responseLatencyMs = responseReceivedAt - requestStartedAt
- checkoutNavigationMs

## Max-lateness policy

POC baseline:
- do not advertise millisecond accuracy
- define a fail-closed late threshold before live use based on rehearsal evidence
- existing prototype's 2-second cutoff is a spike choice, not yet the final design contract

Design requirement:
`maxLatenessMs` must be explicit in ArmedRunSnapshot and visible in logs.

If exceeded before irreversible dispatch:
- do not dispatch late
- state = FAILED/LATE_TARGET

## Sleep/wake detection

Detect discontinuity by comparing expected monotonic elapsed time against wall-clock movement and scheduler wake delay.

If sleep occurs:
- if safely before prewarm with sufficient margin, require fresh preflight
- if inside the critical window or after target, fail closed

No silent "catch-up" checkout after the target.

## Windows preconditions

Live run requires:
- automatic time synchronization enabled
- sleep/hibernate disabled during window
- laptop power connected where applicable
- stable network
- no planned VPN/proxy/network switching
- runner started well before prewarm

## Rehearsal protocol

At least 5 scheduled rehearsals should use a safe/non-final flow or an internal timing-only test.

Record for each:
- target
- scheduler wake lateness
- dispatch lateness
- local CPU/load notes
- browser already-open vs cold

Report:
- median
- p95-like worst observed value for the small sample
- max

Do not add a negative/positive timing offset merely because one run was late. Offset requires repeated evidence and must never intentionally dispatch before the site's permitted time.

## Server-opening rule

The configured target for live use is the published allowed opening instant. The runner must not intentionally send the irreversible action before that instant to "race latency".

If the server still says not open, the response is authoritative and the runner stops according to Error Policy.

## Precision claim policy

Allowed claim before measurement:
- "scheduled target-time dispatch with measured telemetry"

Not allowed:
- "exact millisecond execution"
- "server-synchronized execution"
- "guaranteed first request"

Such claims require empirical evidence that the current POC does not yet have.