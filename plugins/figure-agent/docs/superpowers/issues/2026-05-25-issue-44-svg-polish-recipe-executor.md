# Issue 44 - SVG Polish Recipe Executor and Aesthetic Delta Gate

**Status:** implemented; final verification pending
**Spec:** `../specs/2026-05-25-issue44-svg-polish-recipe-executor-design.md`
**Plan:** `../plans/2026-05-25-issue44-svg-polish-recipe-executor.md`
**Builds on:** Issue 42 SVG polish handoff, Issue 43 aesthetic lever grammar

## Problem

Issue 42 made SVG polish handoff auditable, and Issue 43 made aesthetic intent
explicit enough for critique and loop routing. The remaining gap is execution:
when `/fig_loop` or `/fig_drive --mode polish` says `ready_for_svg_polish`, the
operator still has to decide and perform visual-only SVG edits by hand.

This keeps the plugin from reliably converting a semantically correct generated
figure into a final, hand-finished journal artifact. It also creates a risky
middle ground: an outer agent can edit SVG manually, but the edits are not
expressed as small, reviewable, repeatable polish operations.

## Goal

Add a conservative SVG polish recipe layer that can apply bounded visual-only
edits to `polish/<name>.polished.svg`, record what changed, and force a
before/after aesthetic and semantic review before the polished SVG can be
treated as final.

The goal is not autonomous art direction. The goal is to make the last optical
polish layer safer, more repeatable, and easier to audit.

## Slices

### Issue 44A - Recipe Contract

Define `examples/<name>/polish/svg_polish_recipe.yaml` with a small closed set
of visual-only operations:

- `label_micro_position`
- `leader_line_micro_position`
- `stroke_polish`
- `spacing_balance`
- `color_opacity_polish`
- `typography_cleanup`
- `icon_detail`
- `export_cleanup`

The recipe must be fixture-scoped, deterministic, hashable, and unable to
claim semantic edits as polish.

### Issue 44B - Safe Executor MVP

Implement a dry-run-first executor that reads the recipe and writes
`polish/<name>.polished.svg`. The first executor should support only low-risk
operations, with an explicit dry-run diff summary before write mode.

It must never mutate `exports/`, `build/`, source TeX, critique files,
accepted state, or golden contracts.

### Issue 44C - Aesthetic Delta Audit

Generate before/after review inputs after polish:

- generated export render
- polished SVG render
- visual diff or compact changed-region summary
- recipe summary

Extend the critique/loop surface so the host LLM must answer whether the polish
improved journal finish, introduced regressions, or changed scientific meaning.

### Issue 44D - Semantic Backport Guard

If polish changes scientific semantics, the manifest must set
`semantic_change_declared: true` or `backport_required: true`, and existing
final-artifact state must remain `BLOCKED` until the semantic change is
backported to TikZ, briefing, or spec.

### Issue 44E - Real Fixture Dogfood

Run the recipe layer on one real fixture that already reaches
`ready_for_svg_polish`. Record whether the recipe layer improved the final
artifact and whether the semantic guard caught any unsafe edit.

## In Scope

- Recipe parser and validator.
- A conservative executor for a small subset of SVG visual-only edits.
- Dry-run and write modes.
- Integration with the existing SVG polish audit/manifest path.
- Before/after artifact generation for host critique.
- Lint/status/loop surfacing for recipe presence, staleness, and unsafe edits.
- Tests and one real-fixture dogfood milestone.

## Out of Scope

- Automatic art-direction decisions.
- Free-form SVG editing.
- Inkscape, Affinity, or browser automation in the first slice.
- External web/reference scraping.
- Source-level TikZ patching under the label of SVG polish.
- Accepted/golden mutation.
- Release shortcuts or score gates.
- Paper-wide style propagation.

## Acceptance Criteria

- The recipe schema rejects malformed, broad, semantic, or fixture-external
  edits.
- Dry-run reports exact planned changes without writing files.
- Write mode produces only `polish/<name>.polished.svg` and allowed polish
  metadata.
- The generated polish manifest remains compatible with
  `svg_polish_manifest.py`.
- Before/after audit inputs are deterministic and included in the critique or
  closeout path.
- Any declared or detected semantic change blocks final-artifact readiness
  through the existing `BLOCKED` state.
- A real fixture dogfood run proves that the workflow can improve or reject
  polish without mutating source, exports, accepted state, or golden contracts.

## Priority

This is the next plugin-product priority after Issue 43 because the audit
kernel can now identify aesthetic bottlenecks and route to SVG polish. The next
step is to make the SVG polish execution itself bounded and reviewable.

## Implementation Notes

Implemented as five narrow slices:

- 44A: `svg_polish_recipe.py` parser/validator/writer/freshness contract.
- 44B: dry-run-first `svg_polish_executor.py` with bounded XML-attribute edits.
- 44C: SVG polish aesthetic delta pack and critique-brief surfacing.
- 44D: semantic-change/backport BLOCKED guard regression coverage.
- 44E: real-fixture dogfood on `fig1_overview_v2_pair_001_vault`.

The 44E fixture did not start from a clean polish-ready release route on this
branch; see `../../milestones/2026-05-25-svg-polish-recipe-dogfood.md` for the
route precondition caveat and the two CLI defects found during dogfood.
