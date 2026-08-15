# Next Action

## Single next objective

Complete and review the **Deep Design + Harness baseline** before modifying runtime code.

## Required order

1. Read `status/CURRENT_STATUS.md`.
2. Read `CLAUDE.md` and `docs/POC_SCOPE.md`.
3. Review all files under `design/` created for Deep Design.
4. Run the harness gates in `harness/GATES.md`.
5. Resolve contradictions or mark them as explicit assumptions.
6. Review `verification/ACCEPTANCE_MATRIX.md` and `verification/POC_GO_NO_GO.md`.
7. Update `docs/DEVIATIONS.md` for any material plan change.
8. Ask the user only for decisions that materially change architecture or live behavior.
9. Obtain design approval.
10. Only then create an implementation-reconciliation plan.

## Do not do next

- Do not add features.
- Do not refactor the prototype to match assumptions before design review.
- Do not add a second site.
- Do not add cloud/mobile-only execution.
- Do not automate final payment authorization.

## Completion signal

The next action is complete when the repository can answer, without hidden assumptions:

- who owns scheduling accuracy,
- where authentication lives,
- what each component may call,
- every state transition,
- what is retryable and what is not,
- how duplicate execution is prevented,
- what data is logged/redacted,
- what a site adapter must implement,
- what the user sees in each state,
- and exactly what must pass before live use.