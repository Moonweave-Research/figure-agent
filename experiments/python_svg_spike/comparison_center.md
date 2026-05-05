# Panel B Center Comparison

Reference: `plugins/figure-agent/examples/fig1_overview/reference/variant_aesthetic_ref.png`
TikZ control: `plugins/figure-agent/examples/fig1_overview/fig1_overview.tex` lines 159-250, panel `[P3]`
Python spike: `experiments/python_svg_spike/panel_B_center.svg`

This is a qualitative comparison note only. It does not assign a G2 score.

| feature | TikZ control | Python spike | non-scored assessment note |
| --- | --- | --- | --- |
| Title/card | Title in central hero region | Large red title inside rounded card | Typography is clear, though title sizing is manually chosen. |
| Energy/band structure | LUMO/HOMO tints, axis, shallow/deep levels | LUMO/HOMO boxes, vertical energy axis, blue/red level stacks | Semantic structure is preserved with direct coordinate control. |
| DOS gaussian fills | TikZ plot expressions for shallow and deep lobes | Matplotlib SVG backend emits shallow/deep lobes embedded in drawsvg | Matplotlib improved lobe smoothness, but SVG nesting needed cleanup once. |
| Trap-depth annotation | TikZ bracket and `$E_t` text | Bracketed arrow plus dvisvgm-rendered `$E_t \\sim 0.5\\text{--}1.0\\,\\mathrm{eV}$` | Math is path-rendered through LaTeX; placement/scale still needs manual render iteration. |
| Math labels | TikZ math labels | dvisvgm-rendered `g(E_t)` and `E_t` labels | Math glyph quality is strong; baseline/scale metadata is not automatic. |
| Bottom callout | Three-line explanatory text | Italic rounded callout | Readable and semantically aligned with reference. |

Known non-scored gaps:
- dvisvgm math snippets need explicit width placement rather than text-box-aware layout.
- DOS labels and bracket placement are visually tuned by render inspection.
- The output is a panel spike artifact, not an integrated full-figure layout.
