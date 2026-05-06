# Fig1 Scientific Plot Grammar Handback v7/v7b

## Goal

Build the v7 hybrid scientific plot grammar layer without replacing the semantic scene model or drawsvg compositor, then correct it to v7b reference-schematic grammar after visual review showed that literal mini plots were not appropriate for Fig1 overview.

## What Changed

- Added `src/engine/scientific_plots.py`.
- Kept typed scene payloads as the source of truth.
- Kept renderer dispatch by semantic object kind.
- Used Matplotlib as a grammar calculator for:
  - linear/log coordinate placement,
  - log-spaced decade hints in I(t),
  - payload-driven curve placement inside fixed local plot bounds.
- Kept drawsvg as the SVG compositor and writer.
- Preserved semantic object groups, `data-semantic-id`, `data-semantic-kind`, and payload-derived `data-payload-geometry` tokens.
- v7b removed visible plot frames, numeric tick labels, dense minor ticks, and grids from the evidence/ISPD glyphs.

## Plot Upgrades

### PowerLawDecayPlot

- Rebuilt the I(t) evidence plot as a reference-style log-log schematic glyph.
- Kept sparse decade hints without numeric tick labels.
- Generated the curve from payload `slope`, log range, and sample count.
- Kept the `I(t) ~ t^-n` label and slope label contained inside the local plot bounds.

### PEHysteresisPlot

- Rebuilt the P-E evidence plot with schematic arrow axes and a center dashed guide.
- Smoothed the hysteresis loop with a denser payload-driven parametric curve.
- Removed numeric ticks and plot frame so the mark reads as a measurement icon, not a data panel.

### ISPDPlot

- Added a compact energy/DOS schematic axis.
- Rendered shallow and deep DOS-like lobes inside the local ISPD box.

## Verifier Upgrades

`src/verify_fig1_semantics.py` now checks:

- Required schematic roles for P-E, I(t), and ISPD.
- Rejection of over-real plot frames, numeric tick labels, major/minor tick roles, and grid-like plot grammar in these glyphs.
- Schematic labels inside local plot bounds.
- Shapely containment checks through `uv`.
- svgelements parsing of the rendered SVG through `uv`.
- Existing semantic bbox, forbidden framing, artifact, and payload-mutation checks.

The existing payload mutation check still verifies that trap, DOS, P-E, and decay payload changes alter visible SVG geometry after stripping `data-payload-geometry`.

## Generated Artifacts

- `fig1_reference_semantic.svg`
- `fig1_reference_semantic.png`
- `reference_vs_fig1_reference_semantic.png`

## Verification Record

Fresh commands run on 2026-05-06:

```bash
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/render_fig1_l1.py
python experiments/python_svg_semantic_fig1/src/verify_fig1_semantics.py
python -m xml.etree.ElementTree experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg
rsvg-convert -w 1595 -h 986 experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg -o /tmp/fig1_reference_semantic_check.png
```

Results:

- Render completed and regenerated all three artifacts.
- Semantic verifier output: `fig1 semantic contract passed`.
- XML parse exited with status 0.
- `rsvg-convert` exited with status 0.
- Deterministic SVG hash confirmed across two fresh render runs:
  `870642acdd28e9ec81dd7e0fbf7036bccd7026c62ac068c30311e5f96cfa4bc0`.

## Remaining Gap

v7 first implemented Option A too literally and produced small publication-style plots. v7b keeps the useful calculation layer but restores the reference-schematic visual vocabulary: graph-shaped icons, sparse guides, and semantic labels. The current output is still a scaffold rather than final figure art, but the verifier now protects against drifting back into over-real mini plots.
