# Security Model v1

## Scope

This is a local-first POC threat model. It focuses on preventing the runner from becoming a credential-exfiltration tool or a generic restriction-bypass framework.

## Assets

Protect:
- target-site authenticated browser session
- personal checkout/profile data
- task configuration
- target product values
- local run logs
- payment/PG credentials and approvals

## Trust zones

### Zone A — User + dedicated Chrome profile
Highest trust. Session cookies and login state live here.

### Zone B — Local Runner process
Trusted to orchestrate browser actions, but should not need raw cookie export.

### Zone C — Local Dashboard
Trusted controller. For POC, default bind should be loopback. LAN exposure requires explicit enablement + an authentication mechanism.

### Zone D — Target origin
External service. Its authorization/time/stock validation is authoritative.

### Zone E — Payment provider
External sensitive system. Final authorization is manual and outside runner automation.

## Primary threats and controls

### 1. Cookie/token exfiltration
Threat: automation code reads cookies/local storage and writes them to logs/backend.

Controls:
- do not expose cookie-export APIs in product surface
- same-origin fetch executes in browser context
- logs forbid Cookie/Authorization/Set-Cookie/token fields
- no cloud backend in POC

### 2. Local dashboard hijack
Threat: another device/process calls ARM or manual-continue endpoints.

Controls:
- default listener: `127.0.0.1`
- no LAN bind by default
- if LAN mode is later enabled, require explicit pairing token/session + CSRF protection
- mutating endpoints should reject cross-origin requests

### 3. Arbitrary recipe code execution
Threat: user-provided recipe contains JS/eval and steals session data.

Controls:
- declarative allow-listed step schema
- no arbitrary `eval`
- site adapter code is reviewed/trusted code, not runtime text from a URL

### 4. Over-broad browser permissions
Threat: runner can access unrelated sites/profiles.

Controls:
- dedicated Chrome profile
- adapter URL allowlist
- navigation and same-origin request guard
- POC T1 adapter restricted to expected origin

### 5. Log leakage
Threat: network response includes name/email/phone/address and is persisted/shared.

Controls:
- persist structured summaries, not full bodies
- bounded safe message extraction
- redact known PII keys and secret headers
- never attach raw HAR/session dumps by default

### 6. Confused-deputy action
Threat: dashboard tells runner to call arbitrary endpoint using the logged-in T1 session.

Controls:
- adapter builds request specs; UI does not provide raw arbitrary request editor in POC
- endpoint/method/origin validated by adapter contract

### 7. Server restriction bypass
Threat: automation mutates UI or uses alternate requests to ignore membership/time/queue/CAPTCHA.

Controls:
- explicit forbidden-feature policy
- server rejection is terminal
- no CAPTCHA solving, queue skipping, rate-limit evasion, identity rotation, or DOM-based permission override

### 8. Duplicate financial intent
Threat: transport ambiguity or double-click produces multiple checkout attempts/orders.

Controls:
- one-run execution lease
- no automatic replay of irreversible checkout POST in POC
- ambiguous transport -> manual inspection
- task editing blocked while armed

### 9. Payment automation creep
Threat: implementation gradually clicks through 3DS/OTP/final confirmation.

Controls:
- Manual Payment Boundary is a design invariant
- adapter contract cannot define final authorization steps
- any request to change this requires new design/security review

### 10. Browser profile corruption/locking
Threat: abrupt termination corrupts or locks profile, causing unreliable live behavior.

Controls:
- dedicated profile only
- single runner/browser owner
- detect launch/profile-lock failure in preflight
- do not attach simultaneously from multiple runner instances

## Data classification

### Safe to persist
- runId
- task name/id
- target URL if not secret
- target time
- HTTP status
- checkoutNumber if it contains no personal secret and site behavior confirms it is safe for local log
- timing metrics
- redacted error codes

### Sensitive — local only / avoid persistence where possible
- full response body
- account/profile fields
- checkout page JSON

### Secret — never log/export
- cookies
- Authorization headers
- CSRF/nonce tokens
- payment tokens
- card details
- OTP/2FA

## POC network binding decision

Deep-design default: **localhost-only dashboard**. This supersedes the earlier broad idea that phone control on the same Wi-Fi is automatically included.

Reason: LAN control adds authentication/CSRF/network exposure that is not required for the 17 Aug execution proof.

Mobile-responsive UI remains a design property, but remote phone control becomes an MVP item unless a secure pairing design is separately approved.

## Security gate before live use

Must verify:
- dashboard is not exposed unintentionally on `0.0.0.0`
- dedicated browser profile is used
- logs contain no session or PII dump
- target origin allowlist works
- irreversible POST replay is disabled
- final payment authorization remains manual
- user can identify exactly which browser window/profile is controlled