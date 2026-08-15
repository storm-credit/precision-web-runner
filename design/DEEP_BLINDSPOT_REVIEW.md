# Deep Blindspot Review v1

This is the second-pass review after high-level design and the Architecture Spike. It focuses on hidden failure modes that the first blindspot sweep did not fully contract.

## Findings

### B1 — Implementation became the accidental source of truth
**Severity: BLOCKER — RESOLVED by design freeze**

Risk:
- prototype choices could silently define architecture before contracts were reviewed.

Resolution:
- existing runtime classified as Architecture Spike
- `CLAUDE.md` freezes runtime changes
- future implementation begins with KEEP / CHANGE / DELETE reconciliation

### B2 — Generic retry field can be unsafe for irreversible steps
**Severity: BLOCKER — RESOLVED in design**

Risk:
- a transport timeout does not prove checkout POST failed server-side
- replay can duplicate side effects

Resolution:
- Error Policy is per-step, not global retry count
- irreversible checkout automatic replay OFF by POC default
- ambiguity -> manual inspection

### B3 — Remote phone control adds an unnecessary attack surface
**Severity: MAJOR — RESOLVED for POC**

Risk:
- LAN binding requires authentication, pairing, CSRF/cross-origin protections
- responsive UI was being conflated with remote execution control

Resolution:
- localhost-only live control baseline
- mobile/narrow responsive design retained
- remote phone control deferred

### B4 — ARM must snapshot configuration
**Severity: BLOCKER — RESOLVED in design, implementation must be reconciled**

Risk:
- editing item/time/policy while armed can make UI intent differ from executed intent

Resolution:
- immutable ArmedRunSnapshot at ARM
- edits require disarm/re-arm

### B5 — Cancel semantics are dangerous after dispatch
**Severity: MAJOR — RESOLVED in state/UI design**

Risk:
- UI saying “cancelled” after request is in flight creates false confidence

Resolution:
- no generic undo/cancel once irreversible dispatch begins
- ambiguous result remains RUNNING/FAILED with explicit side-effect status

### B6 — Checkout success vs navigation success vs purchase success were conflated
**Severity: BLOCKER — RESOLVED in semantics**

Resolution:
- checkoutNumber = checkout creation evidence only
- navigation is separate step
- WAITING_MANUAL = automation handoff
- payment success is outside automated POC objective
- no inference of inventory reservation

### B7 — Process restart can silently replay stale work
**Severity: BLOCKER — RESOLVED in design, rehearsal needed**

Resolution:
- ambiguous RUNNING recovery never auto-replays
- ARMED recovery requires explicit policy/fresh preflight
- persisted snapshot/state drive safe recovery

### B8 — Logging safe status can still leak PII through response text
**Severity: MAJOR — RESOLVED in observability design**

Resolution:
- allowlisted structured safe fields
- redaction before persistence
- no full response body/checkout JSON
- rehearsal log inspection mandatory

### B9 — `checkoutNumber` itself could be treated as harmless without proof
**Severity: MINOR — ACCEPTED local-only assumption with caution**

Policy:
- local log only
- never expose publicly
- if evidence shows it acts as secret, reclassify and redact

### B10 — Server “not open yet” handling can tempt pre-opening timing offsets
**Severity: BLOCKER — RESOLVED in timing design**

Resolution:
- target = published permitted opening instant
- no intentional early dispatch to compensate latency
- server rejection remains authoritative

### B11 — Browser profile can be locked/corrupted by multiple instances
**Severity: MAJOR — RESOLVED contractually, rehearsal needed**

Resolution:
- single profile owner
- second runner blocked
- profile-lock behavior in acceptance matrix

### B12 — Session “looks logged in” is not a stable contract
**Severity: MAJOR — PARTIALLY RESOLVED**

Resolution:
- preflight must use non-PII session/origin/contract markers

Remaining:
- exact T1-safe authentication marker must be proven during Windows rehearsal without storing PII.

### B13 — T1 request fields observed across different endpoints can be accidentally merged
**Severity: BLOCKER — RESOLVED in Adapter Spec**

Example:
- `paymentOptionId` observed in cart request
- direct checkout payload observed without it

Resolution:
- never merge unrelated request shapes without direct evidence
- Adapter follows verified endpoint-specific contract

### B14 — Signature `shippingType` remains an unverified assumption
**Severity: LIVE BLOCKER — OPEN**

Resolution required:
- verify from exact target product's normal flow before LIVE ARM

Do not infer from the 49,000 KRW test item.

### B15 — Timing “precision” is meaningless without Windows measurements
**Severity: LIVE BLOCKER — OPEN**

Resolution required:
- >=5 safe scheduled rehearsals
- record dispatch lateness and response latency
- choose max-lateness policy from evidence

### B16 — Last-minute site deploy can invalidate all rehearsals
**Severity: MAJOR / LIVE CHECK**

Resolution:
- Adapter version/health status
- re-run safe preflight/contract check near live window
- material mismatch -> NO-GO, not emergency guessing

### B17 — Semantic locator can match the wrong repeated text
**Severity: MAJOR — RESOLVED in UI/Adapter contract**

Resolution:
- locator uniqueness + expected page/origin scope
- no broad first-match text click
- no coordinate fallback

### B18 — Dashboard can show stale state after runner restart
**Severity: MAJOR — IMPLEMENTATION RECONCILIATION ITEM**

Design requirement:
- state served from authoritative RunnerService/persisted run record
- UI refresh/poll reconnect must show recovery-required state rather than default READY if an ambiguous run existed

### B19 — Event persistence failure can destroy recovery evidence
**Severity: MAJOR — RESOLVED in component contract**

Resolution:
- snapshot persistence is atomic prerequisite for ARM
- critical persistence failure blocks irreversible dispatch when safe recovery would otherwise be impossible

### B20 — Test/live contamination
**Severity: BLOCKER — RESOLVED in UX/domain design**

Resolution:
- TEST/LIVE explicit mode
- live confirmation repeats target/amount/time/adapter version
- no silent promotion from test to live

## Open design blockers

None identified after the current document set, assuming the localhost-only control baseline is accepted.

## Open LIVE blockers

- exact Signature `shippingType`
- Windows dedicated-profile/session rehearsal
- timing variance measurements
- current T1 contract freshness

These are evidence blockers, not reasons to resume coding before design approval.