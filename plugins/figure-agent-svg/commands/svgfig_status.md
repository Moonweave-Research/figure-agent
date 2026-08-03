---
description: Report source/export freshness for an SVG-first figure.
---

Report the current state for an SVG-first figure.

**Usage**: `/svgfig_status <name>`

Run from `plugins/figure-agent-svg`:

```
uv run python scripts/svg_status.py <name>
```

States:

- `SOURCE_MISSING`: `source/<name>.svg` does not exist.
- `EXPORT_MISSING`: no PDF/PNG/TIFF exports exist yet.
- `EXPORT_PARTIAL`: only some of PDF/PNG/TIFF exist.
- `EXPORT_STALE`: source, spec, or underlay is newer than the exports.
- `EXPORT_FRESH`: PDF/PNG/TIFF are all present and fresh.
