# AGENTS.md - figure-agent-py

Codex entry point for the Python-first Fig1 semantic SVG plugin.

Authoritative workflow: `skills/figure-agent-py/SKILL.md`.

This plugin wraps `experiments/python_svg_semantic_fig1`. It does not use the
TikZ/lualatex `plugins/figure-agent` compile chain and does not consume
`examples/<name>/<name>.tex` as input.

Active surface:
- `/pyfig_render_fig1` renders `fig1_reference_semantic.svg`,
  `fig1_reference_semantic.png`, and `reference_vs_fig1_reference_semantic.png`.
- `/pyfig_verify_fig1` runs the Fig1 semantic/scaffold/causal/physics/render
  parity gates.
- `/pyfig_status_fig1` reports current artifact presence, hashes, and gate
  status.

Boundary: measured data-plot production remains outside this plugin. Schematic
scientific plot glyphs used as semantic evidence inside Fig1 are in scope.
