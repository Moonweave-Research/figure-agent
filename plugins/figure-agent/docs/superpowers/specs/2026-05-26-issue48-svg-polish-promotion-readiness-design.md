# Issue 48 SVG Polish Promotion Readiness Design

## Context

Issues 43-47 created the aesthetic lever grammar and the bounded SVG polish
route. The route is deliberately conservative: a real fixture can request
`ready_for_svg_polish` in its aesthetic intent, but the refreshed critique and
loop checkpoint may still route `continue_tikz`.

That behavior is correct. The gap is explanation. `/fig_driver --mode polish`
currently returns a safe action and a reason string, but downstream agents and
humans have no stable field that answers whether SVG polish can start, which
contract blocked it, and what class of action should happen next.

## Design

Introduce a read-only `svg_polish_readiness` object:

```yaml
schema: figure-agent.svg-polish-readiness.v1
source: latest_loop_checkpoint
can_start_svg_polish: false
recommended_path: continue_tikz
next_action: run_fig_loop
blocking_reason: "editorial polish trigger recommends continue_tikz"
blocking_items:
  - source: editorial_art_direction_summary
    id: tikz_vs_svg_polish_trigger
    recommended_path: continue_tikz
    verdict: weak
```

The readiness object is derived from existing loop summaries. It does not read
or mutate files directly, does not add a new schema version to critique output,
and does not change driver action vocabulary.

## Route Semantics

`ready_for_svg_polish` is the only path that sets `can_start_svg_polish: true`.
Even then, the driver still applies existing precedence rules before starting
recipe/delta/handoff guidance:

- crop uncertainty blocks polish;
- aesthetic lever human gate blocks polish;
- top-tier blockers block polish;
- editorial human gate blocks polish;
- semantic backport blocks polish;
- missing/stale render, critique, or export blocks polish earlier in the driver.

`continue_tikz` means the figure needs source-level visual improvement before
SVG polish can count. The next action is to leave polish mode and run the normal
loop against the current goal.

`semantic_backport_required` means the polished artifact or critique changed
scientific or story meaning. The next action is to backport the semantic change
to TikZ, briefing, or spec, then rerun compile/export/critique/loop.

`needs_human_art_direction` means the figure has an art-direction ambiguity
that should not be delegated to an executor. The next action is human review.

## Implementation

Add focused helper functions to `scripts/fig_driver_editorial.py` because this
is where the existing editorial route policy lives:

- `svg_polish_readiness(summary: Any) -> dict[str, Any] | None`
- `svg_polish_readiness_from_checkpoint(checkpoint: dict[str, Any]) -> dict[str, Any] | None`

`fig_loop.py` writes the readiness object into `iteration_001.json` after
building `editorial_art_direction_summary`.

`fig_driver.py` attaches readiness to top-level JSON when a loop checkpoint is
available. If the checkpoint predates Issue 48 and lacks the field, the driver
computes it from `editorial_art_direction_summary`. Driver action selection
continues to call the existing `editorial_polish_route()` function.

## Compatibility

This is an additive contract:

- no existing field is removed;
- `figure-agent.driver.v1` remains compatible because consumers must ignore
  unknown top-level fields;
- older loop checkpoints without `svg_polish_readiness` remain valid;
- critique schema/rubric versions do not change.

## Tests

Focused tests cover:

- helper output for all four recommended paths;
- malformed or missing summaries returning `None`;
- `/fig_loop` writing readiness when editorial summary exists;
- `/fig_driver --mode polish` surfacing readiness for current checkpoints;
- driver fallback computation for legacy checkpoints;
- `continue_tikz`, `semantic_backport_required`, and
  `needs_human_art_direction` keeping `can_start_svg_polish: false`;
- `ready_for_svg_polish` preserving existing recipe/delta/handoff routing.

## Non-Goals

- No automatic SVG editing.
- No automatic TikZ patching.
- No accepted/golden/publication mutation.
- No numeric quality gate changes.
- No guarantee of Nature or Science acceptance.

## Self-Review

- Placeholder scan: none.
- Scope check: one additive readiness contract, no schema/rubric bump.
- Compatibility check: all public driver fields remain; new field is additive.
- Safety check: readiness can only explain routing; it cannot execute anything.
