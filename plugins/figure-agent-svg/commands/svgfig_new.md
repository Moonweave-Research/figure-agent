---
description: Scaffold an SVG-first paper-figure folder.
---

Create `examples/<name>/` for the SVG-first workflow.

**Usage**: `/svgfig_new <name>`

Run from `plugins/figure-agent-svg`.

Create:

```
examples/<name>/
├── spec.yaml
├── briefing.md
├── reference/.gitkeep
├── underlay/.gitkeep
├── source/<name>.svg
├── build/.gitkeep
└── exports/.gitkeep
```

`spec.yaml` should include:

```yaml
name: <name>
reference_image:
required_labels: []
visual_diff:
  max_fraction:
```

`source/<name>.svg` should start as semantic SVG with:

- `<g id="semantic-layer">` for editable final objects.
- No visible vtracer paths in the semantic layer.
- Optional comments pointing to `underlay/<name>.underlay.svg`.

After scaffolding, save a reference/draft image under `reference/`, set
`spec.yaml.reference_image`, then run `/svgfig_underlay <name>`.
