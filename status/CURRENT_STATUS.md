# Current Status

## Phase

**DEEP DESIGN + HARNESS FREEZE.**

Application code already exists in `main`, but it is treated as an **Architecture Spike / prototype evidence only** until the deep-design gate is approved. No feature expansion or code refactor is allowed during this phase unless a design document explicitly requires a tiny measurement spike.

## Why this phase exists

The 2026-08-17 live target caused implementation to start before the full design/harness package was complete. The repository now corrects that order: design contracts, failure policy, timing, security, adapter boundary, UX states, acceptance tests, and release gates are made explicit first.

## Completed

- Product goal and POC scope
- T1 Adapter 001 evidence capture
- Four UI concepts and selection of Concept 02
- First blindspot sweep / implementation-trap check
- High-level local-first architecture
- Initial CLAUDE.md workflow rules
- Meta-prompting guide
- Architecture Spike implementation proving scheduler/browser/adapter feasibility
- CI unit tests for the spike

## In progress in this branch

- Deep system design
- Component contracts
- State-machine contract
- Normal/failure sequence flows
- Error taxonomy and retry policy
- Timing design and measurement policy
- Security / local threat model
- Generic Adapter Contract v1
- Detailed responsive UI behavior
- Harness gates
- Acceptance matrix
- POC Go/No-Go gate

## Frozen during this phase

- `src/`
- `tests/`
- `scripts/`
- runtime dependencies
- new automation features
- generalized URL/AI recipe generation

Existing runtime code may be referenced as evidence, but design must not be bent merely to match prototype implementation.

## Known unresolved live facts

- Signature Edition `shippingType` is not independently verified.
- Live Windows scheduling variance is not yet measured.
- T1 authentication/session persistence has not yet been rehearsed on the user's Windows machine.
- Exact server-side semantics of checkout creation vs inventory reservation are unknown and must not be inferred.

## Exit condition

This phase exits only when `verification/POC_GO_NO_GO.md` has no unresolved design blockers and the user approves the design baseline. Only then may implementation be reconciled against the design.