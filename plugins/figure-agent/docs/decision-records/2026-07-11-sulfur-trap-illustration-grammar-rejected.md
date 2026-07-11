# Sulfur-trap illustration grammar rejection

- `outcome`: `rejected`
- `applies_to`: `sulfur_trap_domain.v1`
- `fixture`: `fig3_trap_schematic_slice4_illustration_grammar`
- `reviewer`: `최문영`
- `reviewed_at`: `2026-07-11`
- `review_input_hash`: `sha256:ae1201ef8cd1c9acd38ba443f0b92b25b41ac9289e5b403b6cf9cee860023f26`
- `publication_acceptance`: `not_claimed`

## Decision

Reject the current sulfur-trap illustration grammar implementation as a
production rendering path. The bound three-way review found:

- grammar SVG is visually worse than the historical raw SVG comparator;
- grammar TikZ and grammar SVG correctly share one neutral scene and the
  surrounding TikZ illustration language; and
- neither grammar artifact reaches the production-quality bar.

The paired backend experiment therefore succeeds as an architecture and
verification result but fails as an illustration-quality result. The dominant
gap is the grammar's sparse, schematic composition: it does not yet reproduce
the density, organic structure, or material coupling of the accepted TikZ
benchmark.

This decision preserves the neutral scene compiler, TikZ/SVG backends,
deterministic manifests, equal-boundary comparison packet, and clean
reproduction machinery as experimental infrastructure. It does not promote a
production default and does not claim publication acceptance. The next
implementation should enrich illustration primitives and composition rules
rather than add another rendering backend.

## Automation boundary

Figure Agent should automatically generate the paired artifacts, normalized
crops, hashes, toolchain and reproduction receipts, detector findings, stale
binding checks, and a provisional comparison summary. A named human must still
accept or reject the bound visual packet. Machine gates and provisional
recommendations cannot sign the publication verdict.
