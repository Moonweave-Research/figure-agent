# Print-Scale Audit Pack Dogfood

**Date:** 2026-05-20 KST
**Fixture:** `fig1_overview_v2_pair_001_vault`
**Status:** pass for Issue 12E command-facing evidence generation

## Purpose

Verify that Issue 12E produces print-scale audit evidence during a real
`/fig_critique` preparation path without mutating source, critique, accepted,
golden, export, or final-artifact state.

This is not a host-vision quality judgment. It proves the plugin now supplies
the evidence and prompt contract that a host critique must use.

## Sequence

1. Checked the figure driver:
   `uv run python3 scripts/fig_driver.py fig1_overview_v2_pair_001_vault --mode review --goal 'dogfood print-scale audit pack' --dry-run`

   Result:
   - `action: run_critique`
   - `safe_command: /fig_critique fig1_overview_v2_pair_001_vault`
   - `stop_boundary: host_llm_critique_required`
   - `render_state: FRESH`
   - `critique_state: STALE`

2. Generated the critique brief:
   `uv run python3 scripts/critique_brief.py examples/fig1_overview_v2_pair_001_vault`

   Result:
   - `## High-Zoom Visual Audit Crops` emitted.
   - `## Print-Scale Audit Images` emitted.
   - `print_178mm.png` emitted with `scale=178mm_equivalent size_px=[1000, 624]`.
   - `print_thumbnail.png` emitted with `scale=thumbnail size_px=[360, 225]`.
   - The brief requires inspecting reduced-scale images before setting
     `journal_polish` or `publication_readiness` to `pass`.
   - The print-scale section tells the host to record reduction failures as
     `micro_defects.kind: print_scale_unreadable`.

3. Verified high-zoom / print-scale separation:
   - The high-zoom section lists only:
     `line_crosses_label`, `wire_crosses_label`, `arrow_tip_fused`,
     `label_target_detached`, `floating_semantic_cue`,
     `drawing_order_suspect`.
   - The high-zoom section does not contain `print_scale_unreadable`,
     `print_178mm`, or `print_thumbnail`.
   - The micro-defect schema allows evidence from a
     `High-Zoom crop or Print-Scale image`.

4. Verified generated image dimensions:
   - `build/audit_crops/print_178mm.png`: `1000 x 624`
   - `build/audit_crops/print_thumbnail.png`: `360 x 225`
   - `build/audit_crops/full_q1.png`: `2136 x 1333`
   - `build/audit_crops/panel_D_q1.png`: `671 x 632`

5. Checked git state:
   - No tracked source, critique, accepted, golden, export, or final-artifact
     mutation was produced by the dogfood path.
   - Generated `build/audit_crops/` files remain ignored build artifacts.

## Judgment

Issue 12E passes this dogfood slice. The plugin now produces distinct
original-pixel high-zoom evidence and reduced-scale print evidence, and the
host-facing brief keeps the two evidence classes separate while allowing both
to feed `micro_defects`.

## Remaining Risk

`print_178mm` is a deterministic fixed-width proxy, not a physical DPI-derived
journal-scale simulation. That is acceptable for Issue 12E evidence generation,
but later calibration work should decide whether the proxy should become a
true export-width or DPI-aware transform.
