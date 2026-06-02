# Issue 100DK - Polish Release-Boundary Gate Alignment

Status: implemented in this slice

Type: SVG polish UX, release-boundary consistency, driver contract

## Problem

Issue 100CP made polish-mode `svg_polish_gate.next_action` mirror compile and
export prerequisites instead of falling through to the generic
`no_current_checkpoint` loop advice.

A real polish-queue pass found a remaining edge case: when export artifacts are
missing or stale but the fixture is already outside the safe draft-export
predicate, `/fig_drive --mode polish` correctly stops at
`accepted_or_final_ready_required` with `required_actor: release_operator`.
However, the additive `svg_polish_gate` still fell back to
`state: no_current_checkpoint` and `next_action: rerun_fig_loop`.

This made a single queue row contradictory: the top-level driver and
`operator_guidance` said to resolve release/accepted/final/publication gates,
while SVG-specific columns suggested rerunning `/fig_loop`.

## Scope

- Treat `accepted_or_final_ready_required` as a polish-mode driver prerequisite
  for the additive SVG polish gate.
- Emit `svg_polish_gate.next_action: resolve_release_boundary` for that case.
- Keep compile, critique, adjudication, export, ready-for-SVG, human-gate, and
  semantic-backport behavior unchanged.
- Update `/fig_drive` documentation with the release-boundary mirror case.

## Non-goals

- Do not make release or force-golden actions executable.
- Do not mutate exports, accepted/golden state, final artifacts, SVG polish
  files, or publication state.
- Do not change the top-level `/fig_drive` action vocabulary.
- Do not weaken the draft-export safety predicate.

## Verification

- TDD red:
  - `uv run pytest -q tests/test_fig_driver.py::test_polish_mode_does_not_surface_not_accepted_export_as_executable`
  failed because `svg_polish_gate.state` was `no_current_checkpoint` instead
  of `blocked`.
- Green:
  - The same test passed after release-boundary gate alignment.
- Live check:
  - `uv run python3 scripts/fig_queue.py --mode polish --format json fig5_floating_clip_mechanism`
  now reports `required_actor: release_operator`,
  `svg_polish_gate_state: blocked`, and
  `svg_polish_next_action: resolve_release_boundary`.

## Review Notes

1. **Authority alignment** - SVG-specific columns now match the authoritative
   driver/operator boundary when release state blocks polish.
2. **Scope containment** - The change is additive to gate explanation only; no
   release, export, accepted, golden, or SVG mutation path is opened.
3. **Integration readiness** - Queue and queue-run filters can now distinguish
   release-boundary blockers from true no-current-checkpoint blockers.
