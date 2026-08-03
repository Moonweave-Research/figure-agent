---
description: Run SVG-first QA checks for labels, white background, freshness, and visual diff.
---

Run QA on an exported SVG-first figure.

**Usage**: `/svgfig_qa <name>`

Use `spec.yaml.required_labels` as `--required-label` arguments. If
`spec.yaml.reference_image` and `visual_diff.max_fraction` are set, compare the
reference/draft image against `exports/<name>.png`. Use
`visual_diff.tolerance` or `--diff-tolerance` for anti-aliased draft images
whose background is not exactly white.

The source SVG is also checked against `docs/semantic-svg-schema-v1.md` and
`styles/svg_style_tokens.yaml`: required groups, required semantic objects,
palette, font family, text role, font size, stroke width, journal preset,
panel spacing, text overlap, object overlap, and margin/cropping.

If `--pdf` is passed, QA also runs `pdffonts` and `pdftotext` to check that PDF
fonts are embedded with Unicode maps and required labels remain extractable.

Command shape:

```
uv run python scripts/svg_qa.py examples/<name>/source/<name>.svg \
  --spec examples/<name>/spec.yaml \
  --pdf examples/<name>/exports/<name>.pdf \
  --png examples/<name>/exports/<name>.png \
  --reference-png examples/<name>/<reference_image> \
  --max-diff <max_fraction> \
  --diff-tolerance <pixel_tolerance> \
  --required-label "Label A" \
  --required-label "Label B"
```

Then check freshness:

```
uv run python scripts/svg_status.py <name>
```
