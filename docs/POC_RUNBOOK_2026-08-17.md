# POC Runbook — T1 2026-08-17 12:00 KST

## Purpose

Make the current POC practically usable for the 2026-08-17 sale while preserving a fail-closed safety boundary.

The runner automates the path to checkout/payment handoff. It does not bypass T1 eligibility or automate final payment authorization.

## One-time setup

1. Install Python 3.11+ and Google Chrome.
2. Clone/pull this repository.
3. Run:

```powershell
.\scripts\setup_windows.ps1
.\scripts\run_windows.ps1
```

4. Dashboard opens at `http://127.0.0.1:8765/`.
5. Click **Chrome 열기 / 로그인**.
6. Sign in to T1 inside that Chrome window.
7. Keep this dedicated Precision Runner profile for the POC.

## Why a dedicated Chrome profile

The runner deliberately does not copy cookies or tokens into a backend. Playwright launches its own persistent Chrome profile under the user's home directory and the user logs in there manually.

## Signature configuration

Current observed defaults:

- target URL: `https://t1.fan/shop/products/525`
- inventory item ID: `3454`
- quantity: `1`
- amount: `500000 KRW`
- target: `2026-08-17 12:00:00 KST`

**Blocking item:** verify the Signature Edition `shippingType` before live ARM. The UI intentionally blocks live checkout until **배송 유형 확인 완료** is checked.

Do not infer that creating a checkout guarantees inventory reservation.

## Rehearsal — 15/16 Aug

### A. Safe preflight

1. Open/login Chrome.
2. Click **Preflight 테스트**.
3. Require an OK response in the log.
4. If authentication/session looks wrong, fix it before checkout testing.

### B. Safe checkout rehearsal

Use a safe/normal product whose request fields you have verified. Do not use the 500,000 KRW target as the first live-flow test.

1. Replace URL/item/price/shipping type with the safe item.
2. Mark shipping type verified only after checking it.
3. Keep final payment manual.
4. Click **Checkout Test Now** and confirm.
5. Verify a new dynamic `checkoutNumber`, checkout navigation, and `WAITING_MANUAL`.
6. If testing consent, read/accept the terms first, enable **약관 체크 자동화 허용**, then test it.
7. Do not complete payment for a rehearsal item unless you intend to buy it.

### C. Scheduler rehearsal

1. Restore a safe test item.
2. Set target time 5-10 minutes ahead.
3. Save and ARM.
4. Confirm T-30s prewarm events appear.
5. Confirm dispatch occurs at the target and inspect timestamps.
6. Repeat to measure real Windows/network timing variance.

The POC must not claim millisecond accuracy until these measurements exist.

## Windows live checklist

- Windows clock is synchronized.
- PC sleep/hibernate is disabled during the sale window.
- Laptop is connected to power.
- Stable network is selected.
- VPN/proxy changes are avoided during the run.
- Precision Runner Chrome profile is logged in.
- Preflight passes.
- T1 task values are restored and double-checked.
- Signature `shippingType` is confirmed.
- Target time is `2026-08-17T12:00:00+09:00`.
- No second Precision Runner instance is running.

Run `./scripts/preflight_windows.ps1` before the live window.

## Suggested live timeline

### 11:40-11:50

- Start runner.
- Open/login Chrome.
- Verify target configuration.
- Run Preflight.

### By 11:55

- Save final task.
- ARM.
- Leave the PC awake and runner process open.

### 11:59:30

Runner enters prewarm automatically and loads the target page plus a safe same-origin preflight.

### 12:00:00

Runner dispatches the checkout request from the logged-in T1 page context.

On success it extracts `checkoutNumber`, navigates to checkout, optionally handles configured consent, optionally opens the payment UI, then stops at manual PG/payment authorization.

If T1 rejects the request, the runner stops and records the reason. It does not attempt restriction bypass.

## Retry policy

Live POC default:

- `max_retries = 0`
- no automatic HTTP replay

This is deliberately fail-closed. Replaying a checkout request can create duplicate checkout sessions or interact badly with rate limits. If a request receives a server response and fails, the runner stops and shows the reason.

Transport retry support remains in the generic runner for future review, but the dashboard and persisted POC task force automatic retry off for this live use.

## Emergency fallback

Keep the browser visible. If runner state becomes `FAILED`, read the error and continue manually in the existing T1 browser if normal site controls are available.

Do not start repeated scripts or multiple runner instances in response to failure.

## Evidence to collect

- target timestamp
- checkout dispatch timestamp
- HTTP status
- `checkoutNumber` (safe to record)
- checkout navigation success
- manual checkpoint reached
- failure reason if any
- dispatch variance from rehearsals

Never paste full checkout page JSON, cookies, session IDs, email, phone number, or payment data into issue logs.
