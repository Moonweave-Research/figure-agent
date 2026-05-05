# Panel A BR Comparison

Reference: `plugins/figure-agent/examples/fig1_overview/reference/variant_aesthetic_ref.png`
TikZ control: `plugins/figure-agent/examples/fig1_overview/fig1_overview.tex` lines 321-379, panel `[P5]`
Python spike: `experiments/python_svg_spike/panel_A_BR.svg`

This is a qualitative comparison note only. It does not assign a G2 score.

| feature | TikZ control | Python spike | non-scored assessment note |
| --- | --- | --- | --- |
| Curved cantilever | Bezier stroke with halo/body layers | Bezier stroke with amber ribbon, dark edge, and negative charge markers | Python version gives direct visual tuning of ribbon width and charge glyph placement. |
| Clamp and hatching | Small block and wall hatching | Hatched top block, clamp block, and callout | Python hatching was easy but manual; no clipping/pattern abstraction was used. |
| Electrode plate | Simple blue plate and +V label | Tall hatched grey plate with highlights and +V label | Python version matches the visual role and gives richer plate texture. |
| Force arrows | Red dominant arrow, small secondary arrow | Large red leftward repulsion arrow, smaller blue rightward Maxwell arrow | Arrow geometry was easy to tune; label placement required visual spacing judgment. |
| Field lines | Short E-field arrows in the control | Dashed curved field lines spanning beam to electrode | Python version follows the reference-style dashed coupling lines more closely than the control excerpt. |
| Probe/title | Title text and callout in TikZ | Top-left probe icon plus title text | Python icon is simplified but readable. |
| Bottom callout | Two-line text summary | Rounded callout with emphasized repulsion phrase | Required one render-based spacing correction for segmented text. |

Known non-scored gaps:
- The probe icon is schematic rather than a detailed microscope/probe illustration.
- Label placement and emphasis are manually tuned rather than layout-solved.
- The red repulsion arrow direction follows the spike spec/TikZ-control wording.
