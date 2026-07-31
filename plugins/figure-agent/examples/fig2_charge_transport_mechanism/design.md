# Design — fig2_charge_transport_mechanism

## Composition

Use a 166.53 × 47.20 mm content artboard inside the current Fig. 2a parent slot
(166.53 × 53.19 mm). The parent data composition owns the figure-wide `a`–`d`
labels, so this artboard deliberately contains no second panel letter. Keep one
open white row with the shared field-on condition carried inside two side-by-side material cells
and one common readout. The two material states must be lateral siblings, not
two serial stages or vertically stacked UI cards:

1. Shared held-DC measurement condition and matched MIM geometry.
2. Ideal dielectric: bound-dipole alignment and rapid pre-window polarization.
3. Sulfur-rich copolymer: sign-neutral localized-state cues and long-lived
   relaxation, explicitly framed as a working picture.
4. Readout icon with early and later response regimes.

The parent panel letter sits outside this artboard; its header lane carries the
quiet held-field condition. The two MIM cells must retain the same visible
footprint; each carries a restrained, neutral field-direction cue so the
comparison cannot read as a serial rail. The object lane carries their distinct
physical marks; one direct arrow leads from the sulfur comparison edge to the
readout. The bottom lane carries only short labels.

At integration time, the parent composition centers this shorter content
artboard vertically in its Fig. 2a row. That blank is a shared row gutter for
the a–d assembly, not an invitation to add filler decoration or unsupported
mechanism detail.

## Visual decisions

- Use cGray for apparatus and held-field context, cAmber for the sulfur-rich
  film, cBlue for ideal-dielectric polarization, and cRed only for
  sign-neutral localized-state/current-response emphasis.
- Keep line weights above the reduction threshold and avoid gradients, 3-D
  substrate blocks, or decorative halos.
- Make the comparison visible with object geometry: bound dipoles and a rapid
  pre-window polarization for the ideal baseline; sulfur-host traces with
  sign-neutral localized-state cues for the sulfur-rich working picture.
- Show the common field where it acts inside each matched MIM cell. An overhead
  rail that reads as a serial process path, a source-OFF cue, or a drain arrow
  is a semantic failure because the transient is acquired under applied DC.
- Do not use a large circular halo, repeated amber/red bead population, or a
  decorative polymer wave; those cues make a localized population read as
  ornament or a second material phase.
- Keep the readout trace qualitative and number-free. Exact analysis windows
  belong to the quantitative panels, not this mechanism strip.
- Do not use full-height column rules or equal framed cards; whitespace and the
  object silhouettes should establish the four lanes.

## Review order

1. Whole strip at 100%: reading order and mechanism ownership.
2. Panel crop at 50%: labels, separators, and object/label ownership.
3. 33% print reduction: minimum font, contrast, and whether the four stages
   still read without the data panels present.

The first visual gate is human: the strip must no longer read as a placeholder
or as an energy diagram in disguise.
