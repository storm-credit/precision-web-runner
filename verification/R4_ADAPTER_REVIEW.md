# R4 Adapter Contract + T1 Adapter Migration Review

## Verdict

**R4 SLICE: PASS.**

This approves the adapter contract/migration slice only. It does not approve BrowserBridge execution, orchestration, or LIVE use.

## Gap coverage

- G11 adapter identity/version/evidence health: implemented
- G12 Signature shippingType LIVE blocker: preserved and made explicit
- preparation for G09/G10 by making adapter output declarative plans instead of browser-owned T1 logic

## Tests-first evidence

`tests/test_adapter_contract.py` was committed before the generic contract/T1 migration implementation.
It verifies:
- exact adapter identity/version/origin
- typed variable schema
- VERIFIED/INFERRED/UNKNOWN evidence enum
- unsupported origin rejection
- LIVE UNKNOWN shippingType blocker
- irreversible execution refuses UNKNOWN shippingType even in TEST mode
- direct checkout plan matches observed request shape
- no cart-only paymentOptionId in direct checkout plan
- preflight is side-effect-free GET
- dynamic checkoutNumber parsed only from current response
- missing/invalid checkoutNumber -> CONTRACT_MISMATCH + AMBIGUOUS
- 401/403/429/5xx semantic rejection without adapter retry flag
- semantic locators instead of generated CSS hashes
- manual final-payment boundary

`tests/test_t1_evidence_contract.py` additionally verifies:
- observed Signature inventoryItemId=3454 and amount=500000 are marked VERIFIED
- Signature shippingType remains UNKNOWN unless explicitly verified
- unobserved item/price pairs are INFERRED, never silently VERIFIED
- cart-only paymentOptionId is not part of the execution variable schema

## Implementation result

New `src/precision_runner/adapter_contract.py` defines immutable generic adapter types:
- EvidenceStatus
- StepEffect
- AdapterParseStatus
- AdapterVariableSpec
- ValidationResult/Issue
- RequestSpec / NavigationSpec / AdapterStep / AdapterPlan
- AdapterStepResult
- semantic LocatorStrategy/LocatorSet
- ManualCheckpointSpec

`T1Adapter` now exposes:
- stable id `t1`, version `1.0.0`
- exact supported origin `https://t1.fan`
- supported product URL prefix
- declared capabilities that exclude final payment authorization
- typed variable schema and evidence rules
- side-effect-free preflight plan
- irreversible direct-checkout plan
- semantic response parser
- dynamic checkout navigation contract
- semantic consent/payment locators
- manual final-payment checkpoint

## Evidence boundaries

The adapter explicitly keeps these distinctions:
- Signature `inventoryItemId=3454`: VERIFIED observation
- Signature `amount=500000 KRW`: VERIFIED observation
- Signature `shippingType`: UNKNOWN until exact-product evidence exists
- normal test item `STANDARD_DELIVERY`: not promoted to Signature evidence
- cart `paymentOptionId=3461`: not injected into direct checkout request
- checkoutNumber: current response only; no default/old fallback

## Retry / rejection boundary

AdapterStepResult intentionally has no generic `retryable` field.
The adapter may classify site semantics, but Core Error Policy owns retry/stop behavior.

For create_checkout:
- 401 -> AUTHENTICATION
- 403 -> AUTHORIZATION
- 429 -> RATE_LIMITED
- other non-2xx -> SERVER_REJECTION
- 2xx with missing/invalid checkoutNumber -> CONTRACT_MISMATCH / AMBIGUOUS

No classification authorizes bypass or replay.

## Transitional compatibility

Legacy methods (`validate_target`, `checkout_payload`, `parse_checkout`, `checkout_url`) remain temporarily because pre-R5/R6 BrowserWorker/RunnerService still call them.
They are compatibility shims, not the forward contract.

R5 migrates browser execution to generic RequestSpec/LocatorStrategy commands.
R6 migrates orchestration to AdapterPlan/AdapterStepResult and then removes the generic retry-oriented spike path.

## Verification evidence

GitHub Actions run `31900441910` completed successfully:
- package install: PASS
- full unittest suite: PASS

## Safety review

PASS:
- no permission/sale-time/membership bypass
- no CAPTCHA/queue/rate-limit evasion
- no cookie/token export
- no hardcoded checkoutNumber reuse
- no generated CSS hash as sole locator
- no final payment/card/OTP/3DS automation
- UNKNOWN shipping contract blocks irreversible execution

## Next action

R5 — Generic BrowserBridge + typed BrowserResult.
