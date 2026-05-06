# Fig1 Physics Sanity Contract v20

## Purpose

This contract defines the first executable basic academic/physics sanity layer for Fig1. It is not publication-grade theory validation, and it does not claim that the schematic quantitatively proves a material mechanism. Its job is narrower: catch clearly wrong ordering, sign, model-chain, and claim-boundary regressions before visual review.

The reference PNG remains layout/style evidence only, not scientific ground truth. The user-provided causal diagram remains semantic/narrative evidence only, not ground_truth.

## Hard Fail Now

`src/verify_fig1_physics_sanity.py` must fail on unambiguous basic regressions:

- Reference authority must not become `ground_truth`.
- LUMO/HOMO labels must stay bound to the correct band edges.
- LUMO must remain above HOMO in the drawn energy schematic.
- Trap positions must remain inside the normalized LUMO/HOMO bandgap.
- Deep traps must remain deeper than shallow traps.
- DOS and ISPD widths, heights, areas, sigma values, and sample counts must stay positive.
- Deep DOS width/area must dominate shallow DOS by the payload ratio.
- P-E hysteresis dimensions and sample counts must stay positive, with normalized remanence in `(0, 1)`.
- The power-law decay model must keep `slope < 0`, `I(t) ~ t^-n` notation, and extracted parameter `n`.
- The causal chain must remain `I(t) ~ t^-n -> n -> Debye exp(-t/tau) -> tau_d -> g(Et)`.
- Debye must remain a reference/bridge in the Fig1 interpretation chain, not a measured equality.
- `g(Et)` must remain a schematic trap-depth output, not an exact measured distribution claim.
- Like-charge repulsion semantics must keep trapped charge and electrode signs consistent with `ForceArrow.sign_condition`.
- The Maxwell attraction cue must remain secondary.

## Fail After Payload Clarification

The current `ForceArrow` payload does not say which object the force acts on. Strict vector physics for the probe panel is therefore deferred until the payload has target semantics such as `force_target`, `acted_on`, or an equivalent field.

Once clarified:

- If the target is the cantilever, a positive trapped charge next to a positive electrode on the right should have a leftward force.
- If the target is the electrode, the current rightward reaction-force cue can pass.
- If the arrow is an interaction cue rather than a vector force, the verifier should check it as an interaction cue, not as force on the cantilever.

Until then, `verify_fig1_physics_sanity.py` reports a warning rather than a hard failure for missing `force_target` semantics.

If a future payload adds `force_target`, that field must land in the same commit as the strict vector check for the allowed target values. The gate must not silently stop warning just because the field exists.

## Document Only

The following are outside this v20 gate:

- Quantitative trap-depth extraction validity.
- Real ISPD fitting quality.
- Material-specific proof of sulfur-polymer trap mechanisms.
- Publication-grade figure approval.
- Subjective readability and reference-fidelity judgment.

Human visual review remains required before publication-grade approval.
