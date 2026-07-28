# Briefing — fig5_cantilever_actuation_artifact_v2

This is an exploratory artifact derived from the local polarity-reversal
experiments. It is intentionally a story test, not a publication-final figure.

## Claim to test

The first “charging” state is part of the same electromechanical actuation
geometry: a polymer cantilever faces a nearby driving electrode across an air
gap, and the applied field produces attraction and bending while the charge
state is established. This is not a standalone high-voltage charging station,
polarization meter, ESVM head, corona needle, or grid.

After the actuation charge state is isolated (OFF / floating), reversing the
nearby drive polarity produces an immediate reversal of the macroscopic
bending direction, followed by a slower relaxation. The air gap is shown as a
capacitor-like electrostatic coupling in the schematic sense only; no measured
capacitance is claimed. The cantilever is a macroscopic probe of trapped
charge, not an application demo.

## Sequence

1. `actuation charge`: the nearby drive electrode is biased across the air gap;
   attraction bends the same cantilever while the charge state is established.
2. `OFF / float`: the clip ground is visibly opened while the same mounted
   cantilever remains in place. The ground lead is lifted manually; this is not
   an electrical switch or an automated motion stage. This intermediate
   electrical state must be shown as its own reader-facing stage, not compressed
   into an arrow caption; the trapped-charge cue remains in the specimen. The
   support-side reference remains held at ground, distinct from the now-floating
   film clip.
3. `-V drive`: the nearby driven electrode reverses polarity. The
   polarity-dependent Coulomb term changes sign, while the Maxwell attraction
   is a polarity-independent baseline.
4. `reverse bend`: the video trace begins at `t=0`, defined as the onset of
   $+5\,\mathrm{kV}$ actuation, when the bend angle is neutral. The 20-minute
   precharge is compressed before the positive plateau; source OFF and the
   short isolation interval then precede polarity reversal, a negative
   excursion, and schematic recovery.

## Physics invariants

- Charging is an actuation state, not a generic source-box state; the exact
  electrical boundary is evidence-bound and must not be inferred from the word
  “charging”.
- The cantilever and driving electrode remain visibly separated by an air gap;
  no contact or measurement lead is implied by the capacitor-like cue.
- The source is switched off before the charged specimen is treated as
  floating.
- The fixed support reference remains at ground while the film clip is opened;
  “floating” applies to the film/cantilever electrical path, not to the support
  boundary.
- The Coulomb contribution is proportional to the sign of $q_{tr}E$ and can
  reverse when the drive polarity reverses.
- The Maxwell attraction baseline is proportional to $E^2$ and is therefore
  polarity-independent.
- The cantilever remains mechanically clamped but electrically floating during
  the actuation observation.

## Scope

- This artifact does not select representative video frames yet.
- The C-panel arrows are an explicitly labelled, illustrated force condition:
  they show the charge-mediated term opposing the Maxwell baseline, not a
  directly measured force vector or a geometry-independent sign assignment.
- B owns the source-off isolation state; it must not be compressed into A or
  replaced by a second bend-state cartoon.
- It intentionally omits ESVM; ESVM belongs to the charge-state measurement
  story, not the center of this actuation evidence panel.
- The trace is a qualitative redraw of the observed waveform shape, not a
  quantitative data plot.
