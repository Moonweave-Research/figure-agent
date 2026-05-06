# Fig1 v19 Reference Fidelity Execution Prompt

## Role

You are refining the Python SVG semantic Fig1 experiment after v18 causal readability polish. Your job is to raise reference-fidelity discipline before any broad reinterpretation.

## Objective

Perform a panel-by-panel reference fidelity audit, then propose the smallest next renderer changes that would make the current semantic SVG output more capable of reaching reference-level completion.

## Current Baseline

- Worktree: `/Users/choemun-yeong/workspace/ResearchOS/[figure-agent-py]`
- Branch: `experiment/python-svg-semantic-fig1`
- Current committed v18 baseline: `499afa5 SEMANTIC.fig1: polish v18 causal readability`
- Current v18 SVG hash: `b43c192481c799e895bd616b57fdd3731dfc58b3bf2d5fcee932d204592c207f`
- Reference PNG: `experiments/python_svg_semantic_fig1/reference/source_variant_aesthetic_ref.png`
- Current output: `experiments/python_svg_semantic_fig1/fig1_reference_semantic.png`
- Comparison output: `experiments/python_svg_semantic_fig1/reference_vs_fig1_reference_semantic.png`

## Hard Boundaries

- Do not create a new scaffold.
- Do not add new semantic content.
- Do not pixel-trace the reference image.
- Do not treat the reference PNG as scientific ground truth.
- Do not introduce a component reference registry yet.
- Do not mutate or stage the legacy dirty files:
  - `experiments/python_svg_semantic_fig1/src/fig1_scene.py`
  - `experiments/python_svg_semantic_fig1/src/semantic_scene.py`
- Do not claim publication-grade completion. Human visual review remains required.

## Execution Sequence

1. Confirm worktree status and v18 baseline.
2. Inspect the full reference PNG, current PNG, and comparison PNG.
3. Produce per-panel visual comparisons for:
   - sulfur polymer origin
   - electrical evidence
   - center hero
   - interpretation
   - macroscopic probe
4. Score each panel against the reference on four axes:
   - layout fidelity
   - visual density and hierarchy
   - scientific schematic credibility
   - text/cue readability
5. Classify each gap as one of:
   - renderer polish: coordinates, font scale, stroke, spacing, local composition
   - scaffold limitation: local boxes or panel proportions block the desired result
   - semantic limitation: payload lacks information needed for a faithful schematic
   - reinterpretation candidate: better handled by a new partial reference from the user
6. Choose at most two panels for the next implementation pass.
7. Do not implement until the chosen panel targets and intended changes are explicit.

## Expected Output

Write a v19 audit document with:

- one-paragraph overall judgment
- panel-by-panel gap table
- ranked next actions
- explicit "do now" versus "needs partial reference" split
- verification plan for any later renderer changes

## Success Criteria

The audit is successful if it separates:

- what can be improved immediately by the current drawsvg renderer,
- what requires a panel-level reference or user taste decision,
- what should stay out of scope until Fig2 proves the reusable component boundary.
