# Blindspot Sweep & Pre-Implementation Trap Check

## Critical blindspots

### 1. “URL만 넣으면 자동화된다”
A URL identifies a destination, not the site's auth model, CSRF, API payload, selectors, queue, or checkout flow.

**Decision:** URL + Recipe/Adapter, not URL-only automation.

### 2. Hosted web app can reuse any logged-in session
Cross-origin cookies may be HttpOnly/SameSite and unavailable to another web app.

**Decision:** local runner + authorized browser context.

### 3. Browser timer equals exact server time
Browser timers can be throttled; PC sleep and network jitter matter.

**Decision:** scheduler outside the page, preflight, timing telemetry, no unmeasured millisecond claims.

### 4. Mobile can behave exactly like desktop
Mobile browsers can suspend background tabs and have different extension capabilities.

**Decision:** POC mobile controls the desktop runner; mobile-only execution is deferred.

### 5. Enabling a disabled button means eligibility
The server may independently enforce membership, sale time, stock, or permissions.

**Decision:** never treat frontend unlock as authorization; server rejection is final.

### 6. Dynamic checkout values can be precomputed
Checkout IDs, nonce values, and tokens may be generated per request.

**Decision:** extract runtime values from prior responses.

### 7. CSS module selectors are stable
Generated class suffixes can change after deploy.

**Decision:** prefer semantic text/role/data attributes and fallback chains; add health checks.

### 8. Checkout created means inventory reserved
Reservation semantics vary by site.

**Decision:** display only what the server actually confirms; do not infer stock reservation.

### 9. More retries always improve success
Retries can cause duplicate orders, throttling, or anti-bot flags.

**Decision:** bounded retry, error classification, execution lease/lock.

### 10. Payment can be automated like checkout
Payment providers add dynamic session tokens, 3DS, 2FA, fraud controls, and sensitive data.

**Decision:** POC stops at manual final-payment checkpoint.

## Security/privacy traps

Before implementation verify:
- no raw cookie persistence in backend storage
- no Authorization/CSRF values in normal logs
- HAR/network export is redacted before sharing
- user profile / phone / email fields are removed from captured page JSON
- browser permissions are minimum necessary
- recipes cannot run arbitrary eval
- secrets never leave the local runner unless an approved design explicitly requires it

## Timing traps

Check:
- timezone storage
- local clock drift
- sleep/wake detection
- DNS/TLS cold start
- target site cold page load
- network interface changes
- scheduler thread starvation
- target time already passed
- arm action occurring too close to target

Record separately:
- targetAt
- schedulerWakeAt
- requestStartedAt
- responseReceivedAt

## Browser/session traps

Check before coding:
- how the POC attaches to a browser session
- whether a dedicated automation profile is required
- profile locking
- SameSite/HttpOnly cookies
- CSRF/nonce
- page reload/login expiry
- extension/content-script origin permissions if used
- popups/new tabs during payment handoff

## Operation traps

Check:
- site API/UI changes
- recipe version mismatch
- duplicate tabs/devices
- stale armed jobs
- runner restart
- machine reboot
- log growth/retention
- unsupported/deprecated recipe status

## Absolute non-solutions

Do not:
1. build the full dashboard before proving the runner/session architecture
2. proxy target-site cookies through a cloud backend
3. use only `setTimeout(target-now)` as the scheduler
4. hardcode generated CSS hashes as the only selectors
5. hardcode checkoutNumber/nonce values
6. use unbounded retries
7. auto-authorize payment in the POC
8. bypass CAPTCHA, queues, membership, sale time, or server authorization
9. treat a frontend DOM edit as permission
10. make the first E2E test a high-value real transaction

## Blindspot Gate

Implementation cannot start until these are answered or explicitly accepted as POC assumptions:

- What exact browser/session strategy will the runner use?
- What happens if the PC sleeps between ARM and target time?
- What is the maximum allowed retry count and interval?
- How is duplicate execution prevented?
- Where are task/run data stored?
- How are sensitive response fields redacted?
- What exact event defines “POC success” before final payment?
- How does the UI show that mobile is controlling a desktop runner?
