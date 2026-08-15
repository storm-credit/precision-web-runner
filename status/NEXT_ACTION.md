# Next Action

## Single next objective

**R4 — Adapter Contract + T1 Adapter Migration.**

R1-R3 passed independently and Checkpoint C1 passed. R4 is now eligible. Do not begin R5 BrowserBridge refactor or R6 orchestration cleanup inside this slice unless a minimal compile seam is unavoidable and explicitly documented.

## Read first

1. `status/CURRENT_STATUS.md`
2. `verification/C1_FOUNDATION_REVIEW.md`
3. `design/IMPLEMENTATION_READY_PLAN.md` — R4 section
4. `design/ADAPTER_SPEC.md`
5. `design/COMPONENT_CONTRACTS.md` — Site Adapter
6. `design/ERROR_POLICY.md`
7. `design/SECURITY_MODEL.md`
8. `docs/T1_EVIDENCE.md`
9. `harness/IMPLEMENTATION_GATE_CHECKLIST.md`

## R4 goals

Move T1 knowledge behind Adapter v1:
- adapter id/version/origin allowlist
- typed adapter variable schema
- evidence status VERIFIED / INFERRED / UNKNOWN
- validate(task/snapshot)
- side-effect-free preflight plan
- execution plan with explicit effect classification
- response parsing to semantic AdapterStepResult
- semantic locator strategies
- manual payment checkpoint
- dynamic checkoutNumber scoped to the current run

## T1 evidence discipline

Verified observations may be encoded as VERIFIED.

Signature-specific `shippingType` remains UNKNOWN until independently confirmed from the exact product flow. UNKNOWN facts that affect irreversible LIVE execution must block LIVE ARM; never fill them from the normal-item example.

Do not merge cart-only `paymentOptionId` into the direct checkout contract without evidence.

## Tests first

Before migration, specify tests for:
- exact supported origin / URL validation
- generic variable schema with evidence status
- LIVE validation blocks UNKNOWN irreversible fields
- direct checkout request plan matches verified request shape
- checkoutNumber parser accepts current-run success and rejects missing/invalid shape
- 401/403/429/server rejection semantic classifications do not imply retry/bypass
- dynamic checkoutNumber is never hardcoded/reused
- locator set prioritizes semantic role/text over generated CSS hashes
- final payment authorization is outside adapter capabilities

## Allowed implementation scope

- `src/precision_runner/t1_adapter.py`
- narrow new adapter contract/types module if needed
- adapter tests
- minimal model/service compatibility seam required to compile/use the new adapter

No general BrowserBridge rewrite, UI redesign, cloud/mobile control, or final-payment automation belongs in R4.

## Completion condition

R4 ends only after:
- full unit suite passes
- Core no longer needs T1 product/request field knowledge for new adapter contract paths
- all T1 facts are labeled by evidence status
- UNKNOWN Signature shippingType remains a visible LIVE blocker
- adapter cannot weaken Core retry/safety policy
- R4 review evidence is recorded

Then R5 becomes eligible.
