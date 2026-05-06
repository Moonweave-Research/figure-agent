# Scaffold Contract Handback v15

## Scope

This pass promotes the Fig1 reference scaffold into an explicit scaffold contract. It is a structure-only contract extraction, not a visual polish pass.

## Implemented Boundary

- `src/engine/scaffold.py` owns the scaffold dataclasses and loader.
- `visual_layout.yaml` remains the Fig1 source file and is treated as JSON with source schema `fig1_reference_visual_layout_v1`.
- The loader normalizes that source into `ScaffoldContract.schema_version == "scaffold_contract_v1"`.
- `fig1_l1_scene.py` keeps Fig1 semantic payload construction local, but consumes scaffold panels, local boxes, object slots, flow anchors, and layout metadata from the scaffold module.
- `src/verify_fig1_scaffold_contract.py` checks the scaffold contract separately from semantic correctness, Fig1 visual policies, and docs governance.

## Contract Meaning

The scaffold contains composition facts: canvas, panels, local boxes, object slots, flow anchors, composition rules, and reference provenance. It does not contain scientific payload values and does not make the reference PNG ground truth.

The reference PNG dependency is now explicit as layout/style evidence. The scaffold is derived from human reference reading; it does not remove the need for a good reference, sketch, or human composition pass.

## Approval Gate

A future real figure cannot start from a scaffold until it has:

1. Declared panel count and panel roles.
2. Declared panel-to-panel flow anchors.
3. Identified the hero panel in composition rules.
4. Recorded a human one-line sign-off that the scaffold is composition-grade.

## Probe Interpretation

`fig_probe_01` and `fig_probe_02` remain architecture-only probes and visual failure evidence. Their weakness should not be reduced to one cause: they lack an approved scaffold and also have lighter payload depth than Fig1.

## Deferred Cleanup

The flat `src/` layout is becoming expensive. A later structural cleanup should move figure-specific files toward `src/figures/{fig1, probe_01, probe_02}/`, but that import-path work is intentionally separated from this hash-stable contract extraction.
