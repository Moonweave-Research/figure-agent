# Reference Fidelity Handback v19

## Scope

This pass follows `reference_fidelity_execution_prompt_v19.md` and `reference_fidelity_audit_v19.md`. It is a reference-fidelity polish pass over the existing Fig1 scaffold, focused only on the interpretation and electrical evidence panels.

## Implemented Boundary

- No new scaffold was created.
- No new semantic content was added.
- The reference PNG remains layout/style evidence only, not scientific ground truth.
- The user-provided causal diagram remains semantic/narrative evidence only.
- The renderer still uses drawsvg as the SVG compositor.
- The legacy dirty files `src/fig1_scene.py` and `src/semantic_scene.py` were not touched by this pass.
- Human visual review remains required before publication-grade approval.

## Visible Changes

- Interpretation causal chain now uses lightweight step capsules for stronger reference-like hierarchy while preserving existing causal roles.
- Interpretation decay plot, Debye bridge, tau_d cue, DOS output, and conclusion band were strengthened inside the existing panel.
- Electrical P-E and current-decay plot insets were reduced so the schematic plots read larger.
- Electrical axis, guide, curve, and label hierarchy were strengthened without adding real plot frames or dense numeric ticks.

## Hash Record

- previous hash: `b43c192481c799e895bd616b57fdd3731dfc58b3bf2d5fcee932d204592c207f`
- new hash: `55702be313ca70192560a569c8d45949b575e5bfa960252acd9e72f7294e230a`

## Next Direction

The next fidelity pass should either tune the center hero density or wait for user-provided partial references for the origin/probe style decisions. The main unresolved judgment is whether the origin panel should preserve the v17 causal relation strip or return closer to the reference's evidence-bullet idiom.
