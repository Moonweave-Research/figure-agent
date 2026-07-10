# figure-agent-py

Python-first semantic SVG plugin for the Fig1 scientific schematic.

> **Product and execution source of truth:**
> [`../../FIGURE_AGENT_SPEC.md`](../../FIGURE_AGENT_SPEC.md). This README
> describes the current Python plugin implementation only.

The implementation source is `experiments/python_svg_semantic_fig1`: Python scene
payloads, scaffold layout contracts, drawsvg composition, Matplotlib-backed
schematic glyphs, and verifier scripts. The plugin commands are thin wrappers
around that experiment so Claude/Codex can use the Python renderer directly.

This plugin does not compile TikZ and does not require `<name>.tex`.

## Commands

- `/pyfig_render_fig1` - render tracked Fig1 SVG/PNG/comparison artifacts.
- `/pyfig_verify_fig1` - run all Fig1 gates in `src/run_fig1_gates.py`.
- `/pyfig_status_fig1` - summarize artifact presence, hashes, and gate result.

## Scope

In scope: semantic scientific schematic rendering, reference-scaffold layout,
schematic P-E / I(t) / ISPD glyphs as visual evidence, physics sanity guards,
render parity, and visual judgment reporting.

Out of scope: producing real measured data plots, fitting data, replacing the
Graph_making_hub/matplotlib data workflow, or pixel-tracing a reference PNG.
