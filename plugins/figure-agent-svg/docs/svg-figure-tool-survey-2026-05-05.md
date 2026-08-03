# SVG Figure Tool Survey - 2026-05-05

## Purpose

This note records external systems worth learning from for the SVG-first
`figure-agent-svg` experiment. The target remains semantic, editable SVG as the
durable manuscript source. Traced SVG paths, raster crops, and generated model
output may provide evidence or draft structure, but they should not become the
final source of truth without semantic normalization.

## Candidate Summary

| Candidate | Best use for this project | Adopt now? |
| --- | --- | --- |
| VFIG | Scientific figure-to-SVG benchmarks, cleanliness metrics, structure-aware QA | Study and spike |
| AutoFigure-Edit | Product pipeline: draft image, segmentation, SVG template, browser editor, artifacts | Study, avoid heavy dependency as baseline |
| Penrose | Semantic DSL and constraint-based layout model | Borrow concepts first |
| Feynman | Agent loop that plans semantic diagrams and renders with Penrose | Watch; not a direct dependency yet |
| Vega-Lite / Vega | Data-driven chart primitives and static SVG export | Spike for plots |
| Observable Plot | Lightweight SVG chart marks and layered plot composition | Spike for plots |
| ELK.js | Coordinate/layout solver for node-link flow diagrams | Spike for flow primitives |
| OpenChemLib JS | Molecule SVG generation from chemical structures | Spike for molecule/polymer fragments |
| RDKit.js | Molecule SVG rendering, highlighting, structure tools | Spike as alternative molecule backend |
| svgdx | SVG-superset DSL ideas: relative positioning, fragments, loops | Borrow syntax ideas only |

## VFIG

Source:

- https://vfig-proj.github.io/
- https://github.com/RAIVNLab/VFig
- https://arxiv.org/abs/2603.24575
- https://huggingface.co/datasets/QijiaHe/VFIG-Data
- https://huggingface.co/XunmeiLiu/VFIG-4B

What it is:

VFIG is a 2026 scientific image-to-SVG system. It includes VFIG-Data, a dataset
of 66K image-SVG pairs focused on diagram-centric scientific figures, plus code
for SFT, RL, inference, benchmark evaluation, code cleanliness, and rule-based
evaluation.

What matters for us:

- It directly supports the boundary we already chose: VTracer can match pixels,
  but it performs badly on SVG cleanliness. That is exactly why vtracer should
  remain a locked underlay, not final source.
- Their evaluation axes map cleanly to our QA: presence, layout, connectivity,
  detail, render success, and SVG cleanliness.
- Their data examples are useful as a corpus for SVG idioms, but not as a final
  authoring standard.

Recommended spike:

1. Run VFIG inference on `examples/n3_trial_01_trap_depth/reference/codex_gen_v1.png`.
2. Compare VFIG output, our primitive output, and vtracer underlay on:
   - text preservation
   - energy-band geometry
   - arrow/connectivity accuracy
   - object count and path noise
   - editability
3. Port a small subset of the VFIG cleanliness idea into `svg_qa.py`.

Do not:

- Replace the semantic source layer with raw VFIG output.
- Treat high pixel similarity as paper-final quality.

## AutoFigure-Edit

Source:

- https://github.com/ResearAI/AutoFigure-Edit
- https://arxiv.org/abs/2603.06674

What it is:

AutoFigure-Edit is a text-to-editable-scientific-illustration system. The
documented pipeline is raw generation, SAM3 segmentation, SVG layout template,
and final assembled vector. It also includes an embedded SVG-Edit canvas and
stores intermediate artifacts such as icon crops and SVG templates.

What matters for us:

- The artifact model is strong: intermediate outputs remain visible and reusable
  instead of being hidden inside one generated file.
- The placeholder/template step is close to what our `source/*.template.svg`
  plus `primitives.yaml` path is trying to become.
- The editor loop is product-relevant: a researcher should be able to inspect,
  drag, edit, and reuse intermediate layers.

Risks:

- SAM3 is a heavy baseline dependency. The repo notes Python 3.12+, PyTorch
  2.7+, CUDA 12.6 for local GPU builds, and checkpoint access may require
  Hugging Face authentication.
- Some pipelines like this can drift toward raster/icon crops inside SVG. That
  is acceptable for draft composition, but not for our final semantic layer.

Recommended spike:

1. Inspect its output directory and SVG template format on a small example.
2. Borrow the artifact-drawer idea into our CLI/reporting vocabulary:
   `reference`, `underlay`, `segments`, `template`, `source`, `exports`.
3. Add a lightweight local segmentation/artifact placeholder step only if it
   improves authoring of real examples.

Do not:

- Make SAM3 mandatory for the MVP.
- Accept raster crops as final source unless explicitly marked as draft evidence.

## Penrose

Source:

- https://github.com/penrose/penrose
- https://penrose.cs.cmu.edu/docs/ref/domain/overview
- https://penrose.cs.cmu.edu/docs/ref/substance/overview
- https://penrose.cs.cmu.edu/docs/ref/style/overview
- https://penrose.cs.cmu.edu/docs/ref/using
- https://penrose.cs.cmu.edu/docs/ref/constraints

What it is:

Penrose separates a diagram into Domain, Substance, and Style. Domain declares
types and relations, Substance declares the objects and relationships, and Style
translates them into shapes, layout, and constraints. Its editor exports PNG,
SVG, SVG for LaTeX, and PDF. Its layout system is constraint/objective driven.

What matters for us:

- This is the strongest conceptual match for semantic scientific diagrams.
- Our `primitives.yaml` should move closer to this separation:
  domain concepts, figure instances, and style/layout rules should not be mixed
  in one free-form SVG prompt.
- Penrose is especially relevant for hard geometry: energy levels, graph-like
  diagrams, mathematical constructs, and domain-constrained layout.

Risks:

- It is not a drop-in paper figure generator. Each domain still needs a domain
  schema and style rules.
- Full adoption could slow the MVP if we try to rewrite the whole plugin around
  Penrose too early.

Recommended spike:

1. Implement one trap-depth energy-band diagram as a tiny Penrose-style schema:
   `EnergyLevel`, `Trap`, `Distribution`, `Transition`.
2. Compare its rendered SVG against our current `energy_band` primitive.
3. If it helps, evolve `primitives.yaml` toward separate `domain`, `objects`,
   and `style` blocks without adding Penrose as a dependency yet.

Do not:

- Rewrite the whole experiment around Penrose before proving it improves one
  hard figure.

## Feynman

Source:

- https://arxiv.org/abs/2603.12597

What it is:

Feynman is a diagramming-agent paper. It enumerates domain ideas, plans code,
translates those ideas into declarative programs, visually refines outputs, and
renders through Penrose. The paper says the dataset, benchmark, and full agent
pipeline are planned for release.

What matters for us:

- The loop shape is useful: idea, plan, render, visual feedback, refinement.
- It reinforces that final diagrams should come from semantic declarations, not
  from one-shot free-form SVG.

Risk:

- It is not yet a concrete repo dependency for our MVP.

Recommended spike:

- Borrow the workflow shape for a future `/svgfig_refine` command: generate
  semantic plan, render, run QA, ask for visual corrections, patch source.

## Vega-Lite / Vega

Source:

- https://vega.github.io/vega-lite/usage/embed.html
- https://vega.github.io/vega/docs/api/view/

What it is:

Vega-Lite is a grammar of graphics that compiles to Vega. Vega's View API can
render with an SVG renderer and can export static SVG or PNG.

What matters for us:

- This is the right class of tool for real plots, axes, legends, scales, and
  log transforms.
- It should replace hand-coded plot geometry inside primitives such as
  `loglog_plot`.

Risks:

- Generated SVG needs normalization into our semantic group contract.
- Vega is overkill for non-chart schematic objects.

Recommended spike:

1. Add an experimental `vega_loglog_plot` primitive that takes data and chart
   tokens.
2. Export SVG through Vega.
3. Wrap the result in a semantic group with a stable `data-object-id`.
4. Validate text, fonts, color tokens, and white-background export.

## Observable Plot

Source:

- https://observablehq.com/plot/features/plots
- https://observablehq.com/plot/features/marks

What it is:

Observable Plot is a JavaScript plotting library where charts are composed from
layered marks. By default, `Plot.plot` returns an SVG element, or an HTML
`figure` when title, subtitle, legend, or caption elements are present.

What matters for us:

- It is lighter than Vega-Lite for small plot fragments.
- It supports layered marks and data-space positioning.
- It can insert arbitrary SVG content as marks, which may help integrate
  custom scientific annotations.

Risks:

- It is JS-first, so a Python plugin would need a Node boundary.
- It is plot-focused, not a general scientific schematic renderer.

Recommended spike:

- Compare Observable Plot vs Vega-Lite for one `loglog_plot` primitive. Use
  the one that produces cleaner, more controllable SVG for our schema.

## ELK.js

Source:

- https://github.com/kieler/elkjs
- https://eclipse.dev/elk/blog/posts/2025/25-08-21-layered.html

What it is:

ELK.js is the JavaScript version of the Eclipse Layout Kernel. It computes
diagram element positions and edge routes. Its layered algorithm is useful for
directed diagrams with ports and follows phases such as cycle breaking, layer
assignment, crossing minimization, node placement, and edge routing.

What matters for us:

- This is a coordinate solver, not a renderer.
- It can help with flow panels, mechanism diagrams, z-pattern layouts, and
  multi-step process schematics.

Risks:

- It provides no styling or final SVG objects. We still need semantic SVG
  rendering after layout.

Recommended spike:

1. Add a `flow_graph` primitive with nodes, edges, ports, and direction.
2. Run ELK.js to compute coordinates.
3. Render the result using our own semantic SVG shapes and labels.

## OpenChemLib JS

Source:

- https://cheminfo.github.io/openchemlib-js/classes/Molecule.html
- https://cheminfo.github.io/openchemlib-js/interfaces/MoleculeToSVGOptions.html

What it is:

OpenChemLib JS can parse chemical structures and export molecule SVG via
`Molecule.toSVG(width, height, id, options)`. Options include crop behavior,
stroke width, font weight, and text-size scaling.

What matters for us:

- This is a better base for chemical structure fragments than hand-drawn
  polymer chains.
- It can be wrapped into a semantic molecule primitive while preserving the
  chemical source string.

Risks:

- The generated SVG may not match our journal token system without cleanup.
- Polymer repeat units and schematic molecular-origin panels often need
  domain-specific annotations beyond a raw molecule drawing.

Recommended spike:

1. Add a `molecule_svg` primitive that accepts SMILES or molfile text.
2. Generate SVG with OpenChemLib.
3. Wrap it with metadata: source string, backend, bbox, style token mapping.

## RDKit.js

Source:

- https://github.com/rdkit/rdkit-js
- https://www.rdkitjs.com/

What it is:

RDKit.js is the official JavaScript distribution of RDKit functionality through
WASM. It can draw molecules as SVG using `get_svg()` and supports SVG
highlighting via `get_svg_with_highlights()`.

What matters for us:

- RDKit is the stronger cheminformatics ecosystem if we need validation,
  descriptors, substructure search, or highlighting.
- It is useful for molecule panels where scientific correctness matters.

Risks:

- The GitHub README currently notes a maintenance transition for npm releases.
- WASM integration adds more runtime surface than OpenChemLib.

Recommended spike:

- Compare RDKit.js and OpenChemLib output on the same molecule/polymer-related
  structure. Keep the backend pluggable if both are useful.

## svgdx

Source:

- https://github.com/codedstructure/svgdx

What it is:

svgdx is a diagrams-as-code format that extends SVG. It supports relative
positioning, reusable fragments, variables, expressions, conditionals, and
loops. Any valid SVG is also valid input to a svgdx processor.

What matters for us:

- The relative positioning and fragment reuse ideas are directly relevant to
  our `source/*.template.svg` plus `primitives.yaml` direction.
- It is a useful design reference for a low-level SVG-native DSL.

Risks:

- The project says it is active pre-v1.0, with known issues and no stable input
  specification yet.

Recommended spike:

- Do not depend on svgdx yet. Borrow syntax ideas such as relative placement,
  local variables, loops, and reusable fragments into our own stable primitive
  schema where needed.

## Implementation Priority

1. Add a better QA rubric inspired by VFIG: presence, layout, connectivity,
   details, cleanliness.
2. Spike one data-driven plot backend: Vega-Lite or Observable Plot.
3. Spike one molecule backend: OpenChemLib first, RDKit.js second.
4. Spike one layout solver: ELK.js for flow diagrams.
5. Evolve `primitives.yaml` toward Penrose-like separation only after one
   hard example proves the value.

## Current Judgment

The current `figure-agent-svg` layer is directionally aligned with the best
available work, but it is not visually paper-final yet. The next improvement
should not be "more raw SVG prompting." It should be a semantic generation
stack:

1. underlay/reference evidence
2. semantic figure plan
3. domain-specific primitive generators
4. layout solvers where appropriate
5. SVG normalization into the schema
6. strict QA and visual review

