# Component Contracts v1

## Contract rule

Components communicate through explicit typed inputs/outputs. A component must not reach through another layer to access private implementation details.

## 1. Dashboard / Control UI

### Responsibilities
- display runner/device state
- edit TaskDefinition while not armed
- request test/preflight/arm/disarm
- render events and manual checkpoint actions

### Inputs
- RunnerStatus
- TaskDefinition
- RunEvents

### Outputs
- SaveTask(command)
- OpenBrowser(command)
- Preflight(command)
- Arm(command)
- Disarm(command)
- ManualContinue(command)

### Forbidden
- target-site cookies
- direct target-site API calls
- precision timer authority
- changing an ArmedRunSnapshot

## 2. Local Control API

### Responsibilities
- validate caller is local/trusted for POC
- serialize commands to RunnerService
- return redacted status

### Contract
Every mutating command returns:
- accepted: boolean
- currentState
- runId if relevant
- safe error code/message on rejection

### Forbidden
- raw browser storage/cookies in API responses
- exposing arbitrary command execution

## 3. RunnerService / Orchestrator

### Responsibilities
- own state machine
- create immutable ArmedRunSnapshot
- own one-run execution lease
- invoke scheduler, browser bridge, and adapter
- enforce stop/retry policy
- emit structured events

### Inputs
- validated TaskDefinition
- user commands
- SchedulerSignal
- BrowserResult
- AdapterResult

### Outputs
- state transitions
- RunEvents
- BrowserCommands

### Invariants
- one active irreversible lease per run
- task cannot mutate active snapshot
- every state transition has reason + timestamp

## 4. Scheduler

### Input
```text
ScheduleRequest {
  runId,
  targetInstant,
  prewarmLead,
  maxLateness,
  cancellationToken
}
```

### Output
```text
SchedulerSignal = PREWARM_DUE | TARGET_DUE | CANCELLED | LATE | CLOCK_DISCONTINUITY
```

### Responsibilities
- derive monotonic deadline from wall-clock target at ARM
- notify prewarm and target
- detect sleep/wake discontinuity
- measure wake lateness

### Forbidden
- target-site calls
- retries
- browser control

## 5. BrowserBridge

### Responsibilities
- own dedicated persistent browser context
- open/navigate target pages
- run allow-listed page-context actions
- return safe structured results

### Representative commands
```text
Open(url)
Navigate(url)
SameOriginRequest(requestSpec)
FindSemantic(locatorSpec)
Check(locatorSpec)
Click(locatorSpec)
ObservePage()
```

### Output
```text
BrowserResult {
  ok,
  category,
  httpStatus?,
  finalUrl?,
  safeBodyText?,
  safeData?,
  reason?
}
```

`safeBodyText` must be bounded and redacted before persistence.

### Forbidden
- exporting cookie jar
- arbitrary JS from user-stored recipes
- cross-origin credential forwarding

## 6. Site Adapter v1

### Responsibilities
- validate target URL and variables
- construct site-specific request specs
- parse site-specific responses
- provide semantic locator strategies
- classify known response semantics without weakening core safety policy

### Core interface
```text
validate(task) -> ValidationResult
preflightPlan(snapshot) -> AdapterPlan
executionPlan(snapshot) -> AdapterPlan
parse(stepId, BrowserResult) -> AdapterStepResult
manualCheckpoint(snapshot) -> ManualCheckpointSpec
```

See `design/ADAPTER_SPEC.md`.

## 7. EventLogger

### Input
```text
RunEvent {
  runId,
  at,
  level,
  state,
  stepId?,
  code,
  message,
  safeDetail
}
```

### Responsibilities
- redact secrets/PII
- enforce size limits
- append locally
- preserve event ordering per run

### Forbidden fields
- Cookie
- Set-Cookie
- Authorization
- CSRF/nonce values
- email/phone/address from checkout data
- full HTML/JSON response dump
- payment credentials

## 8. Local Store

### Responsibilities
- persist editable TaskDefinition
- persist immutable ArmedRunSnapshot metadata
- persist redacted events and measurements

### Atomicity
ARM snapshot and runId creation must be written atomically before scheduler activation.

## 9. Manual Payment Handoff

### Input
- checkout page ready
- optional consent already handled according to policy

### Output
- `WAITING_MANUAL` state
- visible browser/payment UI

### Contract
The runner reports handoff success only when the expected user-facing payment surface is visible or a clearly defined checkout manual checkpoint is reached. It must not report `SUCCEEDED` merely because checkoutNumber exists.

## 10. Contract versioning

Every Adapter and ArmedRunSnapshot records a contract/version string. An armed run must continue with the version it was validated against; silently switching adapter versions mid-run is forbidden.