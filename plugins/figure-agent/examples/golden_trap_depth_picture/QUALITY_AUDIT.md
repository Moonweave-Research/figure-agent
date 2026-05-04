# Golden Target 001 Quality Audit

## Rendered Artifacts

- Reference PNG: `reference/golden_target_001.png`
- Build PDF: `build/golden_trap_depth_picture.pdf`
- Build PNG: `build/golden_trap_depth_picture.png`
- Export PDF: `exports/golden_trap_depth_picture.pdf`
- Export SVG: `exports/golden_trap_depth_picture.svg`
- Export TIFF: `exports/golden_trap_depth_picture.tif`
- Export PNG: `exports/golden_trap_depth_picture.png`
- Diagnostic overlay: `build/golden_visual_clash_overlay.png`
- Latest refresh: after deep-dominant DOS correction, Row 1 `\PlotCallout`
  adoption, accepted-gate policy clarification, and critique-rubric
  label-placement hardening.

## Current Verdict

Status: first-pass vector reconstruction with multiple source-refit passes,
not yet accepted as manuscript-ready.
Fixture flag: `accepted: false`.

The fixture now proves the end-to-end quality-kernel path:

- reference PNG is fixed in the fixture;
- editable TikZ source compiles;
- PDF/SVG/TIFF/PNG exports exist;
- `/fig_status` reaches stage 6/6 without missing/stale notes;
- `scripts/check_golden_artifacts.py` passes the minimum artifact gates.
- accepted-mode gates reject this fixture until remaining visual/checker
  defects are resolved and `spec.yaml` is explicitly changed to
  `accepted: true`.

It does **not** yet satisfy the visual standard implied by the reference image.
Manual reference/build comparison keeps this fixture at `accepted: false`: the
current vector is structurally complete, but local typography, row spacing, and
the molecular-origin row still visibly diverge from the PNG target. The
right-side trap-depth panel contains the expected deep-dominant DOS lobe, Row 1
plot labels now use callout leaders instead of bare labels on traces, and the
repeated-label drift matcher no longer reports the old false `deep=0.373`
drift.

## Defect Table

| severity | layer | target area | defect | next action |
|---|---|---|---|---|
| BLOCKER | source | full layout | The figure is structurally complete and the export aspect ratio now closely matches the reference canvas, but local element positions and typography still need manual refit. | Refit local panels against the reference before calling the fixture accepted. |
| MAJOR | source | row 1 plots | Log-axis tick density is PGFPlots-driven, geometric collisions are cleared, and slope/τ labels now use `\PlotCallout`. Visual-clash heuristics still flag several tick/math labels. | Separate genuine readability defects from checker false positives and keep the compact log-axis + callout pattern. |
| MAJOR | source | right converged picture | Right-side energy/distribution diagram is present. CB/VB now read as line-style band edges, and the corrected deep-dominant g(E_t) lobe is visibly larger than the shallow lobe. | Continue aligning trap levels, dashed divider, and distribution lobes by manual reference comparison. |
| MAJOR | source | molecular origin row | Polymer chains and sulfur markers exist, but chain amplitude, sulfur placement, and dashed boxes are approximate. | Tune chain coordinates and sulfur marker positions against the reference PNG. |
| MAJOR | QA | collision/visual clash checks | `check_collisions.py` now reports 0 collisions. `check_visual_clash.py` reports 35 total candidates; many are known checker noise, and 13 remain tracked as source defects. Accepted-mode artifact gates still reject the fixture. | Drive the 13 source defects to 0 before acceptance; keep total candidates visible in the audit so false-positive drift remains reviewable. |
| MINOR | macro | repeated primitives | `TrapLevel`, `BandBox`, `BellCurve`, `paper loglog`, `PolymerChain`, and `PlotCallout` are now exercised in the fixture. `PlotCallout` closes the recurring bare-inline-label pattern, but it is still manual placement, not automatic collision avoidance. | Promote additional primitives only after repeated source edits or a second fixture proves a stable abstraction. |

## Checker Output

Compile command:

```bash
bash scripts/compile.sh examples/golden_trap_depth_picture/golden_trap_depth_picture.tex
```

Observed:

```text
OK: no collisions found in golden_trap_depth_picture.pdf (108 words)
35 visual clash candidate(s)
Generated: build/golden_trap_depth_picture.pdf, build/golden_trap_depth_picture.png (engine: lualatex)
```

Visual-clash triage:

```text
35 visual clash candidate(s)
Several likely checker false positives: math subscript/superscript fragments,
tick-label extraction, CB/VB compact band labels near band-edge lines, intended
chemfig S-on-backbone glyphs, and tiny symbol fragments from the equation icon.
Known false positives remain visible unless covered by
`_known_false_positives.yaml`, because the global false-positive policy should
stay conservative across future fixtures.
13 unresolved visual clash(es): Debye inset math fragments, row-2
equation/arrow spacing, row-label proximity to separators, S labels near chain
paths, and lower annotation text near paths. Row 1 slope and τ labels now use
`PlotCallout`; the remaining warnings are accepted-gate work, not a missing
callout primitive.
```

Layout-drift triage:

```text
Discharge drift=0.046 now matches within threshold after PGFPlots title
placement settled.
deep now matches within threshold (drift=0.040) after repeated single-token
labels started using the closest reference/PDF pair instead of first-hit
matching.
The `slope` OCR label remains `uncovered_ref` in the drift report despite being
visible in the build; this is a reference/OCR anchoring limitation, not a
compile or label-presence failure.
```

Artifact gate:

```bash
uv run python3 scripts/check_golden_artifacts.py examples/golden_trap_depth_picture --no-require-accepted --min-svg-elements 80 --min-png-width 1600
```

Observed:

```text
OK: golden artifact gates passed for golden_trap_depth_picture
```

Accepted-mode gate:

```bash
uv run python3 scripts/check_golden_artifacts.py examples/golden_trap_depth_picture --require-accepted --max-collisions 0 --max-visual-clashes 0
```

Current expected result:

```text
FAIL: fixture is not marked accepted: true
FAIL: unresolved visual clash budget exceeded: 13 > 0
```

## Acceptance Checklist

- [x] Reference PNG fixed in fixture.
- [x] Editable TikZ source exists.
- [x] Required source tokens present.
- [x] PDF/SVG/TIFF/PNG exports exist.
- [x] `/fig_status` reports stage 6/6 without missing/stale notes.
- [x] Minimum artifact gates pass.
- [x] Accepted-mode gate rejects the first pass.
- [ ] All visual elements match the reference closely.
- [x] `check_collisions.py` reports zero geometric text collisions.
- [ ] No visible text/path/fill clash after manual review.
- [x] Total checker warnings are separated from unresolved visual clashes.
- [ ] Unresolved visual clashes are fixed.
- [ ] Checker false positives are stable enough to suppress or document
  fixture-by-fixture.
- [ ] Typography and layout are manuscript-ready.
