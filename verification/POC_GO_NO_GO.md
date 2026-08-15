# POC Go / No-Go Gate

## Decision statuses

- `PASS` — verified with evidence
- `BLOCKED` — known failure or missing prerequisite
- `UNKNOWN` — not yet tested; treated as blocked for LIVE
- `N/A` — explicitly not applicable with rationale

## A. Design gate

- [ ] PASS Component contracts approved
- [ ] PASS State machine approved
- [ ] PASS Error/ambiguity policy approved
- [ ] PASS Timing policy approved
- [ ] PASS Security model approved
- [ ] PASS Adapter v1 contract approved
- [ ] PASS UI state/CTA specification approved
- [ ] PASS Acceptance matrix approved

Any unchecked design item = NO-GO for implementation reconciliation.

## B. Target contract gate — T1 Signature

- [x] target origin known: `https://t1.fan`
- [x] target product path known: `/shop/products/525`
- [x] observed Signature inventoryItemId: `3454`
- [x] observed amount: `500000 KRW`
- [x] observed checkout endpoint contract from normal item
- [x] observed dynamic `checkoutNumber` response behavior from normal item
- [ ] **Signature-specific `shippingType` verified from exact product flow**
- [ ] target-site flow materially unchanged at rehearsal time

Until the two unchecked rows pass: LIVE = NO-GO.

## C. Local environment gate

- [ ] Windows clock sync confirmed
- [ ] sleep/hibernate disabled for live window
- [ ] stable network selected
- [ ] Python/runtime dependencies verified
- [ ] dedicated Chrome profile opens
- [ ] profile ownership/duplicate runner behavior verified
- [ ] T1 login persists in dedicated profile
- [ ] dashboard bound only to approved interface (localhost by default)

## D. Safe rehearsal gate

- [ ] safe preflight PASS
- [ ] safe checkout response/parse PASS
- [ ] dynamic checkout navigation PASS
- [ ] no automatic irreversible replay observed
- [ ] consent policy behaves as configured
- [ ] manual payment handoff reached
- [ ] final authorization remains manual
- [ ] logs inspected and contain no secrets/PII

## E. Timing gate

- [ ] at least 5 safe scheduled rehearsals
- [ ] dispatch lateness values recorded
- [ ] worst observed lateness reviewed
- [ ] maxLatenessMs explicitly chosen from evidence
- [ ] sleep/wake behavior tested or safely prevented for live window
- [ ] no intentional pre-opening dispatch offset

## F. Failure gate

Verify at least:
- [ ] logged-out preflight fails closed
- [ ] server 4xx fails closed
- [ ] missing checkoutNumber fails closed
- [ ] ambiguous transport does not replay checkout automatically
- [ ] navigation failure after known checkout does not create a second checkout
- [ ] duplicate ARM/run is blocked

## G. UX gate

- [ ] TEST vs LIVE mode unmistakable
- [ ] target item/amount/time visible before ARM
- [ ] all ARM blockers visible by reason
- [ ] mobile/narrow first viewport shows target/time/state/CTA
- [ ] RUNNING does not offer a misleading undo/cancel after dispatch
- [ ] WAITING_MANUAL clearly says final payment is manual

## H. Day-of-live gate

Immediately before ARM:
- [ ] exact task snapshot reviewed
- [ ] target time = published permitted opening time
- [ ] adapter version matches rehearsed version
- [ ] browser already logged in
- [ ] preflight passes
- [ ] no duplicate runner instance
- [ ] no unresolved BLOCKED/UNKNOWN mandatory acceptance row

## Decision rule

### GO
Only when all mandatory design, target, environment, rehearsal, timing, failure, UX, and day-of-live items are PASS.

### CONDITIONAL GO is not supported
For this POC, an UNKNOWN mandatory item is a NO-GO rather than a guessed approval.

### NO-GO
If any mandatory gate is BLOCKED/UNKNOWN, use manual normal site flow or fix/rehearse before target. Do not compensate with bypasses, repeated requests, or unreviewed last-minute code changes.

## Current status at Deep Design creation

**NO-GO / DESIGN IN REVIEW.**

Reason:
- deep design still awaiting review/approval
- Signature `shippingType` still unverified
- Windows/browser live rehearsal not yet performed
- timing variance not yet measured

This status is expected and should not be changed to GO merely because unit tests pass.