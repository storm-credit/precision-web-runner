# Adapter Contract v1

## Purpose

A Site Adapter translates generic runner concepts into one site's verified normal flow without changing scheduler, state-machine, lock, or logging semantics.

T1 is Adapter 001. The adapter contract is intentionally narrower than a generic browser scripting language.

## Adapter identity

Every adapter exposes:

```text
id: stable string
version: semantic or monotonically increasing version
supportedOrigins: exact origin allowlist
supportedUrlPatterns: validated patterns
capabilities: declared step families
```

## Configuration schema

Adapter defines typed variables with:
- key
- type
- required
- validation rules
- user-facing label/help
- sensitivity classification
- evidence status: VERIFIED | INFERRED | UNKNOWN

Unknown fields that affect irreversible execution block LIVE ARM.

## Required methods

### `validate(task) -> ValidationResult`
Checks:
- target URL/origin
- required variables
- range/type constraints
- live-only confirmations

Must not perform irreversible network actions.

### `buildPreflight(snapshot) -> StepPlan`
Returns side-effect-free steps only.

Each step declares:
```text
stepId
effect: NONE
origin
method/action
expected safe result
retryPolicy
```

### `buildExecution(snapshot) -> StepPlan`
Returns verified site-specific irreversible and follow-up steps.

Each step declares:
```text
stepId
effect: NONE | IRREVERSIBLE
request/navigation semantic
expected result contract
manual boundary metadata
```

### `parse(stepId, BrowserResult) -> AdapterStepResult`
Returns:
```text
status: PASS | REJECTED | CONTRACT_MISMATCH | AMBIGUOUS
safeData
nextVariables
errorCode?
sideEffectStatus: NONE | CONFIRMED | AMBIGUOUS
```

### `locators(snapshot) -> LocatorSet`
Returns semantic locator strategies ordered from strongest to weakest.

Preferred:
1. accessible role/name
2. stable visible text scoped to expected region
3. stable data attributes
4. stable structural selector

Generated CSS-module hashes are not the sole locator.

### `manualCheckpoint(snapshot) -> ManualCheckpointSpec`
Defines what automated work must stop before final authorization.

## Request safety contract

Adapter-generated request spec must include:
- exact expected origin
- exact method
- exact path pattern
- headers allowlist
- body schema
- credential mode
- effect classification

Core rejects:
- unexpected origin
- adapter attempt to export cookies
- arbitrary Authorization header injection from UI
- arbitrary raw JavaScript recipe text

## Dynamic variable contract

Dynamic values such as checkout identifiers:
- are extracted only from current-run responses
- are scoped to current runId
- are never reused from a prior run as a fallback
- are typed/validated before interpolation into navigation

## Error-classification boundary

Adapter may map a site response into semantic meaning, but Core Error Policy decides retry/stop safety.

Example:
- adapter: HTTP 403 -> `REJECTED/AUTHORIZATION`
- core: irreversible step rejection -> stop, no retry

Adapter cannot mark an ambiguous irreversible outcome as safe-to-retry unless idempotency is proven and explicitly approved in design.

## T1 Adapter 001 contract baseline

### Verified from observed flow
- origin: `https://t1.fan`
- checkout endpoint: `/svc/shop/api/v1/order/checkout`
- method: POST
- response contains dynamic `checkoutNumber` on observed success
- checkout navigation uses `/shop/checkout/{checkoutNumber}`

### Signature item facts previously observed
- target product URL: `/shop/products/525`
- `inventoryItemId = 3454`
- amount `500000 KRW`

### Still blocking LIVE
- Signature-specific `shippingType` independently verified from the exact live product flow

### Important distinction
A `paymentOptionId` was observed in a cart request, but the direct checkout payload observed later did not require it. The adapter must follow the verified direct-checkout contract, not merge fields from unrelated request shapes without evidence.

## Consent contract

Adapter may expose an optional consent locator only if:
- the user has explicitly configured pre-authorized handling
- the text/meaning matches the consent the user intends to accept
- locator is unambiguous

Failure to locate consent never authorizes a coordinate guess.

## Payment handoff contract

Adapter may open the site's normal payment UI. It must not define steps for:
- card data entry
- OTP
- 3DS
- final simple-payment approval
- equivalent financial authorization

## Adapter health/versioning

Before ARM, record adapter version in the snapshot.

If target-site behavior materially changes:
- mark adapter `UNVERIFIED`
- block LIVE ARM
- update evidence
- increment adapter version
- rerun relevant acceptance tests

## Generalization test

Adapter v1 is accepted only if a second future adapter can implement these methods without changing Core scheduler/state/lock/event contracts.