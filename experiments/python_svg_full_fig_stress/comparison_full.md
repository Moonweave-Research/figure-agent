# Python SVG Full-Figure Stress Comparison

Reference: `plugins/figure-agent/examples/fig1_overview/reference/variant_aesthetic_ref.png`  
TikZ control: `plugins/figure-agent/examples/fig1_overview/fig1_overview.tex`  
Python stress output: `experiments/python_svg_full_fig_stress/full_figure.svg`

This comparison is qualitative only. It does not include G2 scoring.

| region | Python result | comparison note |
| --- | --- | --- |
| TL sulfur polymer | Full card includes icon, title, S8 ring, heat arrow, polymer chain, swatch, bullets. | Python can reproduce the visual story. Chemistry is hand-drawn and does not generalize to arbitrary structures. |
| Center hero | Energy bands, shallow/deep states, DOS lobes, dvisvgm math, callout. | Strongest Python area. Matplotlib lobes and dvisvgm labels are smoother than hand-tuned TikZ, but placement is manual. |
| TR electrical evidence | P-E loop and current decay mini plot. | Schematic evidence is readable. Plot grammar is still hand-authored, not a reusable chart system. |
| BL interpretation | Flow chain, current decay, DOS mini plot, callout. | The panel is dense but rendered. Math boxes needed scale tuning. |
| BR macroscopic probe | Probe icon, clamp, curved beam, charges, electrode, fields, force arrows, callout. | Reused prior spike patterns successfully at full-figure scale. |
| Layout glue | Five cards plus inter-panel arrows. | Layout is coherent and close to the reference topology, but final balance needs human visual polish. |

Evidence-backed comparison:
- The locked stack can produce a complex multi-panel SVG that renders to PNG.
- The drawing-heavy and plot-heavy regions are feasible with direct coordinate control.
- Math typography is good through dvisvgm, but auto-fit/baseline/layout metadata is missing.
- Chemistry is the largest unresolved stack gap.
