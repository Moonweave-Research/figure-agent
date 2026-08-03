---
description: Export semantic SVG to PDF, PNG, and TIFF.
---

Export `examples/<name>/source/<name>.svg`.

**Usage**: `/svgfig_export <name>`

Run from `plugins/figure-agent-svg`:

```
uv run python scripts/svg_export.py <name>
```

The export path:

1. Validates `source/<name>.svg` against the semantic contract and style tokens.
2. Refuses export if required groups, labels, objects, style lock, bbox,
   overlap, margin, or journal preset checks fail.
3. Removes locked coordinate-evidence groups such as `id="vtracer-underlay"`.
4. Adds an explicit white SVG background.
5. Writes `build/<name>.export.svg`.
6. Uses `rsvg-convert` for vector PDF.
7. Uses `rsvg-convert -d 600 -p 600` for the PNG raster.
8. Uses Pillow to save the 600 dpi PNG raster as 600 dpi TIFF.

Outputs:

```
examples/<name>/exports/<name>.pdf
examples/<name>/exports/<name>.png
examples/<name>/exports/<name>.tif
```
