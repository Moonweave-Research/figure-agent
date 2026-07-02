# Issue 91 - Layout Drift Gate Dogfood

Status: precondition missing; fixture plan recorded

Type: restored compile gate dogfood, coordinate-hints fixture coverage

## Context

PR #88 restored `scripts/checks/check_layout_drift.py` as a compile-time
check when a fixture has `coordinate_hints.yaml`. The gate is intentionally
narrow: it compares `golden_contract.required_labels` against OCR/reference
text labels from `coordinate_hints.yaml` and words extracted from the rendered
PDF.

## Dogfood Result

The repository currently has no real fixture that can exercise the restored
gate end to end:

- `find plugins/figure-agent/examples -name coordinate_hints.yaml -print`
  returned no fixtures.
- `fig1_overview_v2_pair_001_vault` is the only fixture with
  `golden_contract.required_labels`.
- Direct checker run against that fixture exits successfully but skips because
  the required hints file is absent:
  `SKIP layout drift: missing coordinate_hints.yaml in examples/fig1_overview_v2_pair_001_vault`.
- `scripts/compile.sh` only invokes the drift checker inside
  `if [[ -f "coordinate_hints.yaml" ]]`; therefore current compile runs cannot
  prove label matching, drift reporting, or false-positive behavior.

This means the restored gate is wired, but not dogfooded on real OCR/reference
hints yet.

## Minimal Fixture Plan

Use the smallest real-fixture path before tuning thresholds:

1. Pick `fig1_overview_v2_pair_001_vault` unless a smaller accepted fixture
   gains `golden_contract.required_labels` first.
2. Add or regenerate a real `coordinate_hints.yaml` from the fixture reference
   image using `/fig_extract <name>` rather than hand-authoring synthetic hints.
3. Run the direct checker:
   `uv run python3 scripts/checks/check_layout_drift.py fig1_overview_v2_pair_001_vault --strict`.
4. Run the compile path only after TeX/render dependencies are available:
   `scripts/compile.sh fig1_overview_v2_pair_001_vault.tex` from the fixture
   directory with strict mode enabled.
5. Record each required label as matched, skipped, drifted, missing in build,
   or missing in reference.
6. Add focused regression tests only if this dogfood pass requires threshold,
   token matching, or skip-policy changes.

## Acceptance Status

- [x] Identified the only current required-label fixture.
- [x] Verified there are no checked-in `coordinate_hints.yaml` files under
      `examples/`.
- [x] Ran the direct checker and confirmed the current skip behavior.
- [x] Documented why compile cannot prove the drift gate with current fixtures.
- [x] Recorded the minimal next fixture plan.
- [ ] Dogfood matched/drifted label behavior on real `coordinate_hints.yaml`
      data.

## Verification

- `find plugins/figure-agent/examples -maxdepth 2 -name coordinate_hints.yaml -print | wc -l`
  -> `0`
- `rg -n "golden_contract:|required_labels:" plugins/figure-agent/examples -g spec.yaml`
  -> only `fig1_overview_v2_pair_001_vault/spec.yaml`
- `uv run python3 scripts/checks/check_layout_drift.py fig1_overview_v2_pair_001_vault --strict`
  -> skipped because `coordinate_hints.yaml` is missing

