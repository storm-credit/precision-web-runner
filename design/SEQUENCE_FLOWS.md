# Sequence Flows v1

## 1. Normal scheduled live flow

```text
User -> Dashboard: save task
Dashboard -> RunnerService: SaveTask
RunnerService -> Adapter: validate(task)
Adapter --> RunnerService: valid

User -> Dashboard: ARM
Dashboard -> RunnerService: Arm(taskId)
RunnerService -> LocalStore: persist ArmedRunSnapshot
RunnerService -> Scheduler: schedule(target, prewarm)
RunnerService --> Dashboard: state=ARMED

Scheduler -> RunnerService: PREWARM_DUE
RunnerService -> BrowserBridge: Open(targetUrl)
BrowserBridge --> RunnerService: origin ready
RunnerService -> Adapter: preflightPlan(snapshot)
RunnerService -> BrowserBridge: safe preflight actions
BrowserBridge --> RunnerService: preflight result
Adapter --> RunnerService: preflight PASS
RunnerService: state=PREWARMING

Scheduler -> RunnerService: TARGET_DUE
RunnerService: acquire execution lease
RunnerService: state=RUNNING
RunnerService -> Adapter: executionPlan(snapshot)
Adapter --> RunnerService: site-specific request spec
RunnerService -> BrowserBridge: SameOriginRequest(checkout)
BrowserBridge -> TargetServer: POST authorized normal request
TargetServer --> BrowserBridge: HTTP response
BrowserBridge --> RunnerService: safe BrowserResult
RunnerService -> Adapter: parse(checkout, result)
Adapter --> RunnerService: checkoutNumber
RunnerService -> BrowserBridge: Navigate(/shop/checkout/{checkoutNumber})
BrowserBridge --> RunnerService: checkout page ready

opt User-approved policy:
RunnerService -> BrowserBridge: semantic consent check
BrowserBridge --> RunnerService: checked
RunnerService -> BrowserBridge: open payment UI
BrowserBridge --> RunnerService: payment surface visible

RunnerService: state=WAITING_MANUAL
RunnerService --> Dashboard: manual handoff
User -> Browser/PG: final authorization manually
```

## 2. Server says not allowed / not eligible

```text
BrowserBridge -> TargetServer: checkout request
TargetServer --> BrowserBridge: 4xx rejection
BrowserBridge --> RunnerService: status + bounded safe summary
RunnerService -> Adapter: classify
Adapter --> RunnerService: NON_RETRYABLE_SERVER_REJECTION
RunnerService: state=FAILED
RunnerService --> Dashboard: exact safe failure code
```

Rule: no alternate endpoint, DOM unlock, timing bypass, or repeated hammering.

## 3. Network transport failure before response

```text
BrowserBridge -> TargetServer: request
X transport error before a confirmed HTTP response
BrowserBridge --> RunnerService: TRANSPORT_ERROR
RunnerService -> ErrorPolicy: classify ambiguity
```

POC live policy:
- automatic checkout replay is disabled by default
- because the request may have reached the server even if the client did not receive the response
- state becomes FAILED/AMBIGUOUS_TRANSPORT unless a future adapter contract proves idempotency

## 4. Retryable safe preflight failure

Safe GET/read-only preflight may use bounded retry if it is explicitly side-effect-free.

```text
preflight -> transient transport/5xx
ErrorPolicy -> retry permitted
wait bounded delay
preflight -> retry
```

Irreversible checkout POST does not inherit this generic retry privilege.

## 5. Dynamic response missing checkoutNumber

```text
TargetServer --> BrowserBridge: 2xx response
Adapter.parse -> expected checkoutNumber missing
Adapter --> RunnerService: CONTRACT_MISMATCH
RunnerService: FAILED
```

Do not guess a checkout number or reconstruct one from prior runs.

## 6. Checkout navigation fails after checkout creation

```text
checkout POST -> success + checkoutNumber
navigate checkout -> timeout/failure
RunnerService: record checkoutNumber
RunnerService: FAILED/NAVIGATION_AFTER_CHECKOUT
Dashboard: show that checkout was created but navigation failed
```

Critical: automatic creation of a second checkout is forbidden. User may manually navigate to the known checkout route if normal site behavior supports it.

## 7. Consent locator not found

If auto-consent is configured:
- semantic locator strategy executes
- if not found or ambiguous, runner fails closed or stops at manual checkpoint before clicking anything else
- do not fall back to broad coordinates or guessed CSS hashes

## 8. Payment UI locator not found

Checkout creation remains a known completed step. Runner transitions to WAITING_MANUAL with reason `PAYMENT_UI_NOT_AUTOMATED` if manual checkout page is usable; otherwise FAILED if the expected checkout page itself is not established.

## 9. PC sleep / clock discontinuity

```text
Scheduler detects monotonic/wall-clock discontinuity
if target not yet reached and safe recovery margin exists:
  require policy-defined recovery + fresh preflight
else:
  FAILED/CLOCK_DISCONTINUITY
```

POC default: if wake occurs inside unsafe target window or after target, do not dispatch late.

## 10. User cancels

Before checkout dispatch:
- cancellation token set
- scheduler stops
- state=CANCELLED

After checkout dispatch begins:
- UI does not claim cancellation
- state remains RUNNING until known result or FAILED/AMBIGUOUS

## 11. Process restart

If persisted state says RUNNING at crash:
- no automatic replay
- mark recovery required
- display known checkoutNumber if already safely persisted

If ARMED and target still well in future:
- POC may require manual re-arm rather than silently resume; exact recovery policy must be verified before live use.