# Friction Log

## Initial Assumptions

- Python should handle the primary visual design layer.
- TikZ should remain useful for final LaTeX integration, not as the first creative surface.
- The hard part to validate here is not line art; it is restrained, publication-appropriate style richness.

## Observed Friction

- SVG defs are powerful but stringly typed when inserted as raw XML. A reusable engine should wrap gradients, filters, masks, clip paths, and patterns in typed helpers.
- Pseudo-3D is practical for paper schematics if kept semantic: shaded faces, fixed perspective, restrained shadows. It should not try to mimic full ray-traced rendering.
- Matplotlib nesting works well for plot/schematic fusion, but deterministic `svg.hashsalt`, metadata stripping, and id prefixing are mandatory.
- dvisvgm math remains the best path for LaTeX-quality equations inside Python-generated SVG.
- Visual layout still needs human or automated screenshot review. XML validity alone misses label crowding and low-level overlap defects.
- General chemistry rendering remains outside this experiment. Overview molecules can be hand-authored; exact structures need a dedicated chemistry renderer.

## Reuse Candidates

- `style_defs()` should become a style-token registry, not a raw string.
- `iso_box()` is a good seed for device-layer primitives.
- `nested_svg()` and `math_svg()` are already useful enough for promotion after packaging and tests.
- Texture primitives should be opt-in and journal-style constrained to avoid poster-like overstyling.
