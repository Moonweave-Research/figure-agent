# Issue 45 - SVG Polish Route UX

**Status:** implemented
**Spec:** `../specs/2026-05-26-issue45-svg-polish-route-ux-design.md`
**Plan:** `../plans/2026-05-26-issue45-svg-polish-route-ux.md`
**Builds on:** Issue 44 SVG polish recipe executor and aesthetic delta gate

## Problem

Issue 44 shipped the bounded SVG polish recipe layer:

1. `polish/svg_polish_recipe.yaml`
2. `scripts/svg_polish_executor.py` dry-run/write
3. `scripts/svg_polish_delta.py` before/after/diff pack
4. `scripts/svg_polish_handoff.py` audit/manifest
5. `/fig_critique` delta review

But `/fig_driver --mode polish` still mostly says "run handoff" once the
generated export is current. That is now too coarse. Operators need one
state-derived next command that starts from the new recipe workflow instead of
jumping directly to handoff.

## Goal

Teach polish mode to surface the first safe next command in the SVG polish
recipe workflow without executing or mutating anything.

## In Scope

- Add command helpers for:
  - recipe executor dry-run
  - recipe executor write
  - delta pack generation
- Improve `/fig_driver --mode polish` reasons and `safe_command`.
- Keep action vocabulary backward compatible; continue using
  `polish_handoff_stop`.
- Update command docs for the canonical polish sequence.
- Add focused tests for missing recipe, recipe present, polished SVG present,
  and delta manifest present states.

## Out of Scope

- Creating or editing recipes automatically.
- Running recipe executor or delta generation from the driver.
- Changing accepted/golden/release behavior.
- Changing final-artifact schema.
- Requiring polished SVG for fixtures that have not opted into polished-SVG
  final artifact state.

## Acceptance Criteria

- If polish mode reaches SVG polish and no recipe exists, the driver tells the
  operator to create `polish/svg_polish_recipe.yaml`.
- If a recipe exists and `polish/<name>.polished.svg` is missing, the driver
  returns the recipe dry-run command as the first safe command.
- If a polished SVG exists and the delta manifest is missing, the driver returns
  the delta-pack generation command as the first safe command.
- If recipe, polished SVG, and delta manifest exist, the driver routes to
  `svg_polish_handoff.py`.
- Semantic backport and human gates still take precedence over all polish UX
  hints.
- Existing public `figure-agent.driver.v1` fields remain compatible.

## Implementation Notes

Implemented on branch `codex/issue45-svg-polish-route-ux`.

The driver still returns `action: polish_handoff_stop`; it now refines
`safe_command` and `reason` based on fixture-local polish files:

- missing recipe -> no command; author `polish/svg_polish_recipe.yaml`;
- recipe present, polished SVG missing -> executor `--dry-run`;
- polished SVG present, delta manifest missing/stale/invalid -> delta-pack
  generation command;
- valid delta manifest present -> handoff guidance.

Human gates, semantic backport, and final-artifact `BLOCKED` still take
precedence.
