# Fig. 1 SVG-first Overview

## Topic

Show the SVG-first paper-figure production layer as a three-panel overview:
reference/draft evidence, semantic source authoring, and manuscript export QA.

## Vocabulary

reference image, draft image, locked vtracer underlay, coordinate evidence,
semantic SVG source, manuscript export, QA gate, freshness.

## Composition

Three horizontal panels in a `nature-double` width:

- A: reference/draft image is converted to a locked underlay as coordinate
  evidence.
- B: the human/LLM authors semantic SVG objects and labels over that evidence.
- C: export and QA produce PDF, PNG, and TIFF with checks.

## Invariants

Vtracer output must never be presented as final source. The final durable source
is semantic SVG. The export layer strips coordinate evidence and uses a white
background.
