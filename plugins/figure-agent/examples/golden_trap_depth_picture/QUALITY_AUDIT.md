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
- Latest refresh: after `TrapLevel` promotion into
  `styles/polymer-paper-preamble.sty`.

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
current vector is structurally complete, but the top Debye box/title, global
typography scale, right-side trap-depth panel proportions, and molecular-origin
row still visibly diverge from the PNG target.

## Defect Table

| severity | layer | target area | defect | next action |
|---|---|---|---|---|
| BLOCKER | source | full layout | The figure is structurally complete and the export aspect ratio now closely matches the reference canvas, but local element positions and typography still need manual refit. | Refit local panels against the reference before calling the fixture accepted. |
| MAJOR | source | row 1 plots | Log-axis tick density was reduced and geometric collisions are cleared, but visual-clash heuristics still flag several tick/math labels. | Separate genuine readability defects from checker false positives and keep the compact log-axis macro candidate. |
| MAJOR | source | right converged picture | Right-side energy/distribution diagram is present, horizontally compressed, and vertically lowered toward the reference, but internal spacing still does not match closely enough. | Continue aligning CB/VB, trap levels, dashed divider, and distribution lobes to a shared coordinate system. |
| MAJOR | source | molecular origin row | Polymer chains and sulfur markers exist, but chain amplitude, sulfur placement, and dashed boxes are approximate. | Tune chain coordinates and sulfur marker positions against the reference PNG. |
| MAJOR | QA | collision/visual clash checks | `check_collisions.py` now reports 0 collisions. `check_visual_clash.py` reports 42 total candidates; 4 are suppressible by `_known_false_positives.yaml`, 25 are documented checker noise, and 13 remain source defects. | Drive the 13 source defects to 0 before acceptance; keep total candidates visible in the audit so false-positive drift remains reviewable. |
| MINOR | macro | repeated primitives | `TrapLevel` was promoted into `polymer-paper-preamble.sty` and is used 8 times in the fixture. `BandBox`, `SmallLobe`, and chain patterns remain local until a second fixture proves reuse. | Promote additional primitives only after repeated source edits or a second fixture proves a stable abstraction. |

## Checker Output

Compile command:

```bash
bash scripts/compile.sh examples/golden_trap_depth_picture/golden_trap_depth_picture.tex
```

Observed:

```text
WARN: flagship_macros_unused
OK: no collisions found in golden_trap_depth_picture.pdf (115 words)
42 visual clash candidate(s)
Generated: build/golden_trap_depth_picture.pdf, build/golden_trap_depth_picture.png (engine: lualatex)
```

Visual-clash triage:

```text
42 visual clash candidate(s)
29 likely checker false positive(s): math subscript/superscript fragments,
tick-label extraction, CB/VB text inside intentional band boxes, and tiny
symbol fragments from the equation icon. Of these, 4 are currently suppressible
via `_known_false_positives.yaml`; the rest remain visible because the global
false-positive policy should stay conservative across future fixtures.
13 unresolved visual clash(es): top-row equation label proximity, Debye inset
math fragments, row-2 equation/arrow spacing, row-label proximity to separators,
S labels near chain paths, right-side distribution labels near fills, and lower
annotation text near paths.
```

Artifact gate:

```bash
uv run python3 scripts/check_golden_artifacts.py examples/golden_trap_depth_picture --min-svg-elements 80 --min-png-width 1600
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
