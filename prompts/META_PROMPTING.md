# Meta Prompting Guide

Use this when asking an AI agent to perform substantial work on Precision Web Runner.

## 1. Context Dump

Provide enough raw context before asking for execution.

Include:
- current goal
- current phase (design / implementation / verification)
- primary user
- approved scope
- known facts/evidence
- unresolved assumptions
- relevant files/logs
- constraints
- explicit non-goals
- safety boundaries

Do not ask the model to infer missing critical context silently.

## 2. Prompt Distillation

Turn the context dump into the smallest executable prompt that preserves the important constraints.

### Goal Prompt

Must contain:
- goal
- success conditions
- stop conditions

Example:

```text
Goal:
Prove that the local runner can schedule and execute the T1 adapter flow to the manual-payment checkpoint.

Success:
- target/dispatch/response timestamps recorded
- dynamic checkoutNumber extracted
- checkout route opened
- exact failed step shown on error
- no raw cookie persisted
- duplicate run prevented

Stop:
- server restriction bypass becomes necessary
- session handling requires exporting secrets
- final payment must be auto-authorized
- architecture spike fails reproducibility
```

### Implementation Prompt

Must contain:
- approved design link/files
- exact files/components in scope
- constraints
- prohibited refactors
- tests/checks to run
- completion verification

Example constraint style:

```text
Constraints:
- no arbitrary eval in recipes
- no unbounded retry
- no cloud cookie storage
- do not build future SaaS features
- T1-specific logic stays in adapter layer
```

### UI Prompt

Must contain:
- viewport targets
- information hierarchy
- selected design system
- required states
- real CTA behavior
- responsive behavior

For this project:
- Concept 02 light dashboard
- mobile first viewport: target + target time + state + primary CTA
- every visible button/form must map to real behavior before POC completion

### Research Prompt

Must contain:
- source priority
- research scope
- freshness requirements
- verification method
- how to label facts vs inference

Recommended:
- primary/official documentation first for browser/library contracts
- repository source code for implementation patterns
- record exact source and commit/tag when a behavior matters to implementation
- do not treat old examples as current API truth

## 3. Result Verification

Before accepting AI output, check:
- did it satisfy every success condition?
- did it exceed POC scope?
- did it invent assumptions?
- did it violate safety/site boundaries?
- are tests/checks actually run, not merely described?
- are failures reported clearly?
- did the plan change?
- if changed, was `docs/DEVIATIONS.md` updated?
- are decision docs current?

## Question-induction rule

When creating a new major prompt from conversation history, instruct the AI:

> Based on the current conversation and repository state, identify only the missing context that would materially change the implementation. Ask for that context before making an irreversible design choice. Do not re-ask questions already answered by the repository or conversation.

## Prompt compression rule

A good final prompt should remove:
- repeated conversation history
- irrelevant brainstorming
- already-rejected options
- speculative future features

It should preserve:
- accepted decisions
- evidence
- constraints
- success criteria
- stop conditions
- verification commands/checks

## Completion rule

Never accept “implemented” as a result by itself.

Completion requires evidence such as:
- test output
- reproduced browser behavior
- timestamps
- changed-file review
- explicit remaining risks
