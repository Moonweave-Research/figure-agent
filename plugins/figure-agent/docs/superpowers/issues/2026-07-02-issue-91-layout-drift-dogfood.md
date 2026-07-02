# Issue 91 - Layout Drift Gate Dogfood

Status: real-fixture dogfood complete; strict drift follow-up required

Type: restored compile gate dogfood, coordinate-hints fixture coverage

## Context

PR #88 restored `scripts/checks/check_layout_drift.py` as a compile-time
check when a fixture has `coordinate_hints.yaml`. The gate is intentionally
narrow: it compares `golden_contract.required_labels` against OCR/reference
text labels from `coordinate_hints.yaml` and words extracted from the rendered
PDF.

## Dogfood Result

The restored gate now has one checked-in real fixture path:
`fig1_overview_v2_pair_001_vault`.

- `fig1_overview_v2_pair_001_vault` remains the only fixture with
  `golden_contract.required_labels`.
- `coordinate_hints.yaml` was generated from the fixture reference image
  (`reference/codex_gen_overview_v1.png`) using the local reference-extract
  helper. The extraction produced 120 OCR text labels, 8 palette colors, and
  28 shape components; `structural_regions` are unavailable for this reference.
- The direct strict checker no longer takes the missing-hints skip path. It
  exits nonzero on real drift and coverage findings.
- The normal compile path invokes the layout-drift checker when the hints file
  is present. Compile remains report-only for this gate and exits zero while
  surfacing the same drift warnings.
- `fig-agent status` now reports `coordinate_hints: present` and a fresh render.
  Remaining publication blockers are critique/export/provenance, not missing
  coordinate hints.

The first strict dogfood pass found real label drift and OCR/coverage gaps
rather than a wiring failure. Representative strict findings:

- `localized traps`: drift `0.094 > 0.050`
- `Probe`: drift `0.363 > 0.050`
- `Debye`: drift `0.095 > 0.050`
- `Coulomb`: drift `0.294 > 0.050`
- `repulsion`: drift `0.304 > 0.050`
- Several required labels are currently skipped as `uncovered_ref` or
  `uncovered_both`, including broad panel labels and OCR-sensitive symbols.

## Follow-up Plan

Use the current real fixture before changing policy:

1. Triage skipped labels into expected OCR limitations, reference omissions, and
   genuine missing rendered labels.
2. Decide whether the checker needs label normalization for formulas/symbols
   such as `g(Et)`, `FMaxwell`, `Vactive`, and `qtr`.
3. Decide whether strict mode should fail on `uncovered_ref` / `uncovered_both`
   for publication fixtures or keep those as report-only findings.
4. Only then tune thresholds or add per-label exceptions.

## Acceptance Status

- [x] Identified the only current required-label fixture.
- [x] Verified there are no checked-in `coordinate_hints.yaml` files under
      `examples/`.
- [x] Ran the direct checker and confirmed the current skip behavior.
- [x] Documented why compile cannot prove the drift gate with current fixtures.
- [x] Recorded the minimal next fixture plan.
- [x] Added synthetic CLI coverage proving a fixture with `coordinate_hints.yaml`
      reports matched labels instead of taking the missing-hints skip path.
- [x] Dogfooded matched/drifted label behavior on real `coordinate_hints.yaml`
      data.
- [ ] Triage strict drift and uncovered-label findings before changing checker
      policy or thresholds.

## Verification

- `./bin/fig-agent helper reference_extract.py fig1_overview_v2_pair_001_vault --rebuild`
  -> `OK: extracted 120 text labels, 8 palette colors (28 shape components),
     structural_regions: unavailable`
- `rg -n "golden_contract:|required_labels:" plugins/figure-agent/examples -g spec.yaml`
  -> only `fig1_overview_v2_pair_001_vault/spec.yaml`
- `uv run python3 scripts/checks/check_layout_drift.py fig1_overview_v2_pair_001_vault --strict`
  -> exits `1` with real strict findings, including `localized traps`,
     `Probe`, `Debye`, `Coulomb`, and `repulsion` drift warnings
- `./bin/fig-agent compile fig1_overview_v2_pair_001_vault`
  -> exits `0`, emits the same layout-drift warnings, and writes fresh
     `build/fig1_overview_v2_pair_001_vault.{pdf,png}`
- `./bin/fig-agent status fig1_overview_v2_pair_001_vault --json`
  -> reports `coordinate_hints: present` and `render_state: FRESH`
- `uv run pytest -q tests/test_check_layout_drift.py`
  -> covers skip behavior, drift warning behavior, and CLI success when a
     fixture has `coordinate_hints.yaml`
