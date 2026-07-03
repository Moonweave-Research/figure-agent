# v5f Visual Comparison Gate

Fixture: `fig1_overview_v5f_art_direction_001_vault`

Baseline/fallbacks:
- `fig1_overview_v5d_redraw_001_vault`
- `fig1_overview_v5e_aggressive_001_vault`

Generated comparison artifacts, ignored under `build/`:
- `build/v5f_comparison/v5d_v5e_v5f_full_contact_sheet.png`
- `build/v5f_comparison/v5d_v5e_v5f_print_thumbnail_sheet.png`
- `build/v5f_comparison/v5d_v5e_v5f_panel_C_contact_sheet.png`
- `build/v5f_comparison/v5d_v5e_v5f_panel_D_contact_sheet.png`
- `build/v5f_comparison/v5d_v5e_v5f_panel_E_contact_sheet.png`
- `build/v5f_comparison/v5d_v5e_v5f_panel_F_contact_sheet.png`

Pixel-diff gate versus v5d:
- Threshold 0 RGB delta: 0.148890 changed-pixel ratio.
- Threshold 8 RGB delta: 0.081553 changed-pixel ratio.
- Threshold 16 RGB delta: 0.073729 changed-pixel ratio.
- Gate result: pass. The conservative threshold-8 ratio is above the 0.020000 minimum for a large art-direction change.

Visual read:
- Full render: v5f is a composition-level redesign, not a local tweak. Panel C now reads as the model hero through the stronger `localized trap model` heading and shallow/deep energy-band fields.
- Print thumbnail: `mobility edge`, `shallow`, `deep`, `high n`, and the Panel F trapped-charge callout remain visible enough for comparison review.
- Panel C crop: v5f strengthens model hierarchy while preserving real-space to energy-diagram mapping and `Delta E_t`.
- Panel D/E crops: evidence-mode panels remain stable; the redesign does not move measured relationships or apparatus semantics.
- Panel F crop: v5f shifts from sparse apparatus emphasis to a mechanism-first charge/force/electrode/air-gap composition. This is the clearest improvement and also the densest remaining art-direction risk.

Decision boundary:
- Tool gate: pass for large-change threshold, compile freshness, and critique lint.
- Human gate: still open. This file does not declare v5f accepted, golden, final, or release-ready.
