# Design — fig2_charge_transport_mechanism

## Composition

Use a 163.8 × 46.4 mm wide strip matching the current Fig. 2a slot. Keep one
open white row with three reader roles: measurement context, a paired material
comparison, and one common readout. The two material states are siblings, not
two serial UI cards:

1. Measurement context and MIM stack.
2. Ideal dielectric: bound-dipole alignment and rapid pre-window polarization.
3. Sulfur-rich copolymer: sign-neutral localized-state cues and long-lived
   relaxation, explicitly framed as a working picture.
4. Readout icon with the early and late time windows.

The header lane carries the panel letter and compact role labels. A shared rail
must fork from measurement to both material states, then merge from both states
into the readout. The object lane carries the physical marks. The bottom lane
carries only short explanatory labels.

## Visual decisions

- Use cGray for apparatus, cAmber for the sulfur-rich film, cBlue for the ideal
  dielectric polarization, and cRed only for a field condition or sign-neutral
  localized-state outline.
- Keep line weights above the reduction threshold and avoid gradients, 3-D
  substrate blocks, or decorative halos.
- Make the comparison visible with object geometry: bound dipoles and a rapid
  pre-window polarization for the ideal baseline; sulfur-host traces with
  sign-neutral localized-state cues for the sulfur-rich working picture.
- Draw one continuous held-field rail above the readout. A source-OFF or drain
  arrow is a semantic failure because the transient is acquired under applied DC.
- Do not use a large circular halo, repeated amber/red bead population, or a
  decorative polymer wave; those cues make a localized population read as
  ornament or a second material phase.
- Keep the readout trace qualitative and number-free except for the two declared
  window labels.
- Do not use full-height column rules or equal framed cards; whitespace and the
  object silhouettes should establish the four lanes.

## Review order

1. Whole strip at 100%: reading order and mechanism ownership.
2. Panel crop at 50%: labels, separators, and object/label ownership.
3. 33% print reduction: minimum font, contrast, and whether the four stages
   still read without the data panels present.

The first visual gate is human: the strip must no longer read as a placeholder
or as an energy diagram in disguise.
