# SVG-First MVP

## Direction

The experiment exists because TikZ-only authoring was not reaching paper-final
visual quality quickly enough. The source of truth moves to editable semantic
SVG, while TikZ remains optional for generated math, plots, or primitive
snippets. SVG-native primitive fragments can also be generated from a small
domain DSL such as `primitives.yaml`.

## Pipeline

1. Save a reference or draft image under `examples/<name>/reference/`.
2. Run vtracer into `underlay/<name>.underlay.svg`.
3. Treat that underlay as locked coordinate evidence only.
4. Author `source/<name>.svg` with semantic SVG groups, labels, shapes, and
   style names, or author `source/<name>.template.svg` plus `primitives.yaml`
   and render the generated semantic fragments into `source/<name>.svg`.
5. Validate `source/<name>.svg` against `docs/semantic-svg-schema-v1.md` and
   `styles/svg_style_tokens.yaml`.
6. Export a cleaned SVG render path to PDF plus real 600 dpi PNG/TIFF rasters.
7. Run QA for required labels, required objects, text overlap, object overlap,
   margins/cropping, PDF font/text preservation, opaque white background,
   freshness, and optional visual difference against the reference/draft.

## Non-Goal

Do not use vtracer output as the final source. Do not route SVG paths into TikZ
as the production conversion path. Dense traced paths can help locate geometry,
but the manuscript source must remain editable and semantic.
