# Fig1 Reference Visual Fidelity Handback v3

## Goal

Move beyond card placement and improve the figure's visual density inside the reference layout.

## What Changed

- Reworked the hero trap display from a few large dots into a stacked shallow/deep level schematic.
- Increased semantic trap density in `TrapLevelSet` while keeping deep traps dominant over shallow traps.
- Adjusted deep levels to stop above HOMO and avoid overlap.
- Added a DOS midline cue and refined the deep/shallow DOS labels.
- Increased probe charge count and distributed charges along the curved polymer cantilever.
- Added denser curved field lines between cantilever and electrode.
- Kept repulsion dominant and Maxwell attraction secondary.
- Made verifier payload checks derive expected trap counts from the scene instead of hard-coded values.

## Result

This is still not a traced reproduction, but it no longer reads as only a layout skeleton. The center hero now communicates the reference idea more directly: many deep trap levels dominate the gap and connect to the large deep DOS lobe. The probe panel is also denser and closer to the reference mechanism.

## Remaining Gap

- The hero still needs finer label placement around `Et ~ 0.5-1.0 eV`.
- The probe beam curve is more plausible but still not as clean as the reference.
- The top-left polymer chemistry motif remains schematic.
- The interpretation card is structurally correct but visually lighter than the reference.
