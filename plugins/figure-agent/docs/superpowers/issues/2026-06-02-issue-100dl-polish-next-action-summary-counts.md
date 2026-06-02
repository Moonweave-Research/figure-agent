# Issue 100DL - Polish Next-Action Summary Counts

Status: implemented in this slice

Type: queue summary UX, SVG polish triage, operator evidence

## Problem

Issues 100CP-100DK made polish-mode row-level `svg_polish_next_action`
meaningful: rows can now distinguish `run_fig_compile`, `run_fig_critique`,
`rerun_fig_loop`, `resolve_release_boundary`, and
`start_svg_polish_recipe`.

`/fig_queue --mode polish` still aggregated SVG gate state, recommended path,
and blocker source, but did not aggregate `svg_polish_next_action`. A real
queue pass therefore showed the exact next action in each row, while the
summary still made operators manually scan rows to answer "what should be done
next across the corpus?"

## Scope

- Add `summary.by_svg_polish_next_action` when polish rows expose
  `svg_polish_next_action`.
- Keep row fields, filters, command-plan behavior, and driver policy unchanged.
- Update `/fig_queue` documentation and the Issue 100 inventory.

## Non-goals

- Do not add execution behavior.
- Do not change SVG polish gate semantics.
- Do not alter the `--svg-polish-next-action` filter.
- Do not mutate source, critique, export, accepted/golden, publication, or SVG
  polish state.

## Verification

- TDD red:
  - `uv run pytest -q tests/test_fig_queue.py::test_polish_queue_summary_counts_svg_gate_and_blockers`
  failed with missing `by_svg_polish_next_action`.
- Green:
  - The same test passed after adding the summary count.
- Live check:
  - `uv run python3 scripts/fig_queue.py --mode polish --format json` now
  reports the corpus-level SVG next-action distribution.

## Review Notes

1. **Operator value** - Queue summary now exposes the exact SVG next-action
   distribution without requiring row-by-row JSON post-processing.
2. **Compatibility** - The field is additive and appears only when rows expose
   SVG next-action values.
3. **Scope containment** - The change does not make any SVG polish, release, or
   workflow action executable.
