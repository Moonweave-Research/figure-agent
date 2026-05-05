# Python SVG Semantic Fig1 Redraw Design

## Goal

Redraw the reference PNG `fig1_overview/reference/variant_aesthetic_ref.png` through a semantic Python scene layer instead of direct ad hoc drawing. The experiment checks whether a meaning-preserving scene can render close to the source figure while staying exportable to SVG/PNG.

## Source Reference

The local experiment copies the reference to:

`experiments/python_svg_semantic_fig1/reference/source_variant_aesthetic_ref.png`

This pass treats the source PNG as the visual layout target: center deep-trap hero card, four supporting cards around it, and gray flow arrows converging into the hero.

## Semantic Objects

The scene must define these objects explicitly:

- `polymer_origin`: S8 ring, heated sulfur chain, composition arrow, and sulfur-fraction bullets.
- `deep_trap_hero`: HOMO/LUMO band diagram, shallow/deep trap levels, DOS lobes, trap-depth annotation, and hero callout.
- `electrical_evidence`: P-E loop and current-decay plot.
- `trap_model`: power-law to Debye to tau-d to DOS flow plus supporting plots.
- `macroscopic_probe`: cantilever, trapped charges, electrode, repulsion arrow, Maxwell attraction cue, and bottom callout.
- `layout_flow`: gray arrows from support cards toward the hero.

Each object should be represented as data before rendering. The renderer consumes these objects and emits SVG primitives.

## Non-Goals

- No automatic image tracing.
- No pixel-level visual diff target.
- No plugin command integration.
- No TikZ export in this pass.

## Success Criteria

- The semantic scene contract passes before visual claims are made.
- The renderer produces deterministic `semantic_fig1.svg`.
- `rsvg-convert` renders `semantic_fig1.png`.
- The PNG visually follows the source reference closely enough for layout/meaning comparison.
- Logs identify whether semantic layering helped or hurt visual fidelity.
