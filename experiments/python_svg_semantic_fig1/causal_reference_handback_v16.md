# Causal Reference Handback v16

## Scope

This pass binds the user-provided causal diagram into Fig1 semantics. It is not a visual polish pass and does not change the approved visual scaffold.

## Implemented Boundary

- The original aesthetic reference remains the visual scaffold authority.
- The new diagram is treated as a causal/semantic reference, not ground_truth and not a pixel-tracing target.
- `fig1_l1_scene.py` now records the causal chain and origin mechanisms in typed payload fields.
- `src/verify_fig1_causal_binding.py` checks the causal binding separately from scaffold, semantic, visual-policy, and docs-manifest checks.

## Bound Narrative

The v16 chain is:

```text
I(t) ~ t^-n -> n -> Debye exp(-t/tau) -> tau_d -> g(Et)
```

This connects experimental current decay to the interpretation layer, then to the trap-depth distribution. The molecular-origin panel binds S-rich segments to localized traps through chemical origin and physical origin cues. The hero panel remains the converged trap-depth picture.

## Output Policy

This pass is allowed to change SVG metadata if renderer payload tokens later expose the new causal fields. It does not intentionally move panels, redraw the scaffold, or claim publication-grade visual approval.

## Next Review

Human visual review should decide whether any of the v16 semantic binding should become visible text. Until that review, the causal diagram remains semantic/narrative evidence rather than a new layout target.
