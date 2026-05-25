# Issue 45 SVG Polish Route UX Design

## Summary

Issue 45 makes `/fig_driver --mode polish` a clearer traffic controller for the
Issue 44 recipe workflow. The driver remains dry-run only and does not execute
SVG polish commands. It simply reports the first safe command the operator can
run next.

## Current Behavior

Once render/critique/export gates are closed and `/fig_loop` says
`ready_for_svg_polish`, polish mode returns:

- `action: polish_handoff_stop`
- `safe_command: null`
- reason text that mentions `svg_polish_handoff.py`

That skips over the new recipe executor and delta pack steps.

## Target Behavior

When polish mode reaches the visual-only SVG handoff branch, choose the next UX
hint from fixture-local polish files:

1. `polish/svg_polish_recipe.yaml` missing:
   - keep `action: polish_handoff_stop`;
   - keep `safe_command: null`;
   - reason says to author the bounded recipe first.
2. recipe exists and `polish/<name>.polished.svg` missing:
   - keep `action: polish_handoff_stop`;
   - set `safe_command` to
     `uv run python3 scripts/svg_polish_executor.py examples/<name> --dry-run`;
   - reason says dry-run first, then `--write` only after reviewing the plan.
3. polished SVG exists and `polish/aesthetic_delta/delta_manifest.json`
   missing:
   - keep `action: polish_handoff_stop`;
   - set `safe_command` to a local `python -c` command that calls
     `build_svg_polish_delta_pack(...)`;
   - reason says delta evidence is required before critique/handoff review.
4. recipe, polished SVG, and delta manifest all exist:
   - keep `action: polish_handoff_stop`;
   - set `safe_command` to `null`;
   - reason says run `svg_polish_handoff.py` after reviewing the delta pack.

## Precedence

Existing gates remain stronger:

- stale/missing render, critique, and export states still route before polish;
- `/fig_loop` human gates still stop first;
- top-tier or crop-audit blockers still stop first;
- `semantic_backport_required` still stops first;
- final artifact `BLOCKED` still stops first;
- final artifact `FRESH` still completes.

## Compatibility

No new driver action is introduced. Consumers that already understand
`polish_handoff_stop` continue to work. The only additive behavior is a more
specific `safe_command` and clearer reason text.

## Testing

Focused `test_fig_driver.py` coverage should prove:

- missing recipe uses a no-command author-recipe stop;
- existing recipe returns executor dry-run safe command;
- existing polished SVG returns delta-pack safe command;
- existing delta manifest returns handoff guidance;
- semantic backport still wins over recipe guidance.
