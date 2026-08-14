# T1 Adapter 001 — Observed Evidence

This document records only the sanitized behavior observed during manual browser inspection. It is evidence for the POC design, not a guarantee that the site contract will remain unchanged.

## Observed cart payload shape

A T1 cart request was observed with this general shape:

```json
{
  "items": [
    {
      "inventoryItemId": 3454,
      "quantity": 1,
      "paymentOptionId": 3461,
      "unitPrice": {
        "currencyCode": "KRW",
        "amount": 500000
      }
    }
  ]
}
```

For the Signature Edition observation:
- `inventoryItemId`: `3454`
- `paymentOptionId`: `3461`
- amount: `500000 KRW`

These are adapter/task data, never core-runner constants.

## Observed checkout creation behavior

On a separate normally purchasable test item, the cart/order UI called:

```http
POST /svc/shop/api/v1/order/checkout
```

Observed request body shape:

```json
{
  "inventoryItemAndQuantities": [
    {
      "inventoryItemId": 3229,
      "quantity": 1,
      "unitPrice": {
        "currencyCode": "KRW",
        "amount": 49000
      },
      "shippingType": "STANDARD_DELIVERY"
    }
  ]
}
```

Observed successful response shape:

```json
{
  "checkoutNumber": 2438052376391680
}
```

The browser then navigated to a route shaped like:

```text
/shop/checkout/{checkoutNumber}
```

## Important uncertainty

Do **not** assume the Signature Edition uses the same `shippingType` until it is observed/validated.

Do **not** assume `paymentOptionId` is required in the direct checkout payload simply because it appeared in the cart payload.

Do **not** hardcode an old `checkoutNumber`; it is dynamic.

## Checkout UI evidence

The checkout page contains a consent step corresponding to the text:

```text
주문 내용과 약관에 동의합니다
```

A payment button exists after the consent state becomes valid.

Generated CSS-module class names were observed, but they are not considered stable selectors. The adapter should prefer semantic text/role/DOM relationships and keep CSS-hash selectors only as last-resort diagnostics.

## Safety boundary

The POC may replay an allowed checkout action **only after the target site normally permits that action for the authenticated user**.

If the server rejects the request because of membership, sale time, stock, authorization, queue, or another rule, the adapter stops and reports the rejection. It does not modify the frontend or request to evade the rule.

## First T1 POC flow

```text
ARM
 -> preflight authenticated T1 page/session
 -> target-time scheduler fires
 -> same-origin checkout request
 -> receive checkoutNumber
 -> navigate /shop/checkout/{checkoutNumber}
 -> wait for checkout UI
 -> configured consent step
 -> manual final-payment checkpoint
```

## Redaction rule

Captured checkout page data may contain user profile/contact fields. Never commit or log full page JSON, cookies, session IDs, phone numbers, email addresses, names, payment data, or authorization material.
