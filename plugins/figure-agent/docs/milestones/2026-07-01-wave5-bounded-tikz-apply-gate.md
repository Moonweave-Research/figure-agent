# Wave 5 Bounded TikZ Apply Gate

Date: 2026-07-01

## Outcome

Wave 5 did not mutate `fig3_trapping_concept.tex`.

The bounded TikZ implementation path is now split into three explicit states:

1. `bounded-tikz-refinement` can prepare a non-mutating request packet.
2. `bounded-tikz-candidate` can prepare a hash-bound candidate packet only when the request packet is ready.
3. `bounded-tikz-apply --apply` requires a separate human decision record with:
   - `decision_kind=apply_bounded_tikz_candidate`
   - `mutation_boundary=source_mutation_allowed`
   - `authorized_candidate_id`
   - `authorized_candidate_hash`

Without that record, apply fails closed.

## Live Fig3 State

Current `fig3_trapping_concept` cannot produce the old bounded TikZ candidate because that candidate is already reflected in source:

- candidate packet state: `blocked_candidate_already_reflected`
- next agent action: `refresh_benchmark_evidence_for_current_source`
- source mutation authorized: `false`

This is a durable rejection/refresh state, not a silent selector failure.

## Changed Contracts

- `human_decision_record` now recognizes `apply_bounded_tikz_candidate` as the only bounded TikZ source-mutation decision kind.
- `bounded_tikz_candidate_apply` validates the human decision record before any source write.
- `bounded_tikz_candidate_packet` distinguishes stale selectors from already-reflected candidates.
- `fig-agent bounded-tikz-apply` accepts `--authorization <json>` for source mutation approval.

## Validation

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_bounded_tikz_refinement_packet.py \
  tests/test_bounded_tikz_candidate_packet.py \
  tests/test_bounded_tikz_candidate_apply.py \
  tests/test_human_decision_record.py
# 48 passed

uv run ruff check scripts/bounded_tikz_refinement_packet.py \
  scripts/bounded_tikz_candidate_packet.py \
  scripts/bounded_tikz_candidate_apply.py \
  scripts/human_decision_record.py \
  tests/test_bounded_tikz_refinement_packet.py \
  tests/test_bounded_tikz_candidate_packet.py \
  tests/test_bounded_tikz_candidate_apply.py \
  tests/test_human_decision_record.py \
  bin/fig-agent
# All checks passed

uv run python -m compileall -q scripts tests bin/fig-agent
# passed
```

Live fail-closed check:

```bash
plugins/figure-agent/bin/fig-agent bounded-tikz-apply fig3_trapping_concept --apply --json
# status=blocked, applied=false, diagnostics[0].code=candidate_packet_not_ready
```
