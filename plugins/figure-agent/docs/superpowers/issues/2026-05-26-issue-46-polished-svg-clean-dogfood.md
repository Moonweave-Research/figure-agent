# Issue 46 - Polished-SVG Clean Dogfood

**Status:** implemented
**Spec:** `../specs/2026-05-26-issue46-polished-svg-clean-dogfood-design.md`
**Plan:** `../plans/2026-05-26-issue46-polished-svg-clean-dogfood.md`
**Builds on:** Issue 44 recipe executor and Issue 45 polish route UX

## Problem

Issue 44 proved that the SVG polish recipe, executor, delta pack, and handoff
can run on a real exported SVG, but the dogfood fixture was not a clean
polish-ready route. Issue 45 made `/fig_driver --mode polish` report clearer
next commands, but current tests still cover the steps mostly as isolated
branches.

The missing proof is a clean, deterministic end-to-end plugin path:

1. generated export is current;
2. recipe is fresh;
3. executor writes only `polish/<name>.polished.svg`;
4. delta pack is generated;
5. handoff writes audit and final-artifact manifest;
6. `/fig_status` reports `final_artifact_state: FRESH`;
7. `/fig_driver --mode polish` closes with `action: complete`.

## Goal

Add a CI-friendly clean dogfood test and milestone evidence proving the full
polished-SVG plugin path without editing real figure source or committing
generated artifacts.

## In Scope

- Add a deterministic temporary fixture test for the full SVG polish path.
- Use existing modules rather than duplicating behavior:
  - `svg_polish_recipe.py`
  - `svg_polish_executor.py`
  - `svg_polish_delta.py`
  - `svg_polish_handoff.py`
  - `status.py`
  - `fig_driver.py`
- Record dogfood evidence and review notes.

## Out of Scope

- Editing real examples.
- Changing TikZ source, accepted state, golden artifacts, or generated exports.
- Adding new SVG polish operation classes.
- Adding hidden auto-polish execution to `/fig_driver`.
- Changing final-artifact schema.

## Acceptance Criteria

- A focused pytest constructs a temporary clean fixture and runs recipe,
  executor, delta, handoff, status, and driver in sequence.
- The test proves source SVG/export files remain unchanged by the executor.
- The test proves `compute_final_artifact_state` via `/fig_status` sees the
  generated manifest as fresh.
- The test proves `/fig_driver --mode polish` returns `action: complete` only
  after the polished final artifact is fresh.
- Documentation records that this is plugin-path dogfood, not a real-figure
  aesthetic-quality claim.

## Implementation Notes

Implemented on branch `codex/issue46-polished-svg-clean-dogfood`.

The shipped guard is `tests/test_svg_polish_clean_dogfood.py`, which constructs
a temporary clean fixture and runs the existing modules in order:

```text
svg_polish_recipe -> svg_polish_executor -> svg_polish_delta ->
svg_polish_handoff -> status.infer_stage -> fig_driver.build_driver_summary
```

No production API was changed. The only test-local adaptation is a base-dir
shim for temporary fixtures outside the repository root, matching the existing
repo-relative hash contract used by real examples.
