# Raw semantic SVG non-promotion decision

- `outcome`: `retain_experimental`
- `applies_to`: `raw_semantic_svg_pilot`
- `fixture`: `fig3_trap_schematic_slice3_semantic`
- `reviewer`: `choemun-yeong`
- `reviewed_at`: `2026-07-11T14:44:13+09:00`
- `review_input_hash`: `sha256:d5609aa5f3d30810a8966b27c5376c605f4757b09e9280370cf20cf0fe1cfde9`
- `publication_acceptance`: `not_claimed`

## Decision

The bound primitive SVG artifact is rejected as a production-quality rendering.
Its primitive geometry, visual density, and cross-panel illustration language
fall below the bound TikZ comparator.

This decision does not supply the still-pending scaffold verdict and therefore
does not close Slice 3. It also does not reject:

- semantic SVG as a QA and attribution surface;
- grammar-driven SVG backends that have not yet been tested; or
- TikZ production composition.

The next experiment must test a renderer-neutral scientific illustration
grammar through both TikZ and SVG. Machine gates remain insufficient for
publication acceptance.
