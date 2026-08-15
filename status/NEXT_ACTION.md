# Next Action

## Single next objective

**R5 — Generic BrowserBridge + Typed BrowserResult.**

R4 Adapter Contract passed. Do not begin R6 orchestration/error/retry migration inside R5 except for a minimal compatibility seam.

## Read first

1. `status/CURRENT_STATUS.md`
2. `verification/R4_ADAPTER_REVIEW.md`
3. `design/IMPLEMENTATION_READY_PLAN.md` — R5
4. `design/COMPONENT_CONTRACTS.md` — BrowserBridge
5. `design/SECURITY_MODEL.md`
6. `design/BROWSER_LIFECYCLE.md`
7. `design/ADAPTER_SPEC.md`
8. `harness/IMPLEMENTATION_GATE_CHECKLIST.md`

## R5 Gap IDs

- G09 generic BrowserBridge
- G10 typed safe BrowserResult
- partial foundation for G25 profile ownership diagnosis

## Tests first

Specify tests for:
- exact origin allowlist enforcement
- same-origin credential requests only
- request spec cannot redirect credentials to another origin
- bounded safe response body/result
- no cookie/Authorization export
- generic navigation using adapter NavigationSpec + current-run variable
- semantic locator handling without site-specific imports
- dedicated persistent profile configuration
- profile-lock/launch errors distinguishable from generic browser failure where possible

## Allowed scope

- browser bridge/worker module(s)
- BrowserResult types
- browser unit tests using injected/fake page seams
- minimal compatibility wrapper for current RunnerService

No T1 request construction inside BrowserBridge. No R6 retry/orchestrator policy, UI, cloud, LAN control, or payment authorization.

## Completion condition

R5 ends when:
- BrowserBridge has no T1Adapter import
- target requests come from declarative RequestSpec
- typed/bounded BrowserResult is used on the forward path
- exact-origin and credential guards are tested
- full CI passes
- R5 review evidence is recorded

Then R6 becomes eligible.
