# Issue 48 - SVG Polish Promotion Readiness

**Status:** implemented on branch `codex/issue48-svg-polish-promotion-gate`
**Builds on:** Issue 43 aesthetic lever grammar, Issue 44 recipe executor,
Issue 45 polish route UX, Issue 46 clean SVG-polish dogfood, Issue 47 real
fixture negative dogfood
**Spec:** `../specs/2026-05-26-issue48-svg-polish-promotion-readiness-design.md`
**Plan:** `../plans/2026-05-26-issue48-svg-polish-promotion-readiness.md`

## Problem

The SVG polish route now exists, but the real fixture dogfood in Issue 47 showed
that a figure can stop at `continue_tikz` without a compact, structured answer
to the operator's real question:

```text
Why is this not ready for SVG polish, and what must be resolved first?
```

The current driver reason is safe but too coarse. It says the latest loop
checkpoint recommends `continue_tikz`; it does not expose a stable readiness
object with the blocker source, recommended path, next action class, and
promotion eligibility.

## Goal

Add a read-only SVG polish readiness contract that is computed from the latest
loop checkpoint and shared by `/fig_loop` and `/fig_driver --mode polish`.

The contract must make the SVG-polish boundary explainable without allowing the
driver to edit source, generated exports, polished SVGs, accepted state, golden
state, or publication provenance.

## Scope

In scope:

- Add a compact `svg_polish_readiness` object to `/fig_loop` iteration output.
- Make `/fig_driver --mode polish` surface the same object when a loop
  checkpoint exists.
- Explain the four main paths:
  - `continue_tikz`
  - `ready_for_svg_polish`
  - `semantic_backport_required`
  - `needs_human_art_direction`
- Preserve existing driver action vocabulary and `figure-agent.driver.v1` shape.
- Add tests for readiness extraction, driver surfacing, blocker precedence, and
  backward compatibility with older loop checkpoints.

Out of scope:

- Hidden auto-polish.
- New SVG operation classes.
- Source drawing changes.
- Accepted/golden/export mutation.
- Release policy changes.
- Any claim that SVG polish is a journal-acceptance guarantee.

## Acceptance Criteria

- `/fig_loop` records `svg_polish_readiness` with:
  - `schema: figure-agent.svg-polish-readiness.v1`
  - `can_start_svg_polish: true|false`
  - `recommended_path`
  - `next_action`
  - `blocking_reason`
  - `blocking_items`
- `/fig_driver --mode polish` includes `svg_polish_readiness` at top level when
  a current loop checkpoint is available.
- `continue_tikz` produces `can_start_svg_polish: false`, `next_action:
  run_fig_loop`, and a blocker naming the editorial polish trigger.
- `ready_for_svg_polish` produces `can_start_svg_polish: true` only when no
  human, top-tier, crop, aesthetic, or semantic-backport blocker has precedence.
- `semantic_backport_required` produces `can_start_svg_polish: false` and
  `next_action: semantic_backport`.
- `needs_human_art_direction` produces `can_start_svg_polish: false` and
  `next_action: human_art_direction_review`.
- Legacy loop checkpoints without `svg_polish_readiness` remain usable; the
  driver computes the readiness summary from existing checkpoint summaries.
- Existing tests for driver action, stop boundary, safe command, and forbidden
  actions continue to pass.

## Review Questions

1. Does this make SVG polish readiness explainable without introducing another
   mutation path?
2. Does it preserve the existing `editorial_polish_route()` policy instead of
   duplicating incompatible route rules?
3. Does it keep `ready_for_svg_polish` subordinate to human, top-tier, crop,
   aesthetic, semantic-backport, freshness, export, accepted, golden, and
   publication gates?
4. Does it help real operators decide whether to keep patching TikZ or move to
   a bounded SVG polish recipe?

## Implementation Notes

Implemented as an additive readiness contract:

- `scripts/fig_driver_editorial.py` owns the route-to-readiness policy.
- `/fig_loop` writes `svg_polish_readiness` into `iteration_001.json` when an
  editorial summary exists.
- `/fig_driver --mode polish` exposes the same readiness object at top level
  for current loop checkpoints.
- Legacy loop checkpoints without `svg_polish_readiness` remain usable because
  the driver computes readiness from `editorial_art_direction_summary`.
- Crop uncertainty, aesthetic human gates, and top-tier blockers override a
  nominal `ready_for_svg_polish` trigger so readiness cannot silently bypass
  review blockers.

Verification during implementation:

```bash
uv run pytest -q tests/test_fig_driver_editorial.py tests/test_fig_driver.py tests/test_fig_loop.py tests/test_fig_loop_assessments.py
uv run pytest -q tests/test_release_contract.py tests/test_ci_workflows.py tests/test_fig_driver_editorial.py tests/test_fig_driver.py tests/test_fig_loop.py tests/test_fig_loop_assessments.py
uv run pytest -q
```
