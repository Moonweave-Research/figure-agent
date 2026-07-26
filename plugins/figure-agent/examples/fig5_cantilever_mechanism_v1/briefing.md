# Briefing — fig5_cantilever_mechanism_v1

> **Status:** first Figure Agent authoring trial for the standalone cantilever
> mechanism. This is a new candidate, not a publication-final figure and not a
> source-level continuation of the legacy `fig5_actuation_mechanism` sandbox.

## 1. Topic

Show how a charged sulfur-polymer specimen moves from two-terminal high-voltage
charging through manual transfer and grounded measurement to a macroscopic
floating-cantilever response near a driven electrode.

## 2. Domain vocabulary

poly(S-r-DIB), two-terminal HV, trapped charge `q_{tr}`, manual transfer,
grounded substrate, induction-type electrostatic surface voltmeter (ESVM),
`V_s`, mechanical clamp, floating cantilever, driven electrode, air gap,
Coulomb repulsion.

## 3. Composition intent

Use a four-column left-to-right process:

1. **charge** — a thin polymer specimen sits between two terminals of an HV
   source. Both terminals are visible; no earth-ground symbol and no grid.
2. **manual transfer** — the same charged specimen is shown before and after a
   discrete hand-mediated move. Use one explicit manual-transfer arrow; do not
   depict a motion stage or conveyor.
3. **grounded measurement** — the film is on a conductive substrate connected to
   ground. An ESVM head remains above the surface at a fixed non-contact gap and
   connects to a small `V_s` meter.
4. **cantilever response** — a vertical polymer cantilever hangs from a clip at
   the top, remains electrically floating, and bends away from a nearby driven
   electrode. The electrode source has its own grounded return. Show one strong
   Coulomb-repulsion arrow and the air gap.

The four panels are a causal process, not four independent devices. Keep the
material identity and trapped-charge cue visually consistent across states.

## 4. Normalize / avoid literal overfit

- No voltage magnitude, force value, displacement, bending angle, time scale,
  instrument model number, or fitted measurement curve.
- Do not infer a polarity-reversed two-direction sequence from a single nearby
  electrode. A future bidirectional figure requires a separate paper-local
  authority decision.
- Do not use a Kelvin-probe fork, vibration arc, grid electrode, automated
  stage, or pseudo-3D apparatus detail.
- The ESVM silhouette is family-level only; model-specific controls and
  dimensions remain schematic.

## 5. Style notes

Use the polymer-paper Style Lock: white canvas, muted cGray apparatus, cAmber
polymer, cRed trapped-charge/force result, compact sans-serif labels, and
consistent stroke tiers. Prefer an open canvas with restrained separators over
rounded UI-like cards. The cantilever response is the visual endpoint, but it
must not become an oversized hero panel.

## 6. Physics invariants

- Charging is a two-terminal high-voltage state with no charging-stage ground
  and no grid.
- Transfer is manual and discrete.
- Ground belongs to the conductive measurement substrate and to the driven
  electrode source return only; it must not connect to the polymer cantilever or
  trapped-charge path.
- The ESVM head is induction-type, non-contact, fixed above the sample surface,
  and separate from the grounded substrate.
- The cantilever is vertical, mechanically clamped at the top, electrically
  floating, and separated from the driven electrode by an air gap.
- The Coulomb force arrow points away from the driven electrode and begins on
  the trapped-charge-bearing cantilever. No unearned field direction is added.

## 7. Author intent — semantic constraints

### Must depict

- The same specimen identity across charge and manual-transfer states.
- Ground ownership: substrate in the measurement panel and source return in the
  actuation panel, never the cantilever.
- A clear ESVM standoff rather than a contact or Kelvin-probe geometry.
- A curved, vertically hanging cantilever with a visibly displaced tip, not a
  rigid horizontal rod.
- `q_{tr}` embedded in the polymer body and an air gap between polymer and
  electrode.

### Must avoid

- Grounded poling, a charging grid, an automated motion stage, or a Kelvin-probe
  fork imported from older validation fixtures.
- A Maxwell arrow or electric-field fan that competes with the declared
  Coulomb-result arrow unless a later paper-local authority explicitly requires
  that contrast.
- Decorative polymer wrinkles, repeated dots floating outside the beam, or a
  pseudo-realistic hand that changes the transfer agency.
- Quantitative claims hidden in line length, marker count, or panel size.
