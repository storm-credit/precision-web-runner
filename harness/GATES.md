# Mandatory Harness Gates

Every substantial task enters at Gate 0 and may move forward only when the current gate is satisfied.

## Gate 0 — Context

Required:
- current repository state read
- current phase identified
- target user and immediate goal stated
- known facts separated from assumptions
- relevant evidence linked

Fail if:
- the task is being answered from stale conversation memory while repository state may have changed
- critical evidence is missing but treated as fact

## Gate 1 — Interview / Intent

Answer:
- what outcome is the user actually trying to achieve?
- who is the primary user now?
- what is explicitly out of scope?
- which unresolved question would materially change the result?

Ask the user only for materially consequential missing context. Do not re-ask resolved questions.

## Gate 2 — Blindspot Sweep

Review at minimum:
- architecture
- authentication/session
- browser constraints
- timing/reliability
- security/privacy
- mobile/desktop boundary
- operational change/failure
- UX ambiguity
- testability

Output: unresolved blockers, accepted assumptions, mitigations.

## Gate 3 — Implementation Trap Check

Before code, explicitly reject shortcuts such as:
- hosted backend replaying foreign cookies
- browser-only timer as precision authority
- generated CSS hash as sole selector
- hardcoded dynamic identifiers
- unbounded retries
- ambiguous automatic replay
- automatic final payment authorization
- server restriction bypass

## Gate 4 — Design Completeness

Pass only if all are defined:
- component ownership and contracts
- state transitions
- normal sequence
- failure sequences
- retry/error policy
- timing policy
- security boundary
- adapter contract
- UX state/CTA behavior
- acceptance criteria

## Gate 5 — Design Review

Apply all review lenses from `harness/HARNESS_OVERVIEW.md`.

A review finding must be classified:
- BLOCKER — must resolve before implementation
- MAJOR — resolve or explicitly accept with rationale
- MINOR — may defer
- NOTE — informational

## Gate 6 — Implementation Ready

Requires:
- design approved by user
- no unresolved BLOCKER
- implementation plan maps each task to design contract + test
- existing spike code explicitly classified as keep/change/delete
- no speculative feature work

## Gate 7 — Implementation / TDD

For each task:
1. restate contract
2. define reproducible test/check
3. implement minimum change
4. run test
5. run regression
6. review changed files
7. update decision/deviation docs if needed

## Gate 8 — Verification

Do not accept a feature because code exists.
Require actual evidence:
- automated tests
- relevant manual/browser checks
- timestamps where timing matters
- expected failure behavior
- log redaction inspection

## Gate 9 — Live Go/No-Go

Use `verification/POC_GO_NO_GO.md`.
No live ARM if a mandatory item is unknown, assumed, or failed.

## Gate 10 — POC Exit

After POC success/failure:
- write result report
- record measured limitations
- classify STOP / REWORK / CONTINUE TO MVP
- do not automatically expand into generic platform work

## Global stop conditions

Stop and re-plan if:
- server restriction bypass becomes necessary
- secrets must be exported to an untrusted component
- automatic payment authorization becomes required
- the design contradicts observed target-site behavior
- a critical assumption cannot be tested
- the requested change exceeds the approved POC scope