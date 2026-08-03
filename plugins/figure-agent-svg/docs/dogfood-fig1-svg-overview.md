# Dogfood: Fig. 1 SVG Overview

Fixture: `examples/fig1_svg_overview`

## What This Exercises

This dogfood run exercises the intended SVG-first path:

1. Rough reference draft SVG under `reference/fig1_svg_overview_draft.svg`.
2. Draft PNG generated from that reference SVG.
3. Real vtracer underlay generated from `spec.yaml.reference_image` via
   `scripts/svg_underlay.py --from-spec`.
4. Semantic final source in `source/fig1_svg_overview.svg`.
5. Strict semantic contract validation.
6. PDF plus 600 dpi PNG/TIFF export.
7. QA for required labels, required semantic objects, style lock, bbox overlap,
   margins, PDF font/text preservation, white background, visual diff, and
   freshness.

## Verified Commands

```bash
rsvg-convert -b white -d 600 -p 600 -f png \
  -o examples/fig1_svg_overview/reference/fig1_svg_overview_draft.png \
  examples/fig1_svg_overview/reference/fig1_svg_overview_draft.svg

uv run --with vtracer python scripts/svg_underlay.py \
  --from-spec examples/fig1_svg_overview

uv run python scripts/svg_contract.py \
  examples/fig1_svg_overview/source/fig1_svg_overview.svg \
  --spec examples/fig1_svg_overview/spec.yaml

uv run python scripts/svg_export.py fig1_svg_overview

uv run python scripts/svg_qa.py \
  examples/fig1_svg_overview/source/fig1_svg_overview.svg \
  --spec examples/fig1_svg_overview/spec.yaml \
  --pdf examples/fig1_svg_overview/exports/fig1_svg_overview.pdf \
  --png examples/fig1_svg_overview/exports/fig1_svg_overview.png \
  --reference-png examples/fig1_svg_overview/reference/fig1_svg_overview_draft.png \
  --max-diff 0.60

uv run python scripts/svg_status.py fig1_svg_overview
```

Observed dogfood evidence:

- semantic SVG contract passed
- export produced PDF, PNG, and TIFF
- SVG QA passed
- status reported `EXPORT_FRESH`
- PNG/TIFF raster size: `4323 x 1938`
- TIFF DPI: `600 x 600`
- visual diff vs independent draft PNG: `0.206198`
- vtracer underlay size: about 204 KB

## Readiness Judgment

Current status: partially ready. See also
`docs/dogfood-fig1-charge-trap-overview.md` for the first scientific Fig. 1
dogfood pass.

The layer is now credible for controlled semantic SVG production experiments:
the source contract is explicit, exports are reproducible, and QA catches style,
label, object, layout, PDF text/font, background, visual-diff, and freshness
problems.

It is not yet safe to call the layer fully paper-final-ready without human visual
review on at least one real manuscript figure and without expanding beyond this
single dogfood example. The next release-readiness gate should be a real
manuscript figure pass with no generated reference copied from the final source
and with visual review by the author.
