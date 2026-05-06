# Fig1 Scientific Visual Grammar Handback v4

## Goal

Make the trap energy and DOS drawing less like guessed coordinates and more like a reusable scientific schematic grammar.

## What Changed

- Added trap energy semantics to `TrapLevelSet`:
  - `energy_reference="normalized_bandgap_lumo_to_homo"`
  - `deep_depth_range_ev=(0.5, 1.0)`
  - `quantitative_status="schematic_placeholder_until_fig3_ispd"`
- Added reusable visual grammar primitives:
  - `draw_level_stack(...)`
  - `dos_lobe(...)`
  - `draw_dos_pair(...)`
- Updated the hero trap rendering to use level-stack grammar instead of ad hoc line placement.
- Updated the hero DOS rendering to use a paired DOS primitive with shallow/deep ordering and deep dominance.
- Added verifier checks that:
  - shallow and deep trap positions are inside the HOMO-LUMO gap
  - deep trap positions are deeper than shallow traps relative to LUMO
  - DOS shallow/deep centers follow the same energy order
  - the current 0.5-1.0 eV label remains explicitly marked as a schematic placeholder until Fig 3 ISPD values are available

## Scientific Scope

This is still a schematic, not a measured DOS plot. The engine now prevents the most important semantic errors for Fig1:

- deep traps cannot be drawn above shallow traps
- traps cannot fall outside the bandgap
- the deep DOS lobe must remain visually dominant
- the trap-depth label is not treated as final measured data

## Remaining Gap

The next scientific upgrade would require real Fig 3 ISPD parameters or paper-approved trap depth values. Without that, the correct behavior is schematic placement with explicit placeholder status, not numeric overclaiming.
