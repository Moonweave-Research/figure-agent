# Fig1 Visual Constraint Layer Handback v5

## Goal

Add a first automatic visual constraint layer so obvious layout defects are caught before manual preview.

## What Changed

- Added `src/engine/visual_constraints.py`.
- Added SVG semantic-group bbox estimation for:
  - rectangles
  - circles
  - lines
  - paths
  - polygons
  - text
  - simple translated text
- Added verifier integration through `semantic_bbox_violations(scene, SVG)`.
- The verifier now checks that semantic objects stay inside their assigned visual region.
- Added specific hero checks:
  - `dos_lobes` should stay near the hero DOS box.
  - trap levels should not be too close to HOMO/LUMO labels.

## Defects Caught And Fixed

The new layer immediately caught:

- `dos_lobes` overflowing the hero card because the deep DOS label extended past the right edge.
- `ispd_plot` overflowing the interpretation card because the inset DOS lobe was wider than its local box.
- An over-strict first rule that treated the trap-depth annotation as if it had to stay inside the band-area only; that was corrected because the Et annotation belongs between the band and DOS regions.

Fixes:

- Moved the deep DOS label inside the DOS area.
- Scaled the ISPD lobe width to fit the inset local box.
- Kept the trap-depth annotation legal while still checking trap level proximity to HOMO/LUMO.

## Remaining Gap

This is a bbox layer, not a full visual solver. It catches overflow and some coarse collisions, but it does not yet optimize placement. Next possible upgrades:

- Label-to-label collision checks.
- Local-box-specific containment per object kind.
- Text-width calibration by font metrics.
- Curve/arrow clearance checks around probe geometry.
- Warning report image overlay for failed constraints.
