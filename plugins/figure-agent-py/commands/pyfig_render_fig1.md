---
description: Render Fig1 from the Python semantic SVG scene.
---

Render the Python-first Fig1 artifacts.

**Usage**: `/pyfig_render_fig1`

Run from the plugin root:

```bash
python3 scripts/pyfig.py render-fig1
```

Outputs:
- `experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg`
- `experiments/python_svg_semantic_fig1/fig1_reference_semantic.png`
- `experiments/python_svg_semantic_fig1/reference_vs_fig1_reference_semantic.png`

Do not call the TikZ `/fig_compile` or `/pyfig_compile` surfaces for this
Python SVG workflow.
