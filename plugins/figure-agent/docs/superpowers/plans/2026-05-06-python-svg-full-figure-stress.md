# Python SVG Full-Figure Stress Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full multi-panel Python SVG stress figure and hand back evidence on whether the locked stack scales to a complex paper overview.

**Architecture:** Keep the stress test isolated under `experiments/python_svg_full_fig_stress/`. Reuse the prior spike helpers by copying them into the new output root, then compose all panels from one `full_figure.py` so full-canvas layout can be tuned directly.

**Tech Stack:** Python, drawsvg, matplotlib SVG backend, pdflatex+dvisvgm, rsvg-convert.

---

## File Structure

- Create `experiments/python_svg_full_fig_stress/src/full_figure.py`: full-canvas drawing entrypoint.
- Create `experiments/python_svg_full_fig_stress/src/stack/drawsvg_helpers.py`: copied and extended primitive helpers.
- Create `experiments/python_svg_full_fig_stress/src/stack/dvisvgm_math.py`: copied math SVG helper.
- Create `experiments/python_svg_full_fig_stress/full_figure.svg`: generated SVG artifact.
- Create `experiments/python_svg_full_fig_stress/full_figure.png`: rendered PNG artifact.
- Create `experiments/python_svg_full_fig_stress/friction_log.md`: one row per stress tag.
- Create `experiments/python_svg_full_fig_stress/defect_log.md`: observed visual defects after render inspection.
- Create `experiments/python_svg_full_fig_stress/time_log.md`: per-region implementation timing.
- Create `experiments/python_svg_full_fig_stress/comparison_full.md`: qualitative comparison to reference and TikZ control.
- Create `experiments/python_svg_full_fig_stress/feasibility_handback.md`: evidence-only feasibility conclusion without G2 numbers.

---

## Task 1: Setup Contract

**Files:**
- Create: `experiments/python_svg_full_fig_stress/src/stack/drawsvg_helpers.py`
- Create: `experiments/python_svg_full_fig_stress/src/stack/dvisvgm_math.py`
- Create: `experiments/python_svg_full_fig_stress/src/full_figure.py`

- [ ] Copy helper code from `experiments/python_svg_spike/src/stack/`.
- [ ] Add a minimal `full_figure.py` that emits a white 1780 x 1000 SVG.
- [ ] Run `uv run --with drawsvg --with matplotlib python experiments/python_svg_full_fig_stress/src/full_figure.py`.
- [ ] Parse `full_figure.svg` with `xml.etree.ElementTree`.
- [ ] Commit with `SETUP.contract` in the subject.

## Task 2: Layout Canvas Cards

**Files:**
- Modify: `experiments/python_svg_full_fig_stress/src/full_figure.py`
- Modify generated: `experiments/python_svg_full_fig_stress/full_figure.svg`

- [ ] Add rounded cards for TL, center, TR, BL, and BR using the reference-like spatial layout.
- [ ] Render and inspect that the cards sit inside the 1780 x 1000 canvas.
- [ ] Commit with `LAYOUT.canvas_cards` in the subject.

## Task 3: TL Sulfur Polymer Origin

**Files:**
- Modify: `experiments/python_svg_full_fig_stress/src/full_figure.py`
- Modify generated: `experiments/python_svg_full_fig_stress/full_figure.svg`

- [ ] Add `TL.s8_ring`: icon/title and hand-drawn S8 ring.
- [ ] Commit with `TL.s8_ring` in the subject.
- [ ] Add `TL.polymer_chain`: heat arrow and sulfur chain schematic.
- [ ] Commit with `TL.polymer_chain` in the subject.
- [ ] Add `TL.composition_swatch`: S60 to S85 color bar and direction arrow.
- [ ] Commit with `TL.composition_swatch` in the subject.
- [ ] Add `TL.bullets`: three checkmarked interpretation bullets.
- [ ] Commit with `TL.bullets` in the subject.

## Task 4: Center Hero

**Files:**
- Modify: `experiments/python_svg_full_fig_stress/src/full_figure.py`
- Modify generated: `experiments/python_svg_full_fig_stress/full_figure.svg`

- [ ] Add `CENTER.energy_bands`: title, LUMO/HOMO, shallow/deep states, energy axis.
- [ ] Commit with `CENTER.energy_bands` in the subject.
- [ ] Add `CENTER.dos_math`: matplotlib DOS lobes and dvisvgm math labels.
- [ ] Commit with `CENTER.dos_math` in the subject.
- [ ] Add `CENTER.callout`: bottom deep-state callout.
- [ ] Commit with `CENTER.callout` in the subject.

## Task 5: TR Electrical Evidence

**Files:**
- Modify: `experiments/python_svg_full_fig_stress/src/full_figure.py`
- Modify generated: `experiments/python_svg_full_fig_stress/full_figure.svg`

- [ ] Add `TR.pe_loop`: P-E mini plot with axes and loop.
- [ ] Commit with `TR.pe_loop` in the subject.
- [ ] Add `TR.current_decay`: log-log current decay mini plot and label.
- [ ] Commit with `TR.current_decay` in the subject.

## Task 6: BL Interpretation

**Files:**
- Modify: `experiments/python_svg_full_fig_stress/src/full_figure.py`
- Modify generated: `experiments/python_svg_full_fig_stress/full_figure.svg`

- [ ] Add `BL.model_flow`: I(t) to Debye to tau to g(E_t) flow chain.
- [ ] Commit with `BL.model_flow` in the subject.
- [ ] Add `BL.current_decay_plot`: mini power-law plot.
- [ ] Commit with `BL.current_decay_plot` in the subject.
- [ ] Add `BL.dos_plot`: mini DOS plot with shallow/deep lobes.
- [ ] Commit with `BL.dos_plot` in the subject.
- [ ] Add `BL.callout`: bottom interpretation callout.
- [ ] Commit with `BL.callout` in the subject.

## Task 7: BR Probe

**Files:**
- Modify: `experiments/python_svg_full_fig_stress/src/full_figure.py`
- Modify generated: `experiments/python_svg_full_fig_stress/full_figure.svg`

- [ ] Add `BR.probe_mechanics`: probe icon, clamp, curved cantilever, electrode.
- [ ] Commit with `BR.probe_mechanics` in the subject.
- [ ] Add `BR.force_cues`: trapped charges, dashed fields, repulsion/Maxwell arrows, callout.
- [ ] Commit with `BR.force_cues` in the subject.

## Task 8: Layout Arrows and Export

**Files:**
- Modify: `experiments/python_svg_full_fig_stress/src/full_figure.py`
- Create generated: `experiments/python_svg_full_fig_stress/full_figure.png`

- [ ] Add `LAYOUT.inter_panel_arrows`: subtle grey arrows toward the center card.
- [ ] Commit with `LAYOUT.inter_panel_arrows` in the subject.
- [ ] Render `full_figure.png` with `rsvg-convert`.
- [ ] Commit with `EXPORT.render_checks` in the subject.

## Task 9: Logs and Handback

**Files:**
- Create: `experiments/python_svg_full_fig_stress/friction_log.md`
- Create: `experiments/python_svg_full_fig_stress/defect_log.md`
- Create: `experiments/python_svg_full_fig_stress/time_log.md`
- Create: `experiments/python_svg_full_fig_stress/comparison_full.md`
- Create: `experiments/python_svg_full_fig_stress/feasibility_handback.md`

- [ ] Write one friction row for every stress tag in the design.
- [ ] Write visual defects from rendered PNG inspection.
- [ ] Write timing and comparison notes.
- [ ] Write evidence-only feasibility handback with no G2 numeric score.
- [ ] Commit with `HANDOFF.logs` in the subject.

## Task 10: Final Audit

**Files:**
- Verify all files under `experiments/python_svg_full_fig_stress/`

- [ ] Regenerate SVG.
- [ ] Parse SVG XML.
- [ ] Render PNG.
- [ ] Inspect PNG.
- [ ] Grep forbidden stack tokens in `src/`.
- [ ] Check all stress tags in logs and commits.
- [ ] Check no G2 numeric score in deliverables.
- [ ] Check git status is clean.
