---
name: figure-agent-py
description: Use for the Python-first Fig1 semantic SVG renderer in experiments/python_svg_semantic_fig1. Renders and verifies SVG/PNG from Python scene payloads and scaffold contracts; does not use TikZ .tex or lualatex.
---

# figure-agent-py

## Identity

`figure-agent-py` is the Python-first semantic SVG surface for Fig1. It wraps
`experiments/python_svg_semantic_fig1`, where the figure is represented as:

- typed Python scene payloads in `src/fig1_l1_scene.py`;
- scaffold/layout contracts in `visual_layout.yaml`;
- drawsvg composition in `src/render_fig1_l1.py`;
- verifier gates in `src/run_fig1_gates.py`;
- tracked SVG/PNG artifacts at the experiment root.

Do not route this workflow through `plugins/figure-agent/scripts/compile.sh`.
That is the separate TikZ quality-kernel plugin.

## Commands

```text
/pyfig_render_fig1    render fig1_reference_semantic.svg/.png and comparison PNG
/pyfig_verify_fig1    run semantic, scaffold, causal, physics, render-parity, and hash gates
/pyfig_status_fig1    report artifact state and gate status
```

## Scope

In scope:
- semantic SVG figure composition;
- schematic scientific plot glyphs used as explanatory evidence;
- Matplotlib as a geometry/schematic calculator, not a measured-data plotter;
- Fig1-specific render parity and visual judgment reports;
- physics sanity guardrails for sign/order/direction/model-chain mistakes.

Out of scope:
- real measured data plot production;
- fitting or analyzing raw measurements;
- converting arbitrary SVG into final source;
- TikZ `.tex` authoring and lualatex compilation.

If the user asks for measured data plots, redirect to matplotlib or
Graph_making_hub. If they ask for the current Fig1 schematic with schematic
P-E, current-decay, or ISPD glyphs, keep it in this Python SVG workflow.
