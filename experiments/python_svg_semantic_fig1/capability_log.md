# Semantic Fig1 Redraw Capability Log

## Source

- Reference PNG: `reference/source_variant_aesthetic_ref.png`
- Mode: semantic redraw, not image tracing.

## Required Semantic Objects

- `polymer_origin`
- `deep_trap_hero`
- `electrical_evidence`
- `trap_model`
- `macroscopic_probe`
- `layout_flow`

## Verification

| UTC time | Check | Result |
| --- | --- | --- |
| 2026-05-05T15:47:38Z | `python experiments/python_svg_semantic_fig1/src/verify_semantic_scene.py` | Pass: semantic scene contract passed |
| 2026-05-05T15:47:38Z | `python -m xml.etree.ElementTree experiments/python_svg_semantic_fig1/semantic_fig1.svg` | Pass |
| 2026-05-05T15:47:38Z | `rsvg-convert -w 1595 -h 986 ... -o /tmp/semantic_fig1_check.png` | Pass |
| 2026-05-05T15:47:38Z | SHA-256 before/after regeneration | Pass: deterministic SVG `cdef3e4aaca0362ef75e0a28019550f0b4702d279172e728780dc9d86444acd8` |

## Visual Notes

- The redraw preserves the five-card composition, central hero, support-card flow arrows, and the major scientific story.
- The semantic renderer is clearer than a path soup: the SVG includes markers for `polymer_origin`, `deep_trap_hero`, `electrical_evidence`, `trap_model`, `macroscopic_probe`, and `layout_flow`.
- Fine visual fidelity is still below the source PNG in chemistry ornamentation, plot tick polish, and icon detail.
- The semantic layer did not prevent good visual styling; it made the renderer easier to inspect and retarget.
