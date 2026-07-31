# Design — fig2_charge_transport_mechanism

## Composition

Use a 166.53 × 47.20 mm content artboard inside the current Fig. 2a parent slot
(166.53 × 53.19 mm). The parent data composition owns the figure-wide `a`–`d`
labels, so this artboard deliberately contains no second panel letter. Keep one
open white row with a compact idealized reference, three matched states of one
sulfur-rich MIM, and one compact output readout. The sulfur states are a causal
sequence, not three different samples or vertically stacked UI cards:

1. Shared held-DC measurement condition and matched MIM geometry.
2. Idealized dielectric reference: bound-dipole alignment.
3. Sulfur-rich early field-on MIM state: empty localized sites and stronger
   mobile-current cue.
4. Progressive trapping state: capture cues terminate at partly occupied sites
   and the mobile-current cue is reduced.
5. Long-lived occupied state: occupied sites dominate qualitatively, a weak
   mobile-current cue remains, and persistent relaxation is indicated.
6. Compact standard transient icon: early power law and persistent late tail.

The parent panel letter sits outside this artboard; its header lane carries the
quiet held-field condition. The reference and all sulfur MIM states must retain
the same visible footprint, electrode spacing, and field cue. State connectors
must read as continued field exposure, not an automated scan or material
conversion. The output arrow begins at the late sulfur state and the bottom lane
uses only short labels.

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
- Make the mechanism visible with object geometry: bound dipoles for the
  idealized reference; repeated sulfur host geometry with empty-to-occupied
  localized states, capture cues, and a diminishing mobile-current cue.
- Show the common field where it acts inside each matched MIM cell. An overhead
  rail that reads as a serial process path, a source-OFF cue, or a drain arrow
  is a semantic failure because the transient is acquired under applied DC.
- Do not use a large circular halo, repeated amber/red bead population, a
  decorative polymer wave, or an insulating wall; those cues make the state
  read as ornament, a second material phase, or complete current blockage.
- Keep the transient readout qualitative and number-free: $\log I$ vertically,
  $\log t$ horizontally, a straight early power-law segment, and a solid
  persistent-relaxation tail above a neutral early-fit extrapolation. It is
  secondary to the MIM state sequence. Exact analysis windows, ratios, and
  cross-material comparisons belong to the quantitative panels.
- Do not use full-height column rules or equal framed cards; whitespace and the
  object silhouettes should establish the four lanes.

## Review order

1. Whole strip at 100%: reading order and mechanism ownership.
2. Panel crop at 50%: labels, separators, and object/label ownership.
3. 33% print reduction: minimum font, contrast, and whether the four stages
   still read without the data panels present.

The first visual gate is human: the strip must no longer read as a placeholder
or as an energy diagram in disguise.
