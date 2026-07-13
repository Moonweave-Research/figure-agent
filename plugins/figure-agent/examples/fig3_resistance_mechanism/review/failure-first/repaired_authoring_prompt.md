# Clean-room repaired attempt: declared layout-lane constraint

Create one new editable TikZ/LaTeX source named `repaired_generated.tex` in this
directory. This is a clean-room authoring attempt, not a modification of any
existing figure.

You may read only these inputs:

- `../../briefing.md`
- `../../spec.yaml`
- `../../authoring_contract.md`
- `../../panel_goals.md`
- `layout_lane_contract.yaml`
- `repaired_authority_packet.yaml`

Do not read or copy the maintained Fig3 source, raw/style-control/verified
artifacts, historical Fig3 artifacts, any Fig1 artifact, or Python/SVG pilot.

Authoring requirements:

- Use a standalone LaTeX document with `\usepackage{polymer-paper-preamble}`
  and TikZ; do not use SVG or Python drawing.
- Preserve the declared two-panel scientific narrative and all semantic
  boundaries from the allowed authority files.
- Keep the complete Panel A narrative text group `applied`, `trapping`,
  `during`, `conduction` at least `0.015` page-diagonal units clear of the
  applied-bias marker text `V`.
- Reserve distinct reading lanes before placing details: panel marker/title,
  bias/electrodes, transport/trapping mechanism, plot, and annotation.
- Use compact publication-scale hierarchy; do not solve collisions by making
  the canvas, title, or labels oversized.
- Do not claim measured quantitative data, carrier polarity, trap chemistry,
  or a spatial trap network.
- Produce only `repaired_generated.tex`. Do not compile, create manifests,
  edit contracts, or commit.

This attempt is `constraint_guided_not_equal_input`; it cannot be claimed as a
fair raw/verified/repaired ablation or publication acceptance.
