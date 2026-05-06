# Fig1 DOS Reference Schematic Handback v9

## Goal

Replace the remaining generic-looking DOS lobes with a reusable reference-style DOS schematic grammar.

This pass focuses on the center hero DOS and the interpretation-card mini-DOS. It keeps the typed scene payloads as the source of truth and keeps `drawsvg` as the semantic SVG compositor.

## What Changed

- Added `draw_reference_dos_schematic()` in `src/engine/primitives.py`.
- Reused that primitive for:
  - hero `DOSLobes`,
  - interpretation-card `ISPDPlot`.
- Changed the hero DOS from a broad Gaussian-like plot shape into a reference-style schematic:
  - blue shallow cap,
  - red deep lobe,
  - dashed threshold guide,
  - DOS-owned `Et ~ 0.5-1.0 eV` double-arrow annotation,
  - bottom `g(Et)` axis label.
- Removed the old trap-stack-owned depth guide from the hero so the depth annotation belongs to the DOS grammar.
- Tuned the `DOSLobes` payload centers and dimensions to match the reference-style shallow/deep lobe placement while preserving deep-dominates-shallow semantics.

## Verifier Changes

`src/verify_fig1_semantics.py` now requires the v9 DOS grammar roles:

- `dos-axis-label`
- `dos-threshold`
- `dos-depth-guide`
- `dos-depth-label`
- `schematic-dos-threshold`
- `schematic-dos-depth-guide`
- `schematic-dos-depth-label`

It also checks that:

- the hero shallow lobe stays above the threshold guide,
- the hero deep lobe starts at or below the threshold guide,
- the hero deep lobe stays inside the local DOS area,
- hero DOS labels stay inside the local DOS area,
- the DOS depth guide sits to the right of the deep lobe.

The RED check before implementation failed on the existing artifact with:

```text
hero reference scaffold missing role dos-axis-label: 0 < 1
```

## Generated Artifacts

- `fig1_reference_semantic.svg`
- `fig1_reference_semantic.png`
- `reference_vs_fig1_reference_semantic.png`

## Remaining Gap

This is still not final figure art. The DOS grammar is now protected by semantic roles and morphology checks, but the next visual pass should tune:

- the exact red-lobe curvature,
- DOS label hierarchy,
- mini-DOS legibility in the interpretation card,
- whole-card text density against the reference scaffold.
