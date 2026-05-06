# Fig1 Scaffold Contract v1

## Format Lock

- Contract source file: `visual_layout.yaml` for the current Fig1 pilot.
- Source file format: JSON object stored in the historical `.yaml` file.
- Normalized schema version: `scaffold_contract_v1` from `src/engine/scaffold.py`.
- Source schema retained for compatibility: `fig1_reference_visual_layout_v1`.

## Contract Fields

`ScaffoldContract` exposes five fields to renderers and verifiers:

1. `canvas`: width and height in SVG pixels.
2. `panels`: ordered `Panel` records with `id`, `role`, `bounds`, `local_boxes`, and `object_slots`.
3. `flow_anchors`: ordered support-to-hero anchors with start/end panel ids, points, and inferred panel sides.
4. `composition_rules`: hero placement and Fig1-specific scaffold rules copied from `visual_rules`.
5. `provenance`: reference image path, normalized authority, source authority, and non-ground-truth note.

## Authority

The scaffold is human-authored layout/style evidence extracted from a reference image, sketch, or composition review. It is not scientific ground truth and is not a pixel-tracing source.

The semantic scene remains the source of truth for scientific objects, payload values, computed geometry, and domain relationships.

## Approval Gate

A scaffold is approved only when all four items are present:

1. Panel count and panel role assignment.
2. Panel-to-panel flow anchors.
3. Hero panel identification.
4. Human one-line sign-off: `scaffold <id> is composition-grade`.

The verifier can check structure and provenance. It cannot replace human visual approval.
