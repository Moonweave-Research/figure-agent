# Fig1 Physics Sanity Gate Handback v20

## Scope

This pass implements the first independent `physics-sanity` gate for Fig1 after the v20 inventory. It converts unambiguous basic academic/physics checks into executable failures while keeping the unresolved probe vector issue as an explicit warning.

## Implemented Boundary

- No new scaffold was created.
- No new semantic content was added to the figure.
- The SVG renderer and visual output were not intentionally changed.
- The reference PNG remains layout/style evidence only, not scientific ground truth.
- The causal diagram remains semantic/narrative evidence only, not ground_truth.
- The legacy dirty files `src/fig1_scene.py` and `src/semantic_scene.py` were not touched by this pass.
- Human visual review remains required before publication-grade approval.

## Added Gate Surface

- `src/verify_fig1_physics_sanity.py` checks basic sign, ordering, model-chain, numeric-parameter, and claim-boundary invariants.
- `src/test_fig1_physics_sanity.py` mutates payloads to prove the gate rejects known bad states.
- `src/run_fig1_gates.py` now includes the independent `physics-sanity` gate.
- `physics_sanity_contract_v20.md` records hard-fail, deferred-fail, and document-only boundaries.

## Probe Force Target Status

`ForceArrow` still lacks `force_target` or equivalent acted-on semantics. The new gate reports that as a warning because strict vector physics would otherwise overclaim correctness or incorrectly fail the existing reference-bound visual cue.

The next strict probe pass should add target semantics first, then decide whether the visible rightward arrow is a reaction force on the electrode, an interaction cue, or an incorrect force-on-cantilever vector.

## Hash Record

- previous hash: `55702be313ca70192560a569c8d45949b575e5bfa960252acd9e72f7294e230a`
- new hash: unchanged, because this pass adds gates/docs/tests and does not intentionally modify the rendered SVG.

## Verification Boundary

The new physics-sanity gate prevents basic academic regressions. It does not validate quantitative trap-depth extraction, real ISPD fitting, or publication-grade scientific correctness.
