# Python SVG Style Capability Stress Design

## Goal

Verify whether a Python-first SVG stack can express the visual styling layer needed for a Nature Communications-level scientific schematic: material texture, controlled gradients, masks, soft shadows, pseudo-3D geometry, plot integration, and math labels.

## Scope

This is an experiment, not a product engine. It creates one standalone stress figure and records whether each visual capability is practical enough to promote into a reusable Python SVG engine later.

The figure must demonstrate:

- SVG-native linear and radial gradients.
- SVG filters for soft shadows or glow-like depth cues.
- SVG masks, clip paths, or deterministic patterns for texture.
- Pseudo-3D/isometric scientific objects built from semantic primitives.
- Matplotlib plot integration through nested SVG.
- LaTeX math labels through the existing `pdflatex` + `dvisvgm` path.
- A raster preview generated from the final SVG.

## Non-Goals

- No automated SVG-to-TikZ conversion.
- No new dependency beyond the existing spike stack: `drawsvg`, `matplotlib`, `numpy`, `pdflatex`, `dvisvgm`, and `rsvg-convert`.
- No claim that this is a general chemistry renderer.
- No promotion into plugin commands in this pass.

## Output

Create `experiments/python_svg_style_capability/` with:

- `style_capability.svg`
- `style_capability.png`
- `src/style_capability.py`
- `src/stack/drawsvg_helpers.py`
- `src/stack/dvisvgm_math.py`
- `capability_matrix.md`
- `friction_log.md`
- `time_log.md`
- `feasibility_handback.md`

## Success Criteria

The experiment passes if:

- The SVG regenerates from the Python script with deterministic output.
- `rsvg-convert` renders a PNG preview without errors.
- The SVG XML parses.
- The output visibly exercises each target capability rather than merely listing it.
- Logs identify which capabilities are reusable, fragile, or unsuitable for paper figures.

## Interpretation Rule

If the result looks better than TikZ-first prototypes but requires excessive ad hoc drawing code, the conclusion is not "ship this script." The conclusion is "build a semantic Python SVG primitive layer and keep TikZ as optional final export/integration."
