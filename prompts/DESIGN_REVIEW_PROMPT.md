# Deep Design Review Prompt

Use this prompt before any implementation reconciliation.

## Context Dump

Read in this order:
1. `CLAUDE.md`
2. `status/CURRENT_STATUS.md`
3. `status/NEXT_ACTION.md`
4. `docs/POC_SCOPE.md`
5. `docs/DECISIONS_AND_INTERVIEW.md`
6. `docs/T1_EVIDENCE.md`
7. `design/*`
8. `harness/*`
9. `verification/*`
10. `docs/DEVIATIONS.md`

Treat existing runtime code as Architecture Spike evidence, not as the design source of truth.

## Goal Prompt

```text
Goal:
Review the Precision Web Runner deep-design baseline for the narrow T1 POC and determine whether it is implementation-ready.

Success conditions:
- identify contradictions between design documents
- identify hidden assumptions
- verify component boundaries are implementable
- verify state/error/timing/security policies are mutually consistent
- verify T1-specific facts are separated from generic core contracts
- verify UI behavior matches state/error policy
- verify acceptance matrix can prove the design
- classify every finding BLOCKER / MAJOR / MINOR / NOTE
- produce an explicit DESIGN PASS or DESIGN FAIL

Stop conditions:
- do not modify runtime code
- do not broaden scope into SaaS/general URL automation
- do not invent missing target-site facts
- do not weaken restriction/payment safety boundaries
- if a material user decision is truly required, ask only that question and explain why it changes the design
```

## Review lenses

### Product
Does the design solve the immediate 17 Aug POC rather than future-platform fantasies?

### Browser
Are session lifecycle, profile ownership, origin, popup, and navigation failure cases explicit?

### Timing
Are target clock, monotonic deadline, prewarm, late policy, sleep and measurement explicit?

### Reliability
Can duplicate and ambiguous irreversible actions be prevented?

### Security
Can the system work without cookie export, arbitrary eval, LAN exposure by default, or final payment automation?

### Adapter architecture
Can a second adapter later be added without rewriting scheduler/state/lock/event contracts?

### UX
Does each state expose the correct CTA and avoid misleading retry/cancel behavior?

### Verification
Does every critical claim map to an acceptance test or live rehearsal artifact?

## Result Verification

Before reporting PASS:
- every BLOCKER resolved
- every MAJOR resolved or explicitly accepted with rationale
- no document still treats unknown `shippingType` as verified
- no document allows generic automatic checkout POST retry in the live POC
- no document claims phone/LAN control is required for POC
- no document claims millisecond/server-synchronized accuracy
- no document equates checkout creation with inventory reservation or payment success

Output a compact finding table followed by final verdict and the exact next action.