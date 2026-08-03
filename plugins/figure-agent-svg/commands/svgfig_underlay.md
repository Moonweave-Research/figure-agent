---
description: Create locked vtracer coordinate-evidence underlay from a reference or draft image.
---

Create the underlay layer for an SVG-first figure.

**Usage**: `/svgfig_underlay <name>`

Run from `plugins/figure-agent-svg`.

Read `examples/<name>/spec.yaml.reference_image`, then run:

```
uv run python scripts/svg_underlay.py --from-spec examples/<name>
```

The output must remain locked coordinate evidence:

- `id="vtracer-underlay"`
- `data-role="coordinate-evidence"`
- `data-locked="true"`
- `data-final-source="false"`

Do not copy traced paths into final TikZ. Do not treat the underlay as the
semantic source. Author or revise `source/<name>.svg` manually from this
coordinate evidence.
