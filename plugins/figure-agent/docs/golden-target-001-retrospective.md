# Golden Target 001 Retrospective

## Outcome

`examples/golden_trap_depth_picture` is landed as N=1 evidence for the v0.2
quality-kernel direction, but it remains `accepted: false`. The fixture proves
that a fixed reference PNG, editable TikZ source, compile/export chain,
artifact gates, and an explicit accepted-mode blocker can live together in one
reproducible folder. It does not yet prove publication-quality visual
reconstruction: the current vector is structurally complete, but the top Debye
box/title, typography scale, right-side trap-depth panel proportions, and
molecular-origin row still visibly diverge from the golden PNG.

## Defect Distribution

- Source: 13 unresolved visual defects. Representative examples are Debye inset
  math/title spacing, row-label proximity to separators, S labels near polymer
  chains, and right-side distribution labels near filled lobes.
- Macro: 1 promoted primitive. `\TrapLevel` moved from fixture-local source to
  `styles/polymer-paper-preamble.sty` and is used 8 times. `BandBox`,
  `SmallLobe`, and chain patterns remain local until a second fixture proves
  reuse.
- Export: 0 current blocker defects. PDF/SVG/TIFF/PNG exports are generated and
  tracked for this fixture; PNG corners are opaque white.
- QA: 29 visual-clash candidates are treated as checker noise or known false
  positives. 4 are suppressible through `_known_false_positives.yaml`; the rest
  stay visible because global suppression would be too broad for future
  fixtures.

## Figure-Agent Gaps

- `/fig_status` now recognizes `reference_image`, and `selected_preview_missing`
  did not fire for this fixture. It still does not surface `accepted: false` as
  a first-class status signal, so "stage 6/6" can be mistaken for figure
  acceptance.
- `scripts/check_golden_artifacts.py` is still partly fixture-specific. The
  required-label contract and source inventory are useful for this trap-depth
  figure, but they are not yet a reusable schema for arbitrary golden targets.
- Export tracking policy exists as a fixture-specific `.gitignore` exception
  plus LFS for TIFF, not as a documented repo-level policy for future golden
  fixtures.
- `SKILL.md` says "No data plots", while this fixture contains qualitative
  log-axis schematics. The real boundary should be stated as "symbolic
  schematic axes are allowed; quantitative data plots and measured datasets are
  out of scope."
- `check_visual_clash.py` can report and optionally suppress known patterns, but
  it does not yet write a structured per-fixture classification file. Manual
  `QUALITY_AUDIT.md` triage is still required.

## Next Action

Keep this fixture unaccepted and use it to drive the next v0.2 kernel work:
generalize the golden-target contract, expose accepted-state in status output,
document export tracking, and only then continue visual refit toward
`accepted: true`.
