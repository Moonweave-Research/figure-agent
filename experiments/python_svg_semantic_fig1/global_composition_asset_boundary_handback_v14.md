# v14 Global Composition And Asset Boundary Handback

## Scope

`v14_global_composition_and_asset_boundary` is a global grammar pass over the v13 renderer. It keeps the semantic scene payload model intact and does not introduce a new backend, TikZ conversion, or reference-image tracing step.

## RED Checks Added First

The v14 verifier adds whole-figure checks that are broader than the panel-specific v12 and v13 checks:

- Support panel titles must carry the shared `panel-title-support` role.
- The hero title must carry the `panel-title-hero` role.
- Support-to-hero arrows must carry `global-flow-arrow` and remain visually quiet.
- Support panel conclusion text must carry the shared `panel-conclusion` role.
- README must register this handback.
- This handback must explicitly document `Reusable asset candidates`, `Fig1-only boundaries`, and `Human visual review`.

Initial RED output:

```text
v14 global composition checks failed:
- support panel titles are not role-tagged consistently: 0 < 4
- hero panel title role count mismatch: 0 != 1
- support-to-hero arrows are not globally role-tagged: 0 < 4
- support panel conclusion cues are not normalized: 0 < 4
- README missing v14 global composition asset-boundary handback
- missing v14 asset-boundary handback
```

## Rendering Changes

- Added `data-panel-role` tags to hero and support panel titles.
- Added `data-panel-role="global-flow-arrow"` and `data-flow-role` attributes to support-to-hero arrows.
- Reduced support-to-hero arrow stroke from the earlier visually dominant treatment to a quieter global flow cue.
- Normalized support panel conclusion/caption texts with the shared `panel-conclusion` role while preserving panel-specific roles such as `electrical-conclusion`, `origin-relation`, and `probe-conclusion`.
- Extended `engine.primitives.arrow()` with optional SVG attributes so reusable arrow roles can be attached without duplicating arrow geometry logic.

## Reusable asset candidates

- `engine.style.FigureStyle` typography and stroke tokens for figure-wide visual rhythm.
- `engine.primitives.arrow(..., attrs=...)` for semantic arrow role tagging.
- `render_fig1_l1._panel_text()` as a candidate for a small public text helper that supports panel roles.
- `verify_fig1_semantics.py` helpers `_panel_role_elements()` and `_semantic_group()` as candidates for a reusable semantic-SVG verifier utility.
- The DOS schematic primitive and schematic plot role checks from v9-v13 remain the strongest reusable scientific-figure assets.

## Fig1-only boundaries

- `fig1_l1_scene.py` remains Fig1-specific because it owns exact panel assignments, copy, local boxes, and figure-level story order.
- `visual_layout.yaml` remains Fig1-specific because its coordinates are derived from the current reference-layout pilot.
- Panel-specific copy such as `Converged deep charge trapping`, `S fraction -> S-S sequence -> deep traps`, and `Repulsion dominates over Maxwell attraction` should not be promoted into a shared engine.
- The v14 checks are reusable in shape, but their required counts are Fig1-specific until they are parameterized by scene layout.

## Human visual review

The verifier now blocks known semantic, geometry, label, role, and composition regressions. It still cannot certify final publication quality. The closeout gate remains: regenerate SVG/PNG, run the semantic verifier, parse SVG XML, compile Python files, convert with `rsvg-convert`, confirm deterministic SVG hash, preview `fig1_reference_semantic.png`, then record any remaining visual judgment gaps for human review.

## Remaining Direction

The next useful pass is not another local label nudge. It should either:

- promote reusable pieces into a small shared semantic-renderer module, or
- run a deliberate final visual review pass focused only on what still looks non-publication-grade in the rendered PNG.
