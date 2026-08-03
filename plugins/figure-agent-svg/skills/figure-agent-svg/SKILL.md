---
name: figure-agent-svg
description: Use for the SVG-first paper-figure experiment where the durable source is semantic SVG, vtracer is locked coordinate evidence, and export/QA produce PDF/PNG/TIFF artifacts.
---

# figure-agent-svg

Use this plugin when the task is about the SVG-first experiment under
`plugins/figure-agent-svg`.

Core rule: vtracer output is never final source. It is a locked underlay and
coordinate-evidence layer. The durable editable source is
`examples/<name>/source/<name>.svg`.

Workflow:

1. `/svgfig_new <name>` scaffolds the per-figure folder.
2. `/svgfig_underlay <name>` creates `underlay/<name>.underlay.svg` from a saved
   reference or draft image.
3. Author semantic SVG in `source/<name>.svg`.
4. `/svgfig_export <name>` strips locked underlays, adds a white background, and
   exports PDF/PNG/TIFF.
5. `/svgfig_qa <name>` checks labels, white background, and optional visual diff.
6. `/svgfig_status <name>` reports source/export freshness.
