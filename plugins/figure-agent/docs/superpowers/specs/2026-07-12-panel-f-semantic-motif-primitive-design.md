# Panel F Semantic Motif Primitive Design

**Status:** Approved implementation evidence; not product authority

## Problem

The reviewed Panel F pilot improved a floating cantilever apparatus through
repeated human correction, but the final TikZ geometry remains embedded in one
fixture. Repeating that source block by hand would preserve neither the learned
semantic constraints nor the finish corrections.

The earlier sulfur-trap illustration grammar is not a production precedent. It
proved deterministic lowering but produced visually weaker artifacts. This
slice therefore extracts one narrow, already-reviewed motif instead of reviving
a complete drawing grammar.

## Design

Create one reusable TikZ motif for a mechanically fixed, electrically floating
cantilever facing a driven electrode. The motif owns only its local apparatus
geometry and semantic anchors. The surrounding LLM-authored figure continues to
own panel composition, typography, narrative labels, and force explanation.

The motif contract declares:

- a neutral mechanical fixed boundary and cantilever attachment;
- a floating sample/cantilever;
- a driven electrode connected to a voltage source;
- a grounded source return that does not imply sample grounding;
- trapped-charge markers owned by the cantilever; and
- distinct mechanical-attachment and electrical-lead style roles.

The first integration uses the existing Fig1 art-direction fixture and the
reviewed Panel F pilot. Both consumers must call the same motif source. No
historical build artifact is treated as regenerated authority, and no machine
gate may claim publication acceptance.

## Boundaries

- Do not add a full illustration grammar or another renderer backend.
- Do not add fixture names or absolute panel coordinates to Python product
  logic.
- Do not move whole-panel composition into the motif.
- Do not modify `scripts/quality/quality_search.py` or
  `scripts/quality/panel_block_edits.yaml`.
- Keep the existing Panel F source selector and semantic-legibility contract.
- Treat successful reuse across these two Fig1 fixtures as transfer evidence,
  not cross-family generalization.

## Verification

Tests first require that both fixtures consume the shared motif, the motif
contains stable semantic anchors and no forbidden sample-ground connection, and
the existing semantic-legibility and source-selector gates still pass. Compile
both fixtures, run strict mode, compare focused Panel F crops, and leave the
human publication verdict separate.

