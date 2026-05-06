# Fig1 Probe Force Target Options v21

## Scope

This document freezes the Fig1 probe-panel force-target decision before the v21 implementation. The reference PNG remains layout/style evidence only, not ground_truth, and not a pixel-tracing target. This decision intentionally prioritizes basic academic/physics sanity over matching the reference arrow direction.

## Options

| Option | Physics Meaning | Reader Intuition | Visual Cost | Gate Value |
| --- | --- | --- | --- | --- |
| `force_target="cantilever"` | Coulomb force acting on the charged cantilever from the right-side positive electrode. | Highest: like charges repel away from each other. | High: red force arrow flips leftward and baseline hash changes. | Highest: vector direction can be strictly checked. |
| `force_target="electrode"` | Equal-and-opposite reaction force acting on the electrode. | Lower: the figure would need explicit copy to stop readers from reading the arrow as force on the cantilever. | Low: current rightward arrow could remain. | Medium: physically valid but visually easy to misread. |
| `force_target="interaction_cue"` | Non-vector cue for a repulsive interaction. | Ambiguous: avoids wrong vector semantics but weakens the panel. | Lowest: current arrow could remain. | Lowest: strict vector gate is mostly bypassed. |

## Decision

Decision: `force_target="cantilever"`.

Reason:

- The probe panel should show the force on the charged cantilever, not a reaction force on the electrode.
- For positive trapped charges next to a positive right-side electrode, the cantilever force points leftward, away from the electrode.
- This makes the schematic easier to read under undergraduate electromagnetics conventions.
- It gives the `physics-sanity` gate a strict vector target instead of downgrading the arrow into an ambiguous interaction cue.

Reference divergence acknowledged: the Fig1 red repulsion arrow flips from rightward reference-style cue to leftward physics-grade cantilever-force vector. This is intentional. The reference PNG remains layout/style evidence only; it does not override the semantic payload source of truth.

## Implementation Scope

v21 must land as one semantic contract migration:

- Add `ForceArrow.force_target` while preserving compatibility for non-Fig1 probes.
- Set the Fig1 probe arrow target to `cantilever`.
- Flip the Fig1 force arrow leftward.
- Update rendered copy and SVG metadata to say the force acts on the cantilever.
- Replace the old `reference_rightward_repulsion` verifier contract with `cantilever_leftward_repulsion`.
- Add geometry sanity checks for charge/electrode separation, force-arrow start proximity, and bend-state consistency.
- Update `verify_fig1_baseline_hash.py` to the new v21 SVG hash in the same commit.
- Do not modify origin, hero, electrical evidence, interpretation, typography hierarchy, component registry, or Fig2 scaffolds.

Human visual review remains required before publication-grade approval.
