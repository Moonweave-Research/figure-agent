# Label-Path Fixture Adoption Dogfood

**Date:** 2026-05-26 KST
**Status:** fixture metadata adopted; current render surfaces live candidates

## Scope

This milestone applies the label-path proximity gate to the active
`fig1_overview_v2_pair_001_vault` fixture. The goal is to make the plugin catch
the zoom-only near-miss class where a label is visually too close to a semantic
line or curve without producing a normal text collision.

This pass changes fixture metadata only. It does not edit the TikZ source,
generated build artifacts, export artifacts, accepted state, golden state, or
SVG-polish state.

## Adopted Contract

The fixture now declares two narrow `spec.yaml.label_path_proximity_checks`:

- `panel_c_mobility_edge_reference`: a horizontal reference-line check for the
  `mobility edge` phrase, with `4.0pt` clearance.
- `panel_c_deep_escape_curve`: a semantic polyline check for the `shallow`
  label, with `5.0pt` clearance.

These checks intentionally target the two real failure shapes that motivated
the plugin gate. Decorative density, background waves, and unrelated paths are
not declared in this first fixture adoption slice.

## TDD Evidence

Baseline targeted regression suite:

```bash
uv run pytest -q tests/test_label_path_proximity.py tests/test_compile_contract.py
```

Result: `14 passed`.

New focused test first failed because the fixture did not declare any
`label_path_proximity_checks`:

```bash
uv run pytest -q \
  tests/test_label_path_proximity.py::test_fig1_vault_declares_minimal_label_path_proximity_checks
```

Result before implementation: failed with missing
`panel_c_mobility_edge_reference` and `panel_c_deep_escape_curve`.

After adding the fixture metadata, the focused test passed:

```bash
uv run pytest -q \
  tests/test_label_path_proximity.py::test_fig1_vault_declares_minimal_label_path_proximity_checks
```

Result: `1 passed`.

The full label-path unit suite also passed:

```bash
uv run pytest -q tests/test_label_path_proximity.py
```

Result: `9 passed`.

## Compile Dogfood

Compile command:

```bash
bash scripts/compile.sh \
  examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex
```

Observed:

- compile exited 0
- `build/label_path_proximity.json` was emitted
- `label_path_proximity.json.total`: 2
- compiler footer emitted two label-path proximity warnings:
  - `LP001`: `label_curve_near_label`, text `shallow`, path
    `panel_c_deep_escape_curve`, distance `0.0pt`
  - `LP002`: `label_stacked_on_reference_line`, text `mobility edge`, path
    `panel_c_mobility_edge_reference`, distance `0.0pt`

## Critique Handoff Evidence

Brief command:

```bash
uv run python3 scripts/critique_brief.py \
  examples/fig1_overview_v2_pair_001_vault \
  | rg "Label-Path Proximity|LP001|LP002|label_path_ref"
```

Observed:

- the brief emitted `## Label-Path Proximity Candidates`
- the brief listed both `LP001` and `LP002`
- the brief linked the candidates to dedicated zoom crops:
  - `build/audit_crops/label_path/LP001_shallow.png`
  - `build/audit_crops/label_path/LP002_mobility_edge.png`
- the output schema included the `label_path_ref` field

Negative lint check:

```bash
uv run python3 scripts/critique_lint.py \
  examples/fig1_overview_v2_pair_001_vault
```

Observed expected failure:

```text
BLOCKER: label_path_accounting: label_path_proximity.json candidates must be referenced by micro_defects[].label_path_ref; missing: LP001, LP002
```

The existing critique was not refreshed in this issue. The important plugin
behavior is that LP candidates are now first-class critique inputs and cannot be
silently omitted from a fresh critique that uses the active schema.

## Current-Render Interpretation

This is a useful adoption result, not a plugin regression. At branch start,
current `main` still had the source positions that motivated this slice:

- `mobility edge` at source y `7.85`
- `shallow` at source x `11.60`

Once the fixture contract was adopted, the compile gate surfaced those
remaining near-miss shapes as first-class `LP###` evidence. The source-level
polish belongs to figure work outside this plugin-adoption issue.

## Remaining Limitation

This fixture adoption does not prove broad auto-inference of all label-path
hazards. It proves that explicit, semantically critical paths in `spec.yaml`
can turn zoom-only near-misses into deterministic compile evidence and critique
accounting inputs.

## Ten-Pass Review Log

1. **Scope containment:** clean. The diff changes fixture metadata, one focused
   test, and docs only. No TikZ source, accepted/golden/export, or SVG-polish
   state was edited.
2. **Path semantic fit:** clean. Both declared paths are semantic hazards tied
   to observed failures: a reference baseline and a deep escape curve.
3. **Coordinate convention:** clean. Coordinates use the existing top-left
   PDF-cm convention consumed by `check_label_path_proximity.py`.
4. **Threshold risk:** clean. `4.0pt` and `5.0pt` clearances are narrow enough
   to avoid broad decorative-path noise while still catching the current
   near-miss shapes.
5. **TDD coverage:** clean. The new real-fixture test fails if the two checks
   disappear or are broadened by extra declarations.
6. **Compile integration:** clean. `/fig_compile` emits
   `label_path_proximity.json` with deterministic `LP001` and `LP002`
   candidates.
7. **Critique integration:** clean. `critique_brief.py` surfaces the LP
   candidates and crops; `critique_lint.py` rejects missing `label_path_ref`
   accounting.
8. **Generated artifact hygiene:** clean. Build outputs and audit crops are
   ignored and are not part of the commit.
9. **Documentation completeness:** fixed. The issue status now reflects
   implemented/pending-commit state and this milestone records the live-candidate
   interpretation.
10. **Release/CI regression risk:** clean. Targeted and full test suites pass,
    ruff is clean, diff whitespace is clean, and plugin validation passes.
