# Python SVG Full-Figure Stress Test — Design

**Date**: 2026-05-06  
**Branch**: `experiment/python-svg-full-fig-stress`  
**Base**: `experiment/python-svg-spike` at `c49c957`  
**Output root**: `experiments/python_svg_full_fig_stress/`

## 1. Goal

Test whether the locked Python SVG stack can build a complex, multi-panel, Nature Communications-style scientific overview figure, using the existing `fig1_overview` reference as the stress case. The output is evidence, not promotion: render artifacts, friction, defects, timing, and a feasibility handback.

## 2. Input Truth

Use these local inputs from the parent figure-agent workspace:

- Reference image: `plugins/figure-agent/examples/fig1_overview/reference/variant_aesthetic_ref.png`
- Briefing: `plugins/figure-agent/examples/fig1_overview/briefing.md`
- Existing TikZ control: `plugins/figure-agent/examples/fig1_overview/fig1_overview.tex`
- Prior Python spike: `experiments/python_svg_spike/`

The full stress test follows the visual reference image more than the current strip-layout briefing where they conflict, because the question is whether Python can reproduce a complex visual paper figure.

## 3. Stack

Allowed:

- `drawsvg` for schematic primitives, layout, labels, arrows, hatching, and composition
- `matplotlib` SVG backend for plot-like subregions
- `dvisvgm` via `pdflatex` for math typography
- Python standard library

Forbidden:

- `svgwrite`
- `rdkit`
- `chemfig`
- `pgfplots`
- `[Graph_making_hub]` imports
- `/fig_compile` integration
- Style Lock integration

## 4. Scope

Build one full composition:

- TL: sulfur polymer origin, including S8 ring, chain, composition arrow, bullets
- Center: deep charge trapping hero, reusing/improving the prior center panel pattern
- TR: electrical evidence with P-E response and current decay
- BL: interpretation model with flow chain, current decay, DOS, callout
- BR: macroscopic probe, reusing/improving the prior BR panel pattern
- Layout glue: cards, full canvas, subtle inter-panel arrows

This test may use hand-drawn chemistry-like SVG for TL, but must record whether that generalizes. A need for a real chemistry renderer is recorded as friction rather than hidden.

## 5. Stress Tags

Use these tags in commits and friction logs:

- `SETUP.contract`
- `LAYOUT.canvas_cards`
- `TL.s8_ring`
- `TL.polymer_chain`
- `TL.composition_swatch`
- `TL.bullets`
- `CENTER.energy_bands`
- `CENTER.dos_math`
- `CENTER.callout`
- `TR.pe_loop`
- `TR.current_decay`
- `BL.model_flow`
- `BL.current_decay_plot`
- `BL.dos_plot`
- `BL.callout`
- `BR.probe_mechanics`
- `BR.force_cues`
- `LAYOUT.inter_panel_arrows`
- `EXPORT.render_checks`
- `HANDOFF.logs`

## 6. Deliverables

Create:

- `experiments/python_svg_full_fig_stress/full_figure.svg`
- `experiments/python_svg_full_fig_stress/full_figure.png`
- `experiments/python_svg_full_fig_stress/src/full_figure.py`
- `experiments/python_svg_full_fig_stress/src/stack/drawsvg_helpers.py`
- `experiments/python_svg_full_fig_stress/src/stack/dvisvgm_math.py`
- `experiments/python_svg_full_fig_stress/friction_log.md`
- `experiments/python_svg_full_fig_stress/defect_log.md`
- `experiments/python_svg_full_fig_stress/time_log.md`
- `experiments/python_svg_full_fig_stress/comparison_full.md`
- `experiments/python_svg_full_fig_stress/feasibility_handback.md`

## 7. Evaluation Rules

Codex must not self-score G2 or assign a reference-match percentage. The handback may state evidence-backed feasibility only:

- what rendered
- what did not render
- what required manual tuning
- what is likely P0/P1/P2 friction
- which regions looked stack-native
- which regions exposed stack limits

## 8. Verification

Before handback:

- Regenerate `full_figure.svg` from `src/full_figure.py`
- Parse SVG XML
- Render PNG with `rsvg-convert`
- Inspect rendered PNG with vision load
- Check forbidden stack tokens in `src/`
- Check all stress tags appear in the logs
- Check deliverables contain no G2 numeric scoring
- Confirm git status is clean
