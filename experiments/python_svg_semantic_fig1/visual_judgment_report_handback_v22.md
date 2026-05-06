# Fig1 Visual Judgment Report Handback v22

## Scope

This pass adds a report-only visual judgment layer for Fig1. It is not a renderer polish pass, not a new scaffold, and not a strict visual-quality gate.

## Implemented Boundary

- `src/report_fig1_visual_judgment.py` generates `fig1_visual_judgment_report.md` and `fig1_visual_judgment_report.json`.
- `src/test_fig1_visual_judgment_report.py` checks the report contract and confirms that the script is not added to `src/run_fig1_gates.py`.
- The report reuses SVG bbox extraction for semantic object bounds and enriches visible text records with role tags from invisible SVG role markers.
- No origin, hero, electrical evidence, interpretation, or probe layout changes were made.
- No absolute min-font-size verifier was added.
- No component registry was introduced.
- No Fig2 scaffold work was started.
- The reference PNG remains layout/style evidence only, not ground truth.
- The causal diagram remains semantic/narrative evidence only.
- Human visual review remains required before publication-grade approval.

## Report Categories

The v22 report exposes these report-only categories:

- Panel Density
- Text / Text Near-Collision
- Text / Shape Conflict
- Visual Hierarchy
- Reading Order
- Reference Divergence
- Human Review Prompts

Each category uses cautious language such as possible issue, candidate risk, evidence, and inspect. These are human-review prompts, not automatic failures.

## Reference Divergence Note

The v21 probe force decision remains intentional: `force_target=cantilever` with `arrow_direction=cantilever_leftward_repulsion`. This divergence from the rightward reference-style cue is preserved for physics sanity, while the reference PNG stays layout/style evidence only.

## Output Interpretation

`fig1_visual_judgment_report.md` is the human-facing review surface. `fig1_visual_judgment_report.json` is the structured sidecar for future agents. The JSON includes panel bounds, semantic object bboxes, visible text bboxes, role tags, font sizes, panel density estimates, near-collision candidates, hierarchy notes, reading-order evidence, reference-divergence notes, and human review prompts.

The report helps the next agent and human reviewer inspect visual risks. It does not claim publication-grade approval and does not replace human visual review.
