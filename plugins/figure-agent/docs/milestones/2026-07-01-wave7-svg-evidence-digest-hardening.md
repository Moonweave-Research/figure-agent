# Wave 7 SVG Evidence Digest Hardening

Date: 2026-07-01

## Outcome

The human decision digest now treats `ready_for_svg_polish_positive_evidence_missing` as part of the SVG-polish evidence-missing family.

This keeps the Wave 6 positive-evidence gate visible to operators and future agents instead of leaving the row ungrouped.

## Boundary

The grouping is intentionally narrow. It applies only when a row has SVG polish gate/readiness signals:

- `svg_polish_gate_state`
- `svg_polish_recommended_path`
- `can_start_svg_polish`

This prevents ordinary release/acceptance rows in polish mode from being misclassified as SVG evidence blockers merely because the queue emits an evidence packet for every polish-mode row.

## Validation

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_queue.py
# 67 passed

uv run ruff check scripts/fig_queue.py tests/test_fig_queue.py
# All checks passed
```
