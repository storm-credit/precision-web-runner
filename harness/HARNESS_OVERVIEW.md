# Project Harness Overview

## Purpose

The harness exists to prevent fast code generation from outrunning product reasoning. It turns the user's preferred AI-working method into repository-enforced checkpoints.

The harness is **process architecture**, not runtime architecture.

## Principles adopted

### Karpathy-style operating rules
- think before coding
- expose assumptions
- prefer the simplest sufficient design
- make surgical changes
- define verifiable success criteria
- do not claim completion without evidence

### Superpowers-style delivery flow
- brainstorm / understand
- design
- approve
- plan
- test
- implement minimally
- review against spec
- verify actual behavior

### Repository-native memory
Use files before adding external memory infrastructure:
- `CLAUDE.md` — permanent constitution
- `status/CURRENT_STATUS.md` — phase and known facts
- `status/NEXT_ACTION.md` — one next objective
- `docs/DECISIONS_AND_INTERVIEW.md` — decisions/assumptions/questions
- `docs/DEVIATIONS.md` — changes from approved plan
- `verification/*` — evidence and release gates

## Roles

These are review lenses. They need not be separate running agents during the POC.

### Project Orchestrator
Owns scope, gate order, contradiction detection, and final synthesis.

### Product / Requirements Architect
Checks that the design serves the actual user goal and does not drift into future-platform work.

### Browser Automation Architect
Challenges session strategy, origin boundaries, browser lifecycle, selector stability, page-context execution, popup/navigation behavior.

### Timing / Reliability Architect
Challenges clock authority, monotonic scheduling, prewarm, sleep/wake, network jitter, duplicate dispatch, late execution.

### Security Reviewer
Challenges cookie handling, local API exposure, CSRF/session leakage, arbitrary recipe execution, log redaction, payment boundaries.

### UI / UX Architect
Checks first-viewport value, state clarity, test/live distinction, destructive-action confirmation, responsive behavior, real CTA behavior.

### Verification Reviewer
Checks acceptance criteria, evidence quality, rehearsal coverage, and whether implementation claims are reproducible.

## Required artifacts by phase

### Design phase
- system design
- contracts
- state machine
- sequences
- error policy
- timing design
- security model
- adapter spec
- UI spec

### Implementation-ready phase
- accepted decisions
- implementation reconciliation plan
- acceptance matrix
- test plan

### Live-ready phase
- rehearsal evidence
- timing measurements
- session persistence proof
- exact target contract confirmed
- POC Go/No-Go PASS

## Harness invariant

A later phase may add detail, but it may not silently weaken an earlier safety or scope rule. Any weakening requires an explicit decision and deviation record.