# G3 Shape/Coordinate Parsing Plan

## Goal

Ship G3 only: expand deterministic source/PDF geometry vocabulary so circles and curves are typed and measured, and commit before/after parse coverage. Do not build G1 vector relations or auto-promote curve-envelope findings.

## Constraints

- No LLM or aesthetic pass/fail gate.
- No topology or intent inference; G3 adds typed geometry vocabulary and coverage, not declaration-free vector correctness rules.
- No auto-promotion of conservative curve/circle envelope findings.
- Named-coordinate resolution remains out of scope unless a target fixture uses named coordinates; this corpus baseline has no meaningful named-coordinate coverage need.
- Keep G3 as a separate stacked PR over G2; do not batch G1.

## Baseline Measured Before Implementation

Measured with the existing `_parse_tikz_geometry()` over draw/fill/shade operations:

| fixture | ops | parsed | coverage | circle tokens | controls tokens |
|---|---:|---:|---:|---:|---:|
| fig1_overview_v5f_art_direction_001_vault | 260 | 96 | 0.369 | 53 | 23 |
| fig2_trap_design_space | 21 | 12 | 0.571 | 0 | 5 |
| fig3_floating_clip_protocol | 39 | 22 | 0.564 | 6 | 2 |
| fig3_resistance_mechanism | 21 | 9 | 0.429 | 0 | 1 |
| fig3_trapping_concept | 16 | 13 | 0.812 | 0 | 1 |
| fig1_overview_v5a_polish_001_vault | 225 | 83 | 0.369 | 46 | 14 |
| fig1_overview_v5b_editorial_001_vault | 224 | 82 | 0.366 | 46 | 14 |
| fig1_overview_v5c_quiet_001_vault | 224 | 80 | 0.357 | 46 | 14 |
| fig1_overview_v5d_redraw_001_vault | 220 | 79 | 0.359 | 46 | 14 |
| fig1_overview_v5e_aggressive_001_vault | 222 | 78 | 0.351 | 47 | 16 |

## Implementation Steps

1. Add RED parser tests in `tests/test_undeclared_geometry.py`.
   - Numeric circles such as `\fill (2,3) circle (0.25);` parse as `circle` with center, radius, and bbox in pt.
   - Bézier source paths with `.. controls (...) and (...) .. (...)` parse as `curve` with control-hull bbox and `clearance_mode: conservative_hull`.
   - Non-literal circles such as `circle ({2.35*\rr})` produce coverage WARN/UNKNOWN rather than a fake numeric geometry.
   - Parse coverage summaries count operations, parsed typed geometry, unknown operations, circles, curves, and unsupported named-coordinate/calc forms.

2. Implement source geometry vocabulary in `scripts/checks/check_undeclared_geometry.py`.
   - Add typed parsing for literal numeric circles.
   - Add typed parsing for cubic Bézier control-hull envelopes.
   - Track one coverage record per draw/fill/shade operation.
   - Preserve existing line/rect candidate behavior and IDs.

3. Add coverage report output.
   - Extend `undeclared_geometry_payload()` with `geometry_parse_coverage`.
   - Include totals, per-kind parsed counts, unknown count, unknown reasons, and non-auto-promotable curve/circle envelope note.
   - Keep malformed or missing required input fail-loud.

4. Consume rendered PDF curves in the existing undeclared geometry path.
   - Reuse `pdfplumber` `page.curves` already used by `perception_pack.py`.
   - Add deterministic rendered curve envelope accounting to the coverage report, not auto-promoted candidates.

5. Commit corpus coverage artifact.
   - Generate `docs/superpowers/reports/2026-07-07-g3-parse-coverage.json`.
   - Include before and after numbers for fig1 v5f, fig2, fig3, and v5a-e.
   - Record remaining UNKNOWN reasons without turning them into failures.

6. Verify and publish.
   - Run targeted undeclared-geometry tests.
   - Run ruff on changed Python.
   - Compile/quality-map v5f and confirm no new auto-promoted curve/circle findings are introduced by G3.
   - Run the full plugin-root suite.
   - Push `g3-shape-coordinate-parsing` and open a stacked PR over `g2-text-alignment`.
