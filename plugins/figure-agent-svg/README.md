# figure-agent-svg

Experimental SVG-first split from `figure-agent`.

This plugin treats the final editable source as semantic SVG objects, not
TikZ and not traced bitmap paths. A reference or draft image can be vectorized
with vtracer, but that output is a locked underlay and coordinate-evidence
layer only. Export preparation strips locked vtracer underlays before producing
manuscript artifacts.

## MVP Workflow

```
/svgfig_new <name>       scaffold examples/<name>/
/svgfig_underlay <name>  reference/draft image -> underlay/<name>.underlay.svg
                         (locked vtracer coordinate evidence, not final source)
[human/LLM authors]      source/<name>.svg with semantic groups, text, shapes
/svgfig_primitives <name>
                         optional primitives.yaml -> generated semantic fragments
/svgfig_export <name>    strict semantic SVG validation -> PDF / 600 dpi PNG/TIFF
/svgfig_qa <name>        schema, style, labels, objects, overlap, margins,
                         PDF fonts/text, white background, optional visual diff
/svgfig_status <name>    source/export freshness state
```

TikZ is optional as a generator for math, plots, or primitive snippets, but any
generated output must be normalized into the semantic SVG source layer. For
SVG-native figure snippets, `primitives.yaml` can describe reusable scientific
fragments such as `loglog_plot`, `polymer_chain`, and `energy_band`; those are
rendered into editable semantic SVG before export. Do not convert vtracer SVG
paths into TikZ as the final source.

Some primitives can delegate hard geometry to SVG-native engines before being
wrapped back into the semantic source contract:

- `vega_loglog_plot`: Vega-Lite/Vega renders data-space log-log plot SVG.
- `openchemlib_molecule`: OpenChemLib renders molecule SVG from SMILES.

These generated SVG subtrees are treated as opaque inside a semantic wrapper
with stable `data-object-id` and `data-bbox`; labels and QA-critical objects
remain in the editable semantic layer.

## Semantic Contract

`source/<name>.svg` must follow `docs/semantic-svg-schema-v1.md`:

- root marker: `data-figure-agent-svg="semantic-v1"`
- root journal preset: `data-journal-preset="nature-single"` or another token
- stable dimensions in `width`, `height`, and `viewBox`
- required groups: `semantic-layer`, `panels`, `objects`, `labels`
- semantic objects with `data-object-id` and `data-bbox`
- text with `data-text-role`, `data-bbox`, `font-family`, `font-size`, and
  palette-locked fill

Style tokens live in `styles/svg_style_tokens.yaml`. Export refuses invalid
semantic SVG before running converters.

## Per-Figure Folder

```
examples/<name>/
├── spec.yaml
├── briefing.md
├── reference/
├── underlay/<name>.underlay.svg
├── primitives.yaml                  # optional generated-fragment DSL
├── source/<name>.template.svg        # optional template with fragment markers
├── source/<name>.svg
├── build/<name>.export.svg
└── exports/<name>.pdf|png|tif
```

## Verification

Run from `plugins/figure-agent-svg`:

```
npm install
uv run pytest
uv run ruff check .
```
