# v5d/v5e/v5f Visual Comparison Gate

Fixture: `fig1_overview_v5f_art_direction_001_vault`

Baseline/fallbacks:
- `fig1_overview_v5d_redraw_001_vault`
- `fig1_overview_v5e_aggressive_001_vault`

Human decision recorded 2026-07-05:
- Selected direction: `fig1_overview_v5d_redraw_001_vault`.
- v5f status: rejected/deferred as an unfinished art-direction lane. The large-change
  tool gate passed, but human visual judgment says v5f completion quality is not
  acceptable and reads like the loop stopped mid-drawing.
- Decision record:
  `docs/decision-records/2026-07-05-fig1-v5-human-pick/fig1_overview_v5_keep_v5d.json`.

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

Visual read after human review:
- v5d is the picked direction because it reads as finished.
- v5f is a composition-level redesign with measurable movement, but that is not enough:
  its finish quality is uneven and the apparatus/charge-trapping lane still feels
  drawn partway rather than fully resolved.
- Panel C/F changes in v5f should not be promoted over v5d without a future rebuild
  that explicitly targets v5d-level completion quality.

Decision boundary:
- Tool gate: pass for large-change threshold, compile freshness, and critique lint.
- Human gate: closed for this comparison. v5d is selected; v5f is not accepted,
  golden, final, or release-ready.
