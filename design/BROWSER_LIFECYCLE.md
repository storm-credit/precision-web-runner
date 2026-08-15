# Browser & Session Lifecycle v1

## POC strategy

Use one **dedicated Precision Runner Chrome profile** owned by one local runner instance.

The user logs into T1 manually inside that profile. The runner does not import/export the user's everyday Chrome cookies.

## Lifecycle

### 1. First launch
- create/open dedicated profile directory
- launch visible Chrome
- navigate to target origin
- user logs in manually
- runner stores no raw login secret outside the browser profile

### 2. Normal startup
- acquire profile/runner ownership lock
- launch persistent browser context
- verify expected origin can load
- do not assume login merely because profile exists

### 3. Preflight
Preflight must check a safe combination of:
- browser connected
- current/final origin expected
- not redirected to login/auth flow
- target page/request reachable
- site contract markers still recognizable

Preflight must not expose or log account PII merely to prove login.

### 4. Armed waiting
- keep runner process alive
- browser may remain open/visible
- no irreversible requests before target
- if browser exits, run becomes not-ready and requires recovery before target

### 5. Prewarm
- ensure browser context alive
- navigate/warm target origin
- perform safe read-only checks
- verify page contract/session again

### 6. Execution
- page-context same-origin request uses current browser credentials normally
- raw cookie extraction is unnecessary and prohibited
- dynamic response values are returned only as typed safe fields

### 7. Manual payment handoff
- keep browser visible
- user owns PG/3DS/OTP/final approval
- runner must not obscure which browser profile/window is being controlled

### 8. Shutdown
- cleanly close context where practical
- release runner/profile lock
- preserve browser profile for next manual login session
- do not copy profile to cloud

## Profile ownership

Only one Precision Runner process may own the dedicated profile at a time.

If profile is locked:
- do not force-open a second instance
- report `BROWSER_PROFILE_LOCKED`
- user resolves duplicate process/window

## Session expiry

Session validity is not inferred from cookie age.

If target redirects to login or preflight detects unauthenticated state:
- block ARM or fail prewarm
- ask user to log in manually
- require fresh preflight

## Browser crash before target

If enough safe time remains:
- restart browser
- perform full fresh preflight
- preserve same ArmedRunSnapshot

If inside critical timing window:
- fail closed unless recovery behavior has been rehearsed and explicitly approved

## Browser crash after checkout dispatch

If checkout success response/identifier was already confirmed:
- do not create another checkout
- recover by navigating to existing checkout when safe

If response status is unknown:
- classify `TRANSPORT/BROWSER_AMBIGUOUS`
- no automatic replay
- manual inspection required

## Unexpected navigation

BrowserBridge validates final origin for critical steps.

If a target action unexpectedly redirects to:
- login -> SESSION_INVALID
- external PG -> only acceptable at configured payment handoff
- unrelated origin -> stop and report

## Popup/new-tab behavior

POC must explicitly observe new pages/popups during payment handoff rather than assuming the original page remains active.

Final financial authorization remains manual regardless of which tab/window opens.

## Locator health

Before automatic consent/payment-UI click:
- verify expected checkout origin/page context
- locator must be unique and semantically match intent
- no coordinate click fallback

## Rehearsal evidence required

Before live use verify on Windows:
- first login persists across runner restart
- profile lock is enforced
- preflight detects logged-out state
- browser can remain stable across at least one scheduled rehearsal
- checkout navigation uses the same visible controlled profile