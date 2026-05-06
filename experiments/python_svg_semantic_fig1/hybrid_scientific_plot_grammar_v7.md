# Fig1 Hybrid Scientific Plot Grammar v7

## Purpose

This document records the next direction after v6 computed scientific geometry.

The v6 renderer is now more semantic-driven internally, but the visible figure still looks under-polished. The current weak point is not semantic modeling. The weak point is scientific visual grammar: axes, ticks, labels, graph density, band/DOS alignment, and collision-aware annotation placement.

The next pass should therefore keep the semantic scene model, but actively borrow mature Python scientific plotting and geometry tools where they solve real problems.

## Current Baseline

Worktree:

- `/Users/choemun-yeong/workspace/ResearchOS/[figure-agent-py]`

Branch:

- `experiment/python-svg-semantic-fig1`

Current experiment root:

- `experiments/python_svg_semantic_fig1/`

Current generated outputs:

- `experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg`
- `experiments/python_svg_semantic_fig1/fig1_reference_semantic.png`
- `experiments/python_svg_semantic_fig1/reference_vs_fig1_reference_semantic.png`

Current semantic renderer files:

- `src/engine/scene.py`
- `src/engine/style.py`
- `src/engine/primitives.py`
- `src/engine/domain_primitives.py`
- `src/engine/scientific_geometry.py`
- `src/engine/visual_constraints.py`
- `src/fig1_l1_scene.py`
- `src/render_fig1_l1.py`
- `src/verify_fig1_semantics.py`

Authoritative semantic inputs remain read-only:

- `/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent/examples/fig1_overview/briefing.md`
- `/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent/examples/fig1_overview/spec.yaml`

Reference PNG:

- `experiments/python_svg_semantic_fig1/reference/source_variant_aesthetic_ref.png`

The reference PNG is the authoritative visual layout target for this pilot, but it is not a pixel-tracing ground truth.

## Architectural Decision

Use a hybrid Python-first renderer:

- Keep `drawsvg` as the figure compositor and semantic SVG writer.
- Keep scene objects and typed payloads as the source of truth.
- Use Matplotlib as a scientific plot grammar engine for axes, ticks, formatters, and optional microplot SVG generation.
- Use geometry/parser libraries to strengthen verification and layout analysis.

Do not introduce TikZ in v7. A later TikZ backend should consume the same scene model, not replace the current renderer mid-experiment.

## Candidate Libraries

Required for v7:

- `drawsvg`: current SVG writer/compositor.
- `matplotlib`: scientific axes, tick locators, tick formatters, path primitives, optional microplot SVG output.
- `numpy`: numerical sampling and curve calculations.
- `shapely`: robust geometry checks for containment, overlap, clearance, and buffered arrows/curves.
- `svgelements`: robust SVG element/path/transform parsing for verifier logic.

Optional in v7, likely useful in v8:

- `svgpathtools`: path length, Bezier bbox, intersections, and curve analysis.
- `svgutils`: composing externally generated SVG microplots back into the master SVG if direct drawsvg translation becomes too costly.
- `scipy`: curve smoothing/fitting only if a real scientific model requires it.

Recommended command shape:

```bash
uv run \
  --with drawsvg \
  --with matplotlib \
  --with numpy \
  --with shapely \
  --with svgelements \
  --with svgpathtools \
  python experiments/python_svg_semantic_fig1/src/render_fig1_l1.py
```

## v7 Goal

Build a reusable scientific visual grammar layer under:

- `experiments/python_svg_semantic_fig1/src/engine/scientific_plots.py`

The layer should make the figure look more like a real publication schematic while preserving semantic-driven rendering.

It should support:

- Scientific axes with major/minor ticks.
- Log-log axes for power-law current decay.
- Publication-style tick labels.
- Plot label placement inside local plot bounds.
- P-E hysteresis rendering with better scale and smoothness.
- DOS/ISPD plot rendering with stronger axis grammar.
- Optional Matplotlib microplot SVG generation for plot-heavy subpanels.
- Conversion or embedding path that preserves semantic group IDs around the plot object.

## Preferred Implementation Strategy

Start conservative, then compare against a more aggressive option.

### Option A: Matplotlib as Grammar Calculator

Use Matplotlib tick locators, formatters, and path/scale logic to compute:

- tick positions
- tick labels
- major/minor tick hierarchy
- axis bounds
- curve points

Then draw the result with existing `drawsvg` primitives.

Pros:

- Keeps semantic IDs clean.
- Keeps SVG deterministic and readable.
- Avoids nested Matplotlib SVG defs/id collisions.
- Easier to verify payload-derived geometry.

Cons:

- Requires implementing drawsvg axis rendering ourselves.
- Some typography polish still needs manual tuning.

### Option B: Matplotlib Microplot SVG Embedding

Generate a small Matplotlib SVG for P-E, I(t), or ISPD, sanitize it, and insert it inside the corresponding semantic group.

Pros:

- Fastest path to real scientific-plot appearance.
- Gets ticks, labels, spines, clipping, and typography from Matplotlib.

Cons:

- Must handle SVG defs/id collisions.
- Matplotlib may convert text to paths unless rcParams are fixed.
- Harder to keep semantic IDs inside every primitive.
- Deterministic SVG hash needs extra care.

### Recommendation

Implement Option A first for `PowerLawDecayPlot`, because the current I(t) plot visibly lacks scientific graph grammar. Add Option B as an isolated experiment only if Option A still looks too hand-drawn.

## Files To Create Or Modify

Create:

- `src/engine/scientific_plots.py`
- `scientific_plot_grammar_handback_v7.md`

Modify:

- `src/engine/domain_primitives.py`
- `src/engine/primitives.py`
- `src/render_fig1_l1.py`
- `src/verify_fig1_semantics.py`
- `README.md`

Possibly modify:

- `src/engine/visual_constraints.py`
- `src/fig1_l1_scene.py`

Do not mutate:

- `/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent/examples/fig1_overview/briefing.md`
- `/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent/examples/fig1_overview/spec.yaml`

## Semantic Requirements

Preserve existing object kinds and add no new broad figure-agent command surface.

Existing semantic object payloads must remain the driver:

- `PowerLawDecayPlot.slope`, log range, sample count, and model drive I(t).
- `PEHysteresisPlot.remanence`, loop dimensions, and model drive P-E.
- `DOSLobes` and `ISPDPlot` payloads drive DOS shapes.
- `BandDiagram` and `TrapLevelSet` remain the energy reference for hero geometry.

Renderer output must still include:

- `data-semantic-id`
- `data-semantic-kind`
- `data-payload-geometry`
- payload-derived geometry that changes when payload changes

## Verification Requirements

Fresh verification must include:

```bash
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/render_fig1_l1.py
python experiments/python_svg_semantic_fig1/src/verify_fig1_semantics.py
python -m xml.etree.ElementTree experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg
rsvg-convert -w 1595 -h 986 experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg -o /tmp/fig1_reference_semantic_check.png
```

Also regenerate twice and confirm deterministic SVG hash.

The verifier should add checks for:

- Minimum major tick count for P-E and I(t) plots.
- Minor tick presence for log-log current decay if using the drawsvg axis path.
- Tick labels staying inside the plot/card local box.
- Curve labels staying inside local plot bounds.
- No curve/label/card overflow from semantic bbox checks.
- Payload mutation changes visible plot geometry after stripping semantic metadata.
- No forbidden force-balance, actuator, or bidirectional-actuation framing terms.

## Visual Acceptance

Manual preview should show clear improvement over v6:

- I(t) should look like a real log-log scientific plot, not a diagonal placeholder.
- P-E loop should have cleaner axis hierarchy and a smoother loop.
- ISPD/DOS plot should have clearer axis and label alignment.
- Hero band/DOS/trap module should look more unified.
- Overall plot typography should look less handwritten and more publication-like.

This v7 pass does not need to make the entire figure final. It should prove that the hybrid scientific plot grammar direction improves the visible figure without weakening semantic verification.

## Non-Goals

- No TikZ backend yet.
- No SVG-to-TikZ conversion.
- No plugin command integration.
- No new slash command.
- No automatic image tracing.
- No generic chemistry renderer.
- No mutation of the main `figure-agent` example folders.
- No replacing the semantic scene model with a reference-copy path soup.

## New Session Slash-Goal Prompt

Use this prompt to continue in a fresh session:

```text
/goal
Goal: Build python_svg_semantic_engine_v7_hybrid_scientific_plot_grammar for Fig1.

Worktree:
- /Users/choemun-yeong/workspace/ResearchOS/[figure-agent-py]
- Branch: experiment/python-svg-semantic-fig1

Context:
- Continue the existing Fig1 Python SVG semantic renderer experiment under:
  experiments/python_svg_semantic_fig1/
- Current v6 state already has:
  - typed scene model
  - renderer dispatch by semantic object kind
  - reference-based visual layout from visual_layout.yaml
  - computed geometry for DOS, P-E hysteresis, and power-law decay
  - verifier checks for object kinds, trap/DOS dominance, energy ordering, visual constraints, semantic SVG IDs, and payload mutation changing visible geometry
- Current v6 handback:
  experiments/python_svg_semantic_fig1/computed_geometry_handback_v6.md
- Current v7 planning doc:
  experiments/python_svg_semantic_fig1/hybrid_scientific_plot_grammar_v7.md

Authoritative semantic files, read-only:
- /Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent/examples/fig1_overview/briefing.md
- /Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent/examples/fig1_overview/spec.yaml

Reference visual target:
- experiments/python_svg_semantic_fig1/reference/source_variant_aesthetic_ref.png
- Treat as authoritative visual layout/style target for this pilot.
- Do not pixel-trace it.
- Do not mark it as ground_truth.

Objective:
Build v7 Hybrid Scientific Plot Grammar.
Keep drawsvg as the semantic SVG compositor, but actively use Matplotlib as a scientific plot grammar engine for axes, ticks, labels, and plot-style calculations. Use Shapely/svgelements/svgpathtools to strengthen verification where useful.

Recommended dependency command shape:
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/render_fig1_l1.py

Required architecture:
- Create:
  experiments/python_svg_semantic_fig1/src/engine/scientific_plots.py
- Keep existing semantic scene/payload model as source of truth.
- Renderer must still dispatch by semantic object kind.
- Renderer must still consume typed payloads.
- Changing plot payloads must change visible SVG geometry, not only semantic metadata.
- Preserve semantic SVG IDs and payload-derived geometry markers.

Implementation focus:
1. Add a reusable scientific plot grammar layer.
2. Implement a better PowerLawDecayPlot first:
   - log-log axis grammar
   - major and minor ticks
   - publication-style tick labels
   - slope guide and label containment
   - curve generated from payload slope/log-range
3. Improve PEHysteresisPlot next:
   - cleaner axes
   - smoother loop
   - better scale/label placement
4. Improve ISPD/DOS axis grammar if time allows.
5. Keep card layout/reference composition stable unless a small local adjustment is required for visual correctness.

Preferred approach:
- Start with Matplotlib as a grammar calculator:
  use Matplotlib ticker/formatter/path logic to compute tick positions, labels, and curve points, then draw with drawsvg.
- Only prototype Matplotlib microplot SVG embedding if the drawsvg translation still looks too hand-drawn.
- If embedding Matplotlib SVG, sanitize IDs/defs and keep it wrapped inside the semantic object group.

Verifier updates required:
- Required plot model tokens still exist.
- Minimum major tick count for P-E and I(t).
- Minor ticks for log-log decay if using drawsvg axis rendering.
- Tick labels stay inside local plot/card bounds.
- Curve labels stay inside plot bounds.
- Semantic bbox/overflow checks still pass.
- Payload mutation for trap, DOS, P-E, and decay changes visible geometry after stripping data-payload-geometry.
- No force-balance panel, actuator framing, or bidirectional-actuation framing.

Visual acceptance:
- Manual preview should look visibly better than v6.
- I(t) should read as a real scientific log-log plot, not a placeholder diagonal line.
- P-E should look smoother and more publication-like.
- Hero DOS/band/trap module should remain semantically correct and visually more unified.
- Column/card composition should still follow the reference layout.

Generate/update:
- experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg
- experiments/python_svg_semantic_fig1/fig1_reference_semantic.png
- experiments/python_svg_semantic_fig1/reference_vs_fig1_reference_semantic.png
- experiments/python_svg_semantic_fig1/scientific_plot_grammar_handback_v7.md
- Update experiments/python_svg_semantic_fig1/README.md

Verification commands:
Run fresh:
- uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/render_fig1_l1.py
- python experiments/python_svg_semantic_fig1/src/verify_fig1_semantics.py
- python -m xml.etree.ElementTree experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg
- rsvg-convert -w 1595 -h 986 experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg -o /tmp/fig1_reference_semantic_check.png
- regenerate and confirm SVG hash is deterministic
- preview experiments/python_svg_semantic_fig1/fig1_reference_semantic.png
- git status --short --branch

Non-goals:
- No TikZ backend in this pass.
- No SVG-to-TikZ conversion.
- No plugin command integration.
- No new slash command.
- No automatic image tracing.
- No generic chemistry renderer.
- No mutation of the main figure-agent example folders.
- No abandoning the semantic scene model for hard-coded reference-copy path soup.
```
