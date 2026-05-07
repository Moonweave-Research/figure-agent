# Fig1 Origin Payload Visibility Handback v25

## Scope

This pass is a narrow visual polish pass for the sulfur polymer origin panel. It closes a semantic-to-visual payload visibility gap without changing the scaffold, adding new semantic content, or claiming publication-grade approval.

## Implemented Change

- `src/render_fig1_l1.py` now renders `payload.heat_label` as the reaction-arrow label instead of the literal `Delta`.
- `src/render_fig1_l1.py` now renders `payload.chain_label` below the sulfur chain instead of the literal `Sx`.
- `src/test_fig1_origin_payload_visibility.py` checks that `Heat 160 C` and `-Sx- chain` from the `sulfur_polymer_origin` payload are visible in `svg_text_for_scene(build_scene())`.
- `fig1_reference_semantic.svg`, `fig1_reference_semantic.png`, `reference_vs_fig1_reference_semantic.png`, and `fig1_visual_judgment_report.md` were regenerated from the current renderer.

## Boundary

- No new scaffold.
- No new semantic content.
- No new strict aesthetic gate.
- No absolute min-font-size verifier.
- No pixel tracing of the reference image.
- Human visual review remains required before publication-grade approval.

## Hash Update

- previous hash: `0ceca15c136d21cb73676dcd91fb9a50aec54e41e05cd2b541dba0caef3b8edf`
- new hash: `76c7976517daf457f7f996945c69d8fd75314113b3125076c41527b04b2ec946`

## Review Notes

This pass makes the origin-panel label text match the typed scene payloads. It does not assert that the origin panel is visually final. Human review should still inspect whether the longer heat and chain labels improve the chemistry narrative without crowding the local composition relation.
