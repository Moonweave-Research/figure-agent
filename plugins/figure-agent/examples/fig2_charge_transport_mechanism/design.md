# Design — fig2_charge_transport_mechanism

## Composition

Use a 180.0 × 51.02 mm content artboard inside the current Fig. 2a parent slot
(180.0 × 53.19 mm). This is the Nature Communications double-column working
width; the parent data composition owns the figure-wide `a`–`d`
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
7. A small open/filled marker key makes the occupancy grammar explicit without
   turning the illustrative sites into a quantitative legend.

The parent panel letter sits outside this artboard; its header lane carries the
quiet held-field condition. The reference and all sulfur MIM states must retain
the same visible footprint, electrode spacing, and field cue. State connectors
must read as continued field exposure, not an automated scan or material
conversion. The output arrow begins at the late sulfur state and the bottom lane
uses only short labels.

At integration time, the parent composition centers this full-width content
artboard vertically in its Fig. 2a row. The remaining vertical space is a
shared row gutter for the a–d assembly, not an invitation to add filler
decoration or unsupported mechanism detail.

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
- Stroke weight carries role, not magnitude, on the Fig. 1 measured ladder
  (0.40 hairline / 0.70 annotation / 0.90 secondary / 1.05 instrument /
  1.25 primary). The device cross-section outranks its own wiring, and the
  readout traces are the only primary-weight strokes. The single declared
  exception is the mobile-current cue, whose weight and carrier-dot count
  encode the qualitative decrease across the three states.
- Draw every MIM cross-section from one macro and every localized-state
  position from one list. A matched footprint and an invariant site field are
  then properties of the source, not of four hand-kept coordinate sets.
- Give the current cue the same start, end, and offset in all three states.
  Length must never be available as a strength claim.
- Label the early-fit extrapolation. An unlabelled dashed line beside a
  material trace is read as a measured control.
- The readout plot shares the MIM band's top and bottom edge, which keeps it a
  secondary lane rather than a second hero panel.

## Typographic register

Follow the canonical Fig. 1 (`fig1_updated_agent_redraw_v1`), which is the
paper's own convention rather than a generic house style:

- No figure headline. A figure is not titled inside the artboard; the caption
  titles it. Here the parent composition owns the panel letter, so this
  artboard carries no panel-level text at all.
- Objects are still named. A comparison the reader cannot resolve without the
  caption is not a comparison, so each lane keeps a short lowercase bold noun
  phrase naming what it is -- `idealized dielectric`, `sulfur-rich copolymer`,
  `qualitative output`. Name the object; do not describe the panel.
- No numeric measurement condition anywhere on the drawing. Fig. 1 states its
  condition qualitatively (`constant bias: current decays`) and leaves the
  numbers to the caption; this strip does the same with `field held on
  throughout`.
- Italics are reserved for mathematical variables. Fig. 1 uses `\itshape`
  nowhere; ordinary labels and micro clauses are roman.
- Three text tiers only: object name (bold, 5.9 pt), label (roman, 5.45 pt),
  micro clause (roman, 5.05 pt). One name and at most one qualifying line per
  object; two labels making the same point is one too many.

## Review order

1. Whole strip at 100%: reading order and mechanism ownership.
2. Panel crop at 50%: labels, separators, and object/label ownership.
3. 33% print reduction: minimum font, contrast, and whether the four stages
   still read without the data panels present.

The first visual gate is human: the strip must no longer read as a placeholder
or as an energy diagram in disguise.
