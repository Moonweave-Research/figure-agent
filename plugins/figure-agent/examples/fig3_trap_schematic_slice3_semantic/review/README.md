# Slice 3 review boundary

The historical review is preserved unchanged at `source/REVIEW.md`. It is not
a verdict on this derivative. Machine gates may advance the fixture to
`review-ready`; Slice 3 remains open until separate human scaffold and artifact
verdicts bind the exact current inputs.

Review inputs:

- `full-render.png`: the complete six-panel derivative.
- `panel-e-render.png`: the structural-origin complex-panel crop.
- `fragment-svg.png` and `fragment-pdf.png`: fixed-size rasterizations of the
  editable SVG and its TeX-imported PDF.
- `fragment-difference-amplified.png`: amplified renderer-only raster delta.
- `human_scaffold_verdict.yaml`: exact hash bindings and pending human fields.
- `machine_receipt.yaml`: machine checks separated from human acceptance.

The ordinary compile passes. Strict mode exits 1 on inherited full-figure
detector findings; `machine_receipt.yaml` records them without reclassifying
the derivative as publication-accepted.
