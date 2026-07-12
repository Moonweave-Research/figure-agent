# TikZ-First, SVG-Assisted Figure Agent Design

**Status:** Approved direction design; pending canonical-document integration

## Decision

Figure Agent keeps TikZ/TeX as its primary publication rendering path. SVG is
retained as a derived inspection, editing, interchange, and diagnostic surface.
Python remains a supporting control-plane implementation language; it is not a
general scientific-illustration renderer and must not accumulate fixture-local
SVG coordinates as product logic.

This decision follows the bounded Panel F comparison. The SVG pilot proved
editable semantic grouping, deterministic replay, and contract validation, but
it did not approach the approved TikZ motif's geometry, composition, or finish.
Machine-valid output therefore remains insufficient evidence for backend
promotion.

## 1. TikZ is the primary production backend

TikZ owns the default path for manuscript figures when it provides the best
available composition, typography, mathematical geometry, and reproducibility.
New figure work should reuse reviewed TikZ motifs and snippets before inventing
a second renderer.

Renderer choice remains technically local, but SVG cannot become a default
publication backend merely because it is editable or passes semantic gates. A
non-TikZ backend requires evidence on at least two materially different figure
families and a named human verdict that it is not materially worse.

## 2. SVG is an assisted surface

SVG has four supported roles:

1. browser and editor preview;
2. stable semantic-object highlighting and diagnostic overlays;
3. bounded manual interchange with Illustrator, Inkscape, or equivalent tools;
4. a derived export of an approved TikZ/PDF artifact when downstream vector
   editing is required.

SVG is not an independent visual authority. A derived SVG binds to its TikZ or
PDF source hash, conversion command and tool versions, output hash, and a
semantic sidecar. Conversion must not claim exact source attribution when the
mapping is ambiguous. It records `exact`, `ambiguous`, or `unbound` instead.

The existing Panel F SVG pilot remains negative evidence. It must not be
silently polished into a production backend or imported as a general drawing
grammar.

## 3. Figure Agent develops the LLM's weak limbs

Product development concentrates on recurring failures that free LLM authoring
misses:

- missing, invented, or scientifically false objects and relations;
- incorrect electrical or mechanical topology;
- label, arrow, contour, and object collisions;
- malformed contours, dangling endpoints, and incomplete outlines;
- wrong panel orientation, hierarchy, density, or relative scale;
- inconsistent typography, strokes, curvature, colors, and repetition;
- stale or unbound review evidence;
- uncontrolled repair that damages protected meaning.

The canonical observation ladder remains whole figure, panel, semantic
object/relation, and zoomed finish region. Findings must be localized to a
declared object or relation and a stable source selector before automatic repair
is allowed. Otherwise they remain review-only.

TikZ motif reuse, detector improvements, bounded repair, provenance, and human
review are product capabilities. Repeated hand-adjustment of one SVG is figure
production evidence, not a Figure Agent capability.

## 4. Approved TikZ-to-SVG export path

The export path begins with an approved, reproducible TikZ source and its
compiled PDF. It performs deterministic local conversion to SVG, rejects
network or unhashed assets, records the conversion receipt, and produces a
semantic sidecar without changing the approved TikZ source.

The minimum packet is:

- authoritative TikZ source path and SHA-256;
- compiled PDF SHA-256;
- conversion tool, version, arguments, and environment boundary;
- derived SVG SHA-256;
- source-to-SVG attribution state for each declared semantic object;
- optional diagnostic overlays and crops;
- explicit `publication_acceptance: not_claimed` for the converted artifact
  until a named human checks it.

The first implementation slice is deliberately narrow: export the approved
Panel F motif, prove deterministic clean reproduction, attach semantic IDs or
an honest sidecar mapping, and verify that conversion does not alter visual
geometry beyond a declared raster tolerance. It does not render a new SVG from
Python and does not replace the TikZ original.

## Python boundary

Python remains useful and necessary for:

- schema and contract validation;
- invoking deterministic TeX, PDF, SVG, and raster tools;
- hashing and provenance receipts;
- geometry extraction and coordinate normalization;
- collision, topology, typography, and finish detectors;
- multi-scale crop and overlay generation;
- finding attribution, repair planning, rollback, and review packets;
- regression and clean-environment reproduction tests.

Python must not own:

- fixture-specific handcrafted SVG coordinates;
- a replacement illustration grammar for open-ended composition;
- publication-quality acceptance;
- invented scientific truth;
- silent conversion of ambiguous geometry into exact semantic attribution.

## Acceptance boundaries

This direction is integrated only when canonical tests prove that:

1. TikZ is named the default publication path;
2. SVG is named a derived assisted surface rather than a co-equal default;
3. Python's renderer boundary is explicit;
4. the approved TikZ-to-SVG export packet is hash-bound and deterministic;
5. the original TikZ source remains unchanged;
6. machine gates do not claim publication acceptance; and
7. the Panel F direct-SVG pilot remains recorded as non-promoted evidence.

