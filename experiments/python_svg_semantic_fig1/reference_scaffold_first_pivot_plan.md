# Reference-Scaffold-First Pivot Plan

## Decision

The Python SVG semantic experiment should stop treating the semantic scene as a layout generator. The better path is reference-scaffold-first rendering: a good layout scaffold is selected or authored first, then semantic payloads, computed geometry, and verifier contracts are bound into that scaffold.

This keeps the strongest result from Fig1 v14: the reference-derived scaffold produced a better scientific schematic than synthetic semantic-first probes.

## What changed

`fig_probe_01` and `fig_probe_02` showed that the engine can render non-Fig1 scenes without importing Fig1 policy modules. They did not show that semantic-first composition produces publication-quality layouts.

The probes are therefore architecture evidence, not visual-quality evidence. Their visible awkwardness is useful: it marks the boundary between semantic correctness and composition quality.

## Target architecture

The renderer should be organized around four separate responsibilities:

- **Reference scaffold**: panel bounds, local boxes, object-to-slot mapping, flow anchors, and visual hierarchy.
- **Semantic payload scene**: scientific objects, payload values, computed parameters, and object relationships.
- **Drawsvg compositor**: deterministic SVG rendering that draws semantic objects inside scaffold slots.
- **Verification layers**: semantic correctness, scaffold containment, Fig-specific visual policy, and docs governance as separate checks.

The reference image, rough sketch, or human-authored scaffold remains layout/style evidence only. It is not ground truth and not a pixel-tracing target.

## Fig1 preservation gate

Fig1 v14 is the baseline. Any scaffold extraction or renderer refactor must preserve the current SVG byte hash unless the task is explicitly visual polish.

Current Fig1 SVG hash:

```text
8291c26721d83444d5232108ad692c1baafa9651652a04cdb08eb6b900bdf879
```

If that hash changes during a structure-only refactor, the refactor failed.

## Next implementation sequence

1. Keep `fig_probe_01` and `fig_probe_02` as architecture-only probes and label them as visual failure evidence.
2. Promote `visual_layout.yaml` / `reference_layout_spec_v1.md` into an explicit scaffold contract.
3. Split scaffold loading/binding helpers from `fig1_l1_scene.py` without changing Fig1 output.
4. Add a scaffold verifier that checks panel bounds, local box containment, object-to-slot binding, and flow-anchor presence.
5. Keep `verify_fig1_semantics.py`, `fig1_visual_policies.py`, and `check_fig1_docs_manifest.py` separate.
6. Require an approved scaffold before starting any second real figure.

## Non-goals

- Do not create another synthetic blank-layout probe.
- Do not make verifier count checks stand in for visual quality.
- Do not pixel-trace the reference PNG.
- Do not merge Fig1 visual policy caps back into the semantic verifier.
- Do not change Fig1 visual output in the first scaffold extraction pass.

## Success criteria

The pivot is successful when Fig1 can be rendered from an explicit scaffold contract with identical SVG bytes, and a future figure can start from an approved scaffold rather than from semantic-first layout synthesis.
