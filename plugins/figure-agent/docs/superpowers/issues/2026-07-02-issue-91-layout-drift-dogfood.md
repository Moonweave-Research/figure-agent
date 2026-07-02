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
- `g(Et)`: drift `0.308 > 0.050`
- `Coulomb`: drift `0.294 > 0.050`
- `repulsion`: drift `0.304 > 0.050`
- Several required labels are currently skipped as `uncovered_ref` or
  `uncovered_both`, including broad panel labels and OCR-sensitive symbols.

## Follow-up Plan

Use the current real fixture before changing policy:

1. Triage skipped labels into expected OCR limitations, reference omissions, and
   genuine missing rendered labels. Complete for the first fig1 pass; see
   "Triage Pass 1" below.
2. Decide whether the checker needs label normalization for formulas/symbols
   such as `g(Et)`, `FMaxwell`, `Vactive`, and `qtr`. Narrow token
   normalization now handles decorated/split forms for several of these; see
   "Triage Pass 2" below.
3. Decide whether strict mode should fail on `uncovered_ref` / `uncovered_both`
   for publication fixtures or keep those as report-only findings.
4. Only then tune thresholds or add per-label exceptions.

## Triage Pass 1

The first real fixture pass separates comparable drift from coverage and
normalization gaps. The checker is doing useful work, but only a subset of the
required labels are currently comparable against the OCR reference.

| Class | Labels | Interpretation | Next action |
| --- | --- | --- | --- |
| Real comparable drift | `localized traps`, `Debye`, `Coulomb`, `repulsion` | Reference and build both contain the phrase, and normalized centers differ beyond `0.050`. These are actionable drift findings unless the reference image is no longer the intended spatial target. | Inspect/update the fig1 layout or explicitly re-baseline the reference target. |
| Ambiguous single-token anchor | `Probe` | Reference OCR finds `probe` near `(0.877, 0.535)` while build PDF finds `probe` near `(0.514, 0.534)`. The y coordinate is similar but x differs by a full panel, so this is likely a same-word/different-context match rather than reliable drift. | Replace the required label with a more specific phrase or add phrase/window context before enforcing. |
| Build-only labels (`uncovered_ref`) | `Sulfur-rich polymer`, `poly(S-r-DIB) linear copolymer`, `Sulfur content`, `real space`, `energy diagram`, `poly(S-r-DIB) thin film`, `convergent evidence`, `kinetic`, `ISPD`, `mechanical`, `MIM stack`, `polymer film`, `SMU`, `Vs meter`, `I(t)`, `high n`/`hig h n`, `low n`, `electrode`, `air gap` | The rendered PDF contains these labels, but the reference OCR does not contain the same phrases. These are not evidence of missing rendered labels; they are reference/OCR coverage gaps for drift comparison. | Keep report-only unless publication policy requires reference coverage; do not tune drift threshold for these. |
| Symbol/formula normalization gaps (`uncovered_both`) | `HV`, `Vactive`, `g(Et)`, `FMaxwell`, `qtr` | The visual content appears in split or decorated forms: examples include `HV+`, `V` + `active`, `g(E`, `Maxwell`, and `q` + `tr`. Exact token matching cannot compare these labels. | Add explicit accepted forms in `required_labels` or implement formula-aware normalization before using these as hard blockers. |
| Broad phrase absent from exact OCR/PDF text (`uncovered_both`) | `three independent probes` | The phrase is too high-level for the current exact-token checker; neither side exposes the complete phrase contiguously. | Convert to concrete visible labels or remove from layout drift enforcement. |

Policy implication: strict mode is ready to block on comparable phrase drift,
but not ready to treat all `uncovered_*` statuses as publication blockers. The
next code change should improve label specificity/normalization before changing
failure policy.

## Triage Pass 2

Narrow token normalization now strips simple token decorations and compares
compact adjacent tokens. This improves the fig1 classification without changing
strict policy:

- `HV`, `Vactive`, and `qtr` moved from `uncovered_both` to `uncovered_ref`.
  The checker can now recognize the rendered forms (`HV+`, `V` + `active`, and
  `q` + `tr` / `qtr`) but the reference OCR still lacks comparable anchors.
- `g(Et)` is now comparable and reports drift `0.308 > 0.050`.
- `FMaxwell` remains `uncovered_both`; the reference/PDF OCR exposes `Maxwell`
  but does not contain the full required label.
- `Probe` remains an ambiguous single-token drift and should still be
  specialized before being used as a hard publication blocker.

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
- [x] Triage strict drift and uncovered-label findings before changing checker
      policy or thresholds.
- [x] Normalize decorated/split token forms for layout-drift matching.
- [ ] Specialize remaining ambiguous formula/single-token labels before
      expanding strict publication-blocking policy.

## Verification

- `./bin/fig-agent helper reference_extract.py fig1_overview_v2_pair_001_vault --rebuild`
  -> `OK: extracted 120 text labels, 8 palette colors (28 shape components),
     structural_regions: unavailable`
- `rg -n "golden_contract:|required_labels:" plugins/figure-agent/examples -g spec.yaml`
  -> only `fig1_overview_v2_pair_001_vault/spec.yaml`
- `uv run python3 scripts/checks/check_layout_drift.py fig1_overview_v2_pair_001_vault --strict`
  -> exits `1` with real strict findings, including `localized traps`,
     `Probe`, `Debye`, `g(Et)`, `Coulomb`, and `repulsion` drift warnings
- `./bin/fig-agent compile fig1_overview_v2_pair_001_vault`
  -> exits `0`, emits the same layout-drift warnings, and writes fresh
     `build/fig1_overview_v2_pair_001_vault.{pdf,png}`
- `./bin/fig-agent status fig1_overview_v2_pair_001_vault --json`
  -> reports `coordinate_hints: present` and `render_state: FRESH`
- local label-presence probe over `coordinate_hints.yaml` and extracted PDF
  words
  -> separates comparable drift, build-only labels, ambiguous single-token
     anchors, and symbol/formula normalization gaps
- `uv run pytest -q tests/test_check_layout_drift.py`
  -> covers skip behavior, drift warning behavior, and CLI success when a
     fixture has `coordinate_hints.yaml`
