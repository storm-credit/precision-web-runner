# Product Design

## Product idea

Precision Web Runner is a scheduled web-action runner. A user creates a task with a target URL, target time, and a site recipe. The local runner executes the recipe in an already-authenticated browser context.

For the POC, only one recipe is implemented: T1 Adapter 001.

## Core user flow

1. Open dashboard.
2. Confirm runner device is connected.
3. Select/create task.
4. Confirm target URL and target time.
5. Run a safe test.
6. ARM the task.
7. Preflight begins before the target.
8. Runner executes the recipe at target time.
9. UI shows each step and timing.
10. Runner reaches a manual final-payment checkpoint.
11. User finishes payment manually.

## Responsive UX

Selected direction: **Concept 02 — light dashboard**.

### Desktop

Primary layout:
- left navigation
- top connection/time status
- task summary
- target time
- runner state
- recipe steps
- Test / ARM / Cancel CTA area
- run log

### Mobile

The first viewport must show, without scrolling if practical:
- task/target
- target time
- runner state
- device connection
- primary CTA

Detailed recipe and logs can be below the fold.

## Primary states

```text
DRAFT
  -> TESTED
  -> ARMED
  -> PREFLIGHT
  -> RUNNING
  -> WAITING_MANUAL
  -> SUCCEEDED
  -> FAILED
  -> CANCELLED
```

A state transition always records a timestamp and reason.

## CTA rules

- DRAFT: `테스트 실행`
- TESTED: `ARM`
- ARMED: `ARM 해제 / 취소`
- PREFLIGHT: `취소`
- RUNNING: show progress; destructive cancel requires confirmation
- WAITING_MANUAL: `결제 계속하기` / `중단`
- FAILED: `로그 보기` / bounded `다시 시도`

Do not show a CTA that has no real implementation.

## Generalization model

The product should not hardcode T1 into core screens or data models.

A Task contains:
- id
- name
- targetUrl
- targetTime
- timezone
- recipeId
- recipeVariables
- executionDeviceId
- retryPolicy
- status

A Recipe contains:
- supported URL patterns
- variable schema
- ordered steps
- stop conditions
- safety metadata
- version

A Run contains:
- taskId
- targetAt
- armedAt
- preflightAt
- requestStartedAt
- responseReceivedAt
- currentStep
- result
- stopReason
- redacted step logs

## POC usability success

- A first-time user can understand what will happen before pressing ARM.
- Test mode is visually distinct from live mode.
- The target time and execution device are obvious.
- The manual-payment boundary is obvious.
- On failure, the user sees which step failed instead of only a generic error.
