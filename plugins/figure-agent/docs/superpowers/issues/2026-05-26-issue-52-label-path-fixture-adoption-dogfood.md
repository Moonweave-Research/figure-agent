# Issue 52 — Label-Path Fixture Adoption Dogfood

Status: completed in commit 1924d31

## Problem

Issue 51 shipped the plugin-level label-path proximity gate, but real fixtures
do not benefit until critical semantic lines and curves are declared in
`spec.yaml.label_path_proximity_checks`.

The first dogfood target is `fig1_overview_v2_pair_001_vault`, because it
exposed the motivating zoom-only near-miss failures:

- `mobility edge` visually stacked on a dashed reference line.
- `shallow` crowded by a nearby deep escape curve.

Issue 51 post-commit dogfood proved that an external temporary spec can detect
both cases as `LP###` candidates without modifying figure source:

- `shallow` -> `label_curve_near_label`
- `mobility edge` -> `label_stacked_on_reference_line`

This issue is the fixture-contract adoption slice, not another plugin-engine
feature.

## Current-Main Caveat

At branch start, `main` still carries the source positions visible in
`fig1_overview_v2_pair_001_vault.tex`:

- `mobility edge` at source y `7.85`
- `shallow` at source x `11.60`

Those positions may still produce real LP candidates once checks are adopted.
That is not a plugin failure. If candidates appear, record the dogfood as
"adoption surfaced a live near-miss" and keep source polishing out of scope.

## Scope

In scope:

- Add minimal `label_path_proximity_checks` to selected real fixture specs.
- Prefer high-risk semantic paths only: reference lines, semantic curves, and
  label-critical baselines that have actually produced zoom-only misses.
- Run `/fig_compile` and confirm `build/label_path_proximity.json` is present.
- Run `/fig_critique` or equivalent host-vision critique refresh and confirm
  every `LP###` candidate is accounted through `micro_defects[].label_path_ref`.
- Record dogfood evidence in a milestone doc.

Out of scope:

- Editing `.tex` source as part of this issue.
- Changing figure design or accepting/rejecting the figure's visual state.
- Broadly declaring every decorative line, hatch, or background wave.
- Making `label_path_proximity_checks` auto-infer arbitrary TikZ paths.
- Mutating accepted/golden/export state.

## Candidate Fixture Contract

For `fig1_overview_v2_pair_001_vault`, start with two checks:

```yaml
label_path_proximity_checks:
  - id: panel_c_mobility_edge_reference
    kind: horizontal_line
    role: reference_line
    y_pdf_cm: <measured from PDF>
    x_range_pdf_cm: [<left>, <right>]
    clearance_pt: 4.0
    text_phrases:
      - id: mobility_edge
        words: [mobility, edge]
  - id: panel_c_deep_escape_curve
    kind: polyline
    role: semantic_curve
    points_pdf_cm:
      - [<x0>, <y0>]
      - [<x1>, <y1>]
      - [<x2>, <y2>]
    clearance_pt: 5.0
    text_allowlist: [shallow]
```

Coordinates must be measured from the compiled PDF page using the same top-left
PDF-cm convention as other figure-agent geometry contracts.

## Acceptance Criteria

- The real fixture spec contains only narrowly justified label-path proximity
  checks.
- `bash scripts/compile.sh examples/<name>/<name>.tex` emits
  `build/label_path_proximity.json`.
- A no-issue current render is allowed to produce zero candidates; this should
  be recorded as a clean adoption state, not a failure.
- A deliberately regressed scratch copy or historical-shape replay produces the
  expected `LP###` candidates for the known near-miss class.
- If current `main` already carries the historical near-miss shape, live
  candidate emission from the current render satisfies the historical-shape
  replay evidence; do not create a scratch copy just to reproduce the same
  geometry.
- If candidates are present, `critique_lint.py` rejects a critique missing the
  corresponding `micro_defects[].label_path_ref`.
- Generated build artifacts and scratch regression copies are not committed.

## Execution Plan

1. Add a focused test that the real `fig1_overview_v2_pair_001_vault/spec.yaml`
   declares exactly the two intended label-path checks.
2. Add the two checks to `spec.yaml` using measured PDF-cm coordinates from the
   current compiled PDF.
3. Run `/fig_compile` on the fixture and inspect
   `build/label_path_proximity.json`.
4. If the current fixture emits LP candidates, treat them as dogfood evidence
   and do not patch `.tex` in this issue.
5. Record the result in a milestone doc, including whether the current render is
   clean or whether live candidates were surfaced.
6. Run targeted tests, lint/diff checks, and then perform 10 critical review
   passes across contract, fixture scope, false-positive risk, freshness,
   critique-accounting, generated-artifact hygiene, CI fit, documentation,
   source-containment, and readiness.

## Review Questions

- Are the declared paths semantically critical enough to justify recurring
  checks?
- Are clearance thresholds narrow enough to avoid turning decorative density
  into false-positive noise?
- Does the dogfood evidence prove both clean-current behavior and historical
  regression catchability?
- Does the fixture adoption remain separate from actual figure polishing work?
