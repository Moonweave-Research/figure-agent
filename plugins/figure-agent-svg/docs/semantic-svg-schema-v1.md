# Semantic SVG Schema v1

The final durable source for `figure-agent-svg` is
`examples/<name>/source/<name>.svg`. The vtracer underlay is coordinate evidence
only and is not final source.

Required root contract:

```xml
<svg
  data-figure-agent-svg="semantic-v1"
  data-journal-preset="nature-single"
  width="89mm"
  height="54mm"
  viewBox="0 0 890 540">
```

Required layer groups:

```xml
<g id="semantic-layer">
  <g id="panels">...</g>
  <g id="objects">...</g>
  <g id="labels">...</g>
</g>
```

Each panel declares `data-role="panel"` and `data-bbox="x y width height"`.
Each semantic object declares `data-object-id="..."` and `data-bbox="x y width
height"`. Each label is a `<text>` element with `data-text-role`, `data-bbox`,
`font-family`, `font-size`, and palette-locked `fill`.

Generated SVG from domain engines can be embedded as an opaque subtree only
inside a semantic wrapper. The wrapper still needs a stable `data-object-id`
and `data-bbox`; the raw engine output is marked `data-external-svg="true"` so
the schema validator does not require every internal path or atom label to use
the figure-agent text/object contract.

TikZ fragments follow the same rule as Vega-Lite and other generator-backed
fragments: TikZ may compute coordinates and emit an SVG subtree, but that
subtree is opaque generator output inside `data-external-svg="true"` and is not
promoted to durable semantic source.

Example:

```xml
<text data-text-role="label" data-bbox="520 330 145 18"
  x="520" y="344" font-family="Arial" font-size="14" fill="#111827">
  Trap depth
</text>
```

Locked vtracer underlay files live under `underlay/<name>.underlay.svg`.
They may carry:

```xml
<g id="vtracer-underlay" data-role="coordinate-evidence"
  data-locked="true" data-final-source="false">
```

That vtracer underlay is not final source and must not be copied into
`source/<name>.svg`. Export code strips coordinate-evidence groups as a safety
guard, but strict QA reports them as source-contract violations.

Style tokens live in `styles/svg_style_tokens.yaml` and define the allowed
journal presets, palette, font families, text roles, stroke widths, panel gap,
and content margin.
