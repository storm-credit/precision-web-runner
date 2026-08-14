# Decisions & Interview

This file captures what is already clear from the conversation and separates it from assumptions that still need confirmation before implementation.

## Inferred intent

The user wants a practical tool that can:
- prepare a timed web action in advance
- execute automatically at a target time
- work through a logged-in browser session
- show a clear web/mobile control UI
- begin with T1 but later support other target URLs through reusable recipes/adapters

The immediate goal is a **POC**, not a full SaaS platform.

## Primary user

Current assumption:
- primary user: the repository owner / one trusted individual
- device: Windows PC
- mobile: secondary control/monitor screen

This avoids prematurely designing multi-user authentication, teams, billing, or cloud secret storage.

## Product decisions already accepted

- Repository: `storm-credit/precision-web-runner`
- Product working name: Precision Web Runner / Precision Runner
- First adapter: T1 Membership
- UI: Concept 02 light responsive dashboard
- T1 must not be hardcoded into core modules
- Target URLs become configurable through Tasks + Recipes, not URL-only magic
- Design-first workflow
- Blindspot sweep before implementation
- Pre-implementation trap gate
- Plan deviations must be recorded
- Final payment is manual by default
- Server-side restrictions are not bypassed

## POC assumptions to use unless the user changes them

1. The Windows PC can remain powered on and awake while a task is armed.
2. The user can log into T1 manually before arming.
3. The POC may use a dedicated browser profile if that is safer/more reliable than attaching to the user's everyday profile.
4. The phone and PC can be on the same trusted network for POC mobile control.
5. One task runs at a time.
6. Local storage is acceptable for POC task/run metadata.
7. The POC stops before final payment authorization.

## Questions to resolve before implementation lock

These questions should be asked only when their answer becomes necessary; they do not block the current design documentation.

### Q1. Browser session strategy

Preferred choice?
- A. dedicated automation Chrome profile (recommended for repeatability)
- B. attach to currently open everyday Chrome

### Q2. Mobile control scope

Is same-Wi-Fi local access sufficient for the POC, or must the phone be able to arm/check the runner from outside the home network?

Recommended POC default: same trusted network only.

### Q3. Consent behavior

The checkout consent step can technically be configured as an automated click once the user has reviewed and accepted the applicable terms. Should the POC:
- A. auto-click that configured consent step
- B. stop there for user confirmation

Current design supports either; final payment remains manual.

### Q4. Timing policy

Should the target dispatch be:
- exact configured local time based on synchronized PC clock
- configurable offset (for example target + N ms) after measurements

Recommended: start with exact synchronized target and log measured error; only add offset after evidence.

### Q5. Retry policy

Recommended safe default:
- one primary attempt
- at most a small bounded number of retries only for explicitly retryable transport/server errors
- never retry an ambiguous success automatically

Exact numbers should be chosen after the architecture spike.

## Interview completion rule

Before implementation begins, convert unresolved answers into explicit decisions in this file. Do not leave an important execution/security choice as an implicit assumption in code.
