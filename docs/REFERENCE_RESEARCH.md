# Reference Research — What We Actually Need

The user supplied five reference projects/patterns. The POC should **adopt useful process ideas without importing unnecessary runtime complexity**.

## 1. Karpathy Guidelines — USE NOW

Reference: `multica-ai/andrej-karpathy-skills`

Useful principles:
- think before coding
- state assumptions
- simplicity first
- surgical changes
- goal-driven execution with verifiable success criteria

Adoption:
- embedded directly into `CLAUDE.md`
- required before implementation

Do not:
- treat the reference repo as a runtime dependency

## 2. claude-video — PATTERN ONLY / DEFER RUNTIME USE

Reference: `bradautomates/claude-video`

Useful pattern:
- a capability can be packaged as a self-contained skill/tool with its own scripts and setup checks
- capability detection and preflight should be explicit

Possible future use:
- Recipe/Adapter packaging conventions
- self-contained adapter diagnostics

POC decision:
- no dependency/install required
- not part of the runtime problem we are proving

## 3. Superpowers — USE THE WORKFLOW NOW

Reference: `obra/superpowers`

Useful workflow:
- brainstorming before coding
- design approval
- detailed implementation plan
- TDD / systematic debugging
- spec review and code review
- verification before completion

Adoption:
- implemented as project gates in `CLAUDE.md`
- implementation does not begin until design approval

POC decision:
- workflow ideas are required
- installing the complete framework is optional and deferred until implementation tooling is chosen

## 4. Understand-Anything — DEFER

Original user reference: `Lum1104/Understand-Anything`; the project currently resolves to `Egonex-AI/Understand-Anything`.

Useful later:
- codebase knowledge mapping
- explaining relationships when the project becomes large

POC decision:
- unnecessary before there is a meaningful codebase
- no runtime dependency
- revisit after POC/MVP code volume grows

## 5. agentmemory — DEFER; USE LIGHTWEIGHT DOC MEMORY NOW

Reference: `rohitg00/agentmemory`

Useful later:
- persistent context across long-running agent sessions
- remembering decisions and prior discoveries

POC decision:
- do not introduce a memory server yet
- use repository-native memory first:
  - `CLAUDE.md`
  - `docs/DECISIONS_AND_INTERVIEW.md`
  - `docs/DEVIATIONS.md`
  - run/test reports once implementation starts

Revisit only if repeated sessions genuinely lose important context.

## “본보기 코드” rule

The user's note says the “find similar GitHub/open-source examples” rule was primarily intended for novel/reference work rather than as a mandatory software-project requirement.

For this POC:
- do not copy a random automation project just to satisfy the rule
- use targeted reference code only when a concrete implementation question appears (e.g. Playwright browser attachment, clock scheduling, extension bridge)
- prefer official/primary documentation for implementation contracts

## Final adoption summary

### Required now
- Karpathy behavioral rules
- Superpowers-style design/plan/test/review/verify gates
- blindspot sweep
- implementation trap check
- four UI concepts + explicit selection
- interview/assumption record
- deviation log
- meta-prompting process

### Deferred until needed
- claude-video runtime/skill installation
- Understand-Anything code graph
- agentmemory server
- generalized AI recipe generation
- multi-agent orchestration

The POC should remain small enough that each new dependency must justify itself against the POC success criteria.
