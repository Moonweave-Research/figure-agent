# Semantic Fig1 Redraw Handback

## Verdict

The semantic-layer approach works for this figure family.

The experiment redraws the source PNG as a Python-generated SVG/PNG while preserving explicit semantic objects for the material origin, deep-trap hero, electrical evidence, trap-model interpretation, macroscopic probe, and layout flow. This is materially different from tracing: the renderer consumes meaning-bearing objects and emits SVG primitives.

## Outputs

- `reference/source_variant_aesthetic_ref.png`: copied source reference.
- `semantic_fig1.svg`: Python-generated vector redraw.
- `semantic_fig1.png`: rendered preview.
- `reference_vs_semantic_fig1.png`: source-vs-redraw side-by-side comparison.
- `src/semantic_scene.py`: dataclass scene model.
- `src/fig1_scene.py`: Fig 1 semantic scene.
- `src/render_semantic_fig1.py`: semantic renderer.
- `src/verify_semantic_scene.py`: semantic contract verifier.

## What Worked

- The semantic contract catches missing scene objects before rendering.
- The renderer can follow the source composition while keeping semantic IDs in the SVG.
- Deep-trap dominance, support-card evidence, trap-model flow, and probe repulsion direction are encoded in scene assertions.
- The same scene model could later emit alternate renderers, including a cleaner SVG renderer, PDF path, or TikZ backend.

## Remaining Gap

- The redraw is not pixel-identical and should not be treated as final paper art.
- Chemistry detail is schematic, not chemical-renderer accurate.
- Plot ticks and icon details need a small polish pass if this becomes manuscript-facing.
- A real engine should split visual primitives from domain primitives more cleanly than this one-file renderer.

## Architecture Implication

The correct next layer is not SVG-to-TikZ conversion. It is semantic scene preservation.

Once the scene is defined as objects such as `DeepTrapHero`, `TrapDOS`, `SulfurPolymerOrigin`, `EvidencePanel`, and `MacroscopicProbe`, a TikZ backend can redraw the same meaning without reverse-engineering SVG paths. Python remains the best authoring and preview surface; TikZ becomes an optional emitter.
