# Wave 6 SVG Polish Positive Evidence Gate

Date: 2026-07-01

## Outcome

SVG polish readiness now requires positive readiness evidence.

`ready_for_svg_polish` and `can_start_svg_polish=true` are no longer sufficient by themselves. A readiness summary must carry non-empty `positive_evidence` before the driver/queue can treat SVG polish as ready.

## Contract

Ready SVG polish requires:

- `recommended_path=ready_for_svg_polish`
- `can_start_svg_polish=true`
- non-empty `positive_evidence`
- no top-tier blockers
- no crop uncertainty
- no human art-direction gate
- no source-level semantic backport requirement

If `ready_for_svg_polish` is present without positive evidence, the system returns:

- `can_start_svg_polish=false`
- `next_action=collect_svg_polish_evidence`
- blocker id `positive_svg_polish_evidence_missing`
- queue evidence state `not_qualified`

## Live Fig3 State

Current `fig3_trapping_concept` remains blocked from SVG polish:

- `svg_polish_gate_state=blocked`
- `can_start_svg_polish=false`
- `svg_polish_evidence_state=not_qualified`
- `polish_blocker_reason=continue_tikz_recommended`
- `svg_polish_recommended_path=continue_tikz`

No generated polished SVG, source, export, accepted, golden, final-artifact, or release state was mutated.

## Validation

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_driver_editorial.py tests/test_fig_queue.py
# 87 passed

uv run ruff check scripts/driver/fig_driver_editorial.py scripts/fig_queue.py \
  tests/test_fig_driver_editorial.py tests/test_fig_queue.py
# All checks passed

uv run python -m compileall -q scripts tests bin/fig-agent
# passed
```

Live smoke:

```bash
plugins/figure-agent/bin/fig-agent queue --mode polish fig3_trapping_concept --json
# row: blocked, can_start_svg_polish=false, svg_polish_evidence_state=not_qualified
```
