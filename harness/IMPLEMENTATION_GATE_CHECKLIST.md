# Implementation Gate Checklist

Use immediately before each runtime coding slice.

## Gate A — Scope
- [ ] active slice is exactly one of R1-R10
- [ ] Gap IDs are named
- [ ] design authority files are named
- [ ] files allowed to change are named
- [ ] no speculative feature is included

## Gate B — Safety
- [ ] no membership/sale-time/queue/CAPTCHA/rate-limit bypass
- [ ] no cookie/token export
- [ ] no final payment authorization automation
- [ ] irreversible replay rule remains intact
- [ ] ambiguous side effects have fail-closed behavior

## Gate C — Tests first
- [ ] expected behavior stated
- [ ] failure behavior stated
- [ ] regression checks stated
- [ ] live target request is not required for unit implementation validation

## Gate D — Change control
- [ ] implementation is surgical
- [ ] no unrelated refactor
- [ ] if plan must change, `docs/DEVIATIONS.md` is updated first
- [ ] new dependency requires explicit demonstrated need

## Gate E — Completion
- [ ] Gap IDs actually closed
- [ ] tests/checks passed
- [ ] changed files reviewed against design
- [ ] secrets/PII not logged
- [ ] status updated
- [ ] next R-slice is not started implicitly

A failed checkbox stops the slice or triggers replanning.